from ambianic.pipeline.ai.pose_engine_utils import decode_multiple_poses
from ambianic.pipeline.ai.tf_detect import TFDetectionModel
from ambianic import DEFAULT_DATA_DIR
import logging
import time
import numpy as np
from PIL import Image, ImageDraw
from pathlib import Path


log = logging.getLogger(__name__)

KEYPOINTS = (
  'nose',
  'left eye',
  'right eye',
  'left ear',
  'right ear',
  'left shoulder',
  'right shoulder',
  'left elbow',
  'right elbow',
  'left wrist',
  'right wrist',
  'left hip',
  'right hip',
  'left knee',
  'right knee',
  'left ankle',
  'right ankle'
)


class Keypoint:
    __slots__ = ['k', 'yx', 'score']

    def __init__(self, k, yx, score=None):
        self.k = k
        self.yx = yx
        self.score = score

    def __repr__(self):
        return 'Keypoint(<{}>, {}, {})'.format(self.k, self.yx, self.score)


class Pose:
    __slots__ = ['keypoints', 'score']

    def __init__(self, keypoints, score=None):
        assert len(keypoints) == len(KEYPOINTS)
        self.keypoints = keypoints
        self.score = score

    def __repr__(self):
        return 'Pose({}, {})'.format(self.keypoints, self.score)


class PoseEngine:
    """Engine used for pose tasks."""
    def __init__(self, tfengine=None, context=None):
        """Creates a PoseEngine wrapper around an initialized tfengine.
        """
        if context:
            self._sys_data_dir = context.data_dir
        else:
            self._sys_data_dir = DEFAULT_DATA_DIR
        self._sys_data_dir = Path(self._sys_data_dir)
        assert tfengine is not None
        self._tfengine = tfengine

        self._input_tensor_shape = self.get_input_tensor_shape()

        _, self._tensor_image_height, self._tensor_image_width, self._tensor_image_depth = \
            self.get_input_tensor_shape()

        self.confidence_threshold = self._tfengine.confidence_threshold
        log.debug(f"Initializing PoseEngine with confidence threshold \
            {self.confidence_threshold}")

    def get_input_tensor_shape(self):
        """Get the shape of the input tensor structure.
        Gets the shape required for the input tensor.
        For models trained for image classification / detection, the shape is
        always [1, height, width, channels].
        To be used as input for :func:`run_inference`,
        this tensor shape must be flattened into a 1-D array with size
        ``height * width * channels``. To instead get that 1-D array size, use
        :func:`required_input_array_size`.
        Returns:
        A 1-D array (:obj:`numpy.ndarray`) representing the required input
        tensor shape.
        """
        return self._tfengine.input_details[0]['shape']

    def parse_output(self, heatmap_data, offset_data, threshold):
        joint_num = heatmap_data.shape[-1]
        pose_kps = np.zeros((joint_num, 4), np.float32)

        for i in range(heatmap_data.shape[-1]):

            joint_heatmap = heatmap_data[..., i]
            max_val_pos = np.squeeze(
                np.argwhere(joint_heatmap == np.max(joint_heatmap)))
            remap_pos = np.array(max_val_pos/8*self._tensor_image_height,
                                 dtype=np.int32)
            pose_kps[i, 0] = int(remap_pos[0] + offset_data[max_val_pos[0],
                                 max_val_pos[1], i])
            pose_kps[i, 1] = int(remap_pos[1] + offset_data[max_val_pos[0],
                                 max_val_pos[1], i+joint_num])
            max_prob = np.max(joint_heatmap)
            pose_kps[i, 3] = max_prob
            if max_prob > threshold:
                if pose_kps[i, 0] < self._tensor_image_height and \
                   pose_kps[i, 1] < self._tensor_image_width:
                    pose_kps[i, 2] = 1

        return pose_kps

    def sigmoid(self, x):
        return 1 / (1 + np.exp(-x))

    def tf_interpreter(self):
        return self._tfengine._tf_interpreter

    def detect_poses(self, img):
        """
        Detects poses in a given image.
        :Parameters:
        ----------
        img : PIL.Image
            Input Image for AI model detection.
        :Returns:
        -------
        poses:
            A list of Pose objects with keypoints and confidence scores
        PIL.Image
            Resized image fitting the AI model input tensor.
        """

        image_net_mean = [-123.15, -115.90, -103.06]

        _tensor_input_size = (self._tensor_image_width,
                              self._tensor_image_height)

        # thumbnail is a proportionately resized image
        thumbnail = TFDetectionModel.thumbnail(image=img,
                                               desired_size=_tensor_input_size)
        # convert thumbnail into an image with the exact size
        # as the input tensor preserving proportions by padding with
        # a solid color as needed
        template_image = TFDetectionModel.resize(image=thumbnail,
                                                 desired_size=_tensor_input_size)

        template_image = np.expand_dims(template_image.copy(), axis=0)
        template_input = template_image + image_net_mean

        template_input = template_input.astype(np.float32)

        self.tf_interpreter().\
            set_tensor(self._tfengine.input_details[0]['index'],
                       template_input)
        self.tf_interpreter().invoke()

        heatmap_result = self.tf_interpreter().\
            get_tensor(self._tfengine.output_details[0]['index'])
        offsets_result = self.tf_interpreter().\
            get_tensor(self._tfengine.output_details[1]['index'])
        displacement_bwd_result = self.tf_interpreter().\
            get_tensor(self._tfengine.output_details[2]['index'])
        displacement_fwd_result = self.tf_interpreter().\
            get_tensor(self._tfengine.output_details[3]['index'])

        heatmap_result = self.sigmoid(heatmap_result)

        pose_score, keypoint_scores, keypoint_coords = decode_multiple_poses(
                        heatmap_result.squeeze(axis=0),
                        offsets_result.squeeze(axis=0),
                        displacement_fwd_result.squeeze(axis=0),
                        displacement_bwd_result.squeeze(axis=0),
                        output_stride=16)

        pose_score = pose_score[0]
        keypoint_scores = keypoint_scores[0]
        keypoint_coords = keypoint_coords[0]

        poses = []
        keypoint_dict = {}

        for point_i in range(len(keypoint_coords)):
            x, y = keypoint_coords[point_i, 1], keypoint_coords[point_i, 0]
            keypoint = Keypoint(KEYPOINTS[point_i], [x, y],
                                keypoint_scores[point_i])
            keypoint_dict[KEYPOINTS[point_i]] = keypoint

        log.debug(f"Overall pose score (keypoint score average): {pose_score}")
        poses.append(Pose(keypoint_dict, pose_score))

        return poses, thumbnail, pose_score

from ambianic.pipeline.ai.inference import TFInferenceEngine
import logging
import numpy as np
from PIL import Image

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


class PoseEngine(TFInferenceEngine):
    """Engine used for pose tasks."""
    def __init__(self, model, **kwargs):
        """Creates a PoseEngine with given model.
        Args:
            model: dict
            {
                'tflite': 
                    'ai_models/posenet_mobilenet_v1_075_721_1281_quant_decoder.tflite'
                'edgetpu': 
                    'ai_models/posenet_mobilenet_v1_075_721_1281_quant_decoder_edgetpu.tflite'
                labels: ai_models/pose_labels.txt
            }
            mirror: Flip keypoints horizontally
        Raises:
          ValueError: An error occurred when model output is invalid.
        """
        assert model is not None
        super().__init__(model, **kwargs)
        
        self._input_tensor_shape = self.get_input_tensor_shape()
        if (self._input_tensor_shape.size != 4 or
                self._input_tensor_shape[3] != 3 or
                self._input_tensor_shape[0] != 1):
            raise ValueError(
                ('Image model should have input shape [1, height, width, 3]!'
                 ' This model has {}.'.format(self._input_tensor_shape)))
        _, self.image_height, self.image_width, self.image_depth = \
                                                self.get_input_tensor_shape()


    def get_input_tensor_shape(self):
        """Get the shape of the input tensor structure.
        Gets the shape required for the input tensor.
        For models trained for image classification / detection, the shape is always
        [1, height, width, channels]. To be used as input for :func:`run_inference`,
        this tensor shape must be flattened into a 1-D array with size ``height *
        width * channels``. To instead get that 1-D array size, use
        :func:`required_input_array_size`.
        Returns:
        A 1-D array (:obj:`numpy.ndarray`) representing the required input tensor
        shape.
        """
        return self.input_details[0]['shape']

    def parse_output(self, heatmap_data, offset_data, threshold):
        joint_num = heatmap_data.shape[-1]
        pose_kps = np.zeros((joint_num, 4), np.float32)

        for i in range(heatmap_data.shape[-1]):

            joint_heatmap = heatmap_data[...,i]
            max_val_pos = np.squeeze(np.argwhere(joint_heatmap == np.max(joint_heatmap)))
            remap_pos = np.array(max_val_pos/8*257, dtype=np.int32)
            pose_kps[i, 0] = int(remap_pos[0] + offset_data[max_val_pos[0], max_val_pos[1], i])
            pose_kps[i, 1] = int(remap_pos[1] + offset_data[max_val_pos[0], max_val_pos[1], i+joint_num])
            max_prob = np.max(joint_heatmap)
            pose_kps[i, 3] = max_prob
            if max_prob > threshold:
                if pose_kps[i, 0] < 257 and pose_kps[i, 1] < 257:
                    pose_kps[i, 2] = 1

        return pose_kps

    
    def sigmoid(self, x):
        return 1 / (1 + np.exp(-x))

    def DetectPosesInImage(self, img):
        """
        Detects poses in a given image.
        For ideal results make sure the image fed to this function is 
        close to the expected input size - it is the caller's 
        responsibility to resize the image accordingly.
        Args:
          img: numpy array containing image
        """
        src_templ_height, src_tepml_width = img.size 
        template_image = img.resize((self.image_width, self.image_height), Image.ANTIALIAS)

        templ_ratio_width = src_tepml_width/self.image_width
        templ_ratio_height = src_templ_height/self.image_height
       
        template_input = np.expand_dims(template_image.copy(), axis=0)
        floating_model = self.input_details[0]['dtype'] == np.float32

        if floating_model:
            template_input = (np.float32(template_input) - 127.5) / 127.5

        self._tf_interpreter.set_tensor(self.input_details[0]['index'], template_input)
        self._tf_interpreter.invoke()

        template_output_data = self._tf_interpreter.get_tensor(self.output_details[0]['index'])
        template_offset_data = self._tf_interpreter.get_tensor(self.output_details[1]['index'])

        template_heatmaps = np.squeeze(template_output_data)
        template_offsets = np.squeeze(template_offset_data)
        
        template_kps = self.parse_output(template_heatmaps,template_offsets,0.3)
        
        kps, ratio = template_kps, (templ_ratio_width, templ_ratio_height)

        poses = []

        keypoint_dict = {}
        cnt = 0
        for point_i, point in enumerate(kps):
                
            x, y = int(round(kps[point_i, 0]*ratio[0])), int(round(kps[point_i, 1]*ratio[1]))
            prob = self.sigmoid(kps[point_i, 3])
        
            if prob > 0.60:
                cnt += 1
            keypoint = Keypoint(KEYPOINTS[point_i], [x, y], prob)            
            keypoint_dict[KEYPOINTS[point_i]] = keypoint
        
        pose_scores = cnt/17
        poses.append(Pose(keypoint_dict, pose_scores))

        return poses

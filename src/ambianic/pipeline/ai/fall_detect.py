"""Fall detection pipe element."""
import logging
from ambianic.pipeline.ai.image_detection import TFImageDetection
from ambianic.pipeline.ai.pose_engine import PoseEngine
from ambianic.util import stacktrace
import math
log = logging.getLogger(__name__)


class FallDetector(TFImageDetection):
    """Detects falls comparing two images spaced about 1-2 seconds apart."""
    def __init__(self,
                 model=None,
                 **kwargs
                 ):
        """Initialize detector with config parameters.
        :Parameters:
        ----------
        model: dict
        {
            'tflite': 
                'ai_models/posenet_mobilenet_v1_075_721_1281_quant_decoder.tflite'
            'edgetpu': 
                'ai_models/posenet_mobilenet_v1_075_721_1281_quant_decoder_edgetpu.tflite'
        }
        """
        super().__init__(model, **kwargs)
        self._prev_vals = []
        self._pose_engine = PoseEngine(model, **kwargs)
        self._fall_factor = 60

    def process_sample(self, **sample):
        """Detect objects in sample image."""
        log.debug("%s received new sample", self.__class__.__name__)
        if not sample:
            # pass through empty samples to next element
            yield None
        else:
            try:
                image = sample['image']
                inference_result = self.fall_detect(image=image)
                inf_meta = {
                    'display': 'Fall Detection',
                }
                # pass on the results to the next connected pipe element
                processed_sample = {
                    'image': image,
                    'inference_result': inference_result,
                    'inference_meta': inf_meta
                    }
                yield processed_sample
            except Exception as e:
                log.error('Error "%s" while processing sample. '
                          'Dropping sample: %s',
                          str(e),
                          str(sample)
                          )
                log.warning(stacktrace())

    def calculate_angle(self, p):
        x1, y1 = p[0][0][0], p[0][0][1]
        x2, y2 = p[0][1][0], p[0][1][1]
        x3, y3 = p[1][0][0], p[1][0][1]
        x4, y4 = p[1][1][0], p[1][1][1]

        theta1 = math.degrees(math.atan2(y2-y1, x1-x2))
        theta2 = math.degrees(math.atan2(y4-y3, x3-x4))
            
        theta = abs(theta1-theta2)
        return theta
    
    def find_keypoints(self, image):

        image_ori = image.copy()
        rotation = [90, -90]
        
        while True:
            poses = self._pose_engine.DetectPosesInImage(image)

            if not poses:
                return None
            
            for pose in poses:
                if pose.score < 0.25:
                    if rotation:
                        angle = rotation.pop()
                        image = image_ori.rotate(angle, expand=True)
                    else:
                        return None
                else:
                    return poses


    def fall_detect(self, image=None):
        assert image
        log.debug("Calling TF engine for inference")
        
        # Detection using tensorflow posenet module
        poses = self.find_keypoints(image)
        
        if not poses:
            log.debug("No Key-points are found")
        else:
            inference_result = []
            pose_vals_list = [[], []]      # [[left shoulder, left hip], [right shoulder, right hip]]

            for pose in poses:
                for label, keypoint in pose.keypoints.items():
                    if (label == 'left shoulder' or label == 'left hip') and (keypoint.score > 0.5):
                        pose_vals_list[0].append((keypoint.yx[0], keypoint.yx[1]))
                    elif label == 'right shoulder' or label == 'right hip':
                        pose_vals_list[1].append((keypoint.yx[0], keypoint.yx[1]))

                if not self._prev_vals:
                    res = False
                else:
                    try:
                        temp_left_point = [[self._prev_vals[0][0], self._prev_vals[0][1]], [pose_vals_list[0][0], pose_vals_list[0][1]]]
                        left_angle = self.calculate_angle(temp_left_point)
                    except IndexError:
                        left_angle = 0

                    try:
                        temp_right_point = [[self._prev_vals[1][0], self._prev_vals[1][1]], [pose_vals_list[1][0], pose_vals_list[1][1]]]
                        right_angle = self.calculate_angle(temp_right_point)
                    except IndexError:
                        right_angle = 0

                    if left_angle > self._fall_factor or right_angle > self._fall_factor:
                        inference_result.append(('FALL', pose.score))

            self._prev_vals = pose_vals_list

            return inference_result

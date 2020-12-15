"""Fall detection pipe element."""
from ambianic.pipeline.ai.image_detection import TFImageDetection
from ambianic.pipeline.ai.pose_engine import PoseEngine
from ambianic.util import stacktrace
import logging
import math
import time
from PIL import Image, ImageDraw

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
        # previous pose detection information to compare pose changes against
        self._prev_vals = []
        self._prev_time = time.monotonic()
        self._prev_thumbnail = None

        self._pose_engine = PoseEngine(self._tfengine)
        self._fall_factor = 60
        self.pose_confidence_threshold = kwargs['confidence_threshold']

        # Require a minimum amount of time between two video frames in seconds.
        # Otherwise on high performing hard, the poses could be too close to each other and have negligible difference
        # for fall detection purpose.
        self.min_time_between_frames = 1
        # Require the time distance between two video frames not to exceed a certain limit in seconds.
        # Otherwise there could be data noise which could lead false positive detections.
        self.max_time_between_frames = 10



    def process_sample(self, **sample):
        """Detect objects in sample image."""
        log.info("%s received new sample", self.__class__.__name__)
        if not sample:
            # pass through empty samples to next element
            yield None
        else:
            try:
                image = sample['image']
                inference_result, thumbnail = self.fall_detect(image=image)
                inf_meta = {
                    'display': 'Fall Detection',
                }
                # pass on the results to the next connected pipe element
                processed_sample = {
                    'image': image,
                    'thumbnail': thumbnail,
                    'inference_result': inference_result,
                    'inference_meta': inf_meta
                    }
                yield processed_sample
            except Exception as e:
                log.exception('Error "%s" while processing sample. '
                          'Dropping sample: %s',
                          str(e),
                          str(sample)
                          )


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

        # this score value should be related to the configuration confidence_threshold parameter
        min_score = 0.25
        rotations = [Image.ROTATE_270, Image.ROTATE_90]
        angle = 0
        pose = None
        poses, thumbnail = self._pose_engine.DetectPosesInImage(image)
        width, height = thumbnail.size
        # if no pose detected with high confidence, 
        # try rotating the image +/- 90' to find a fallen person
        # currently only looking at pose[0] because we are focused on a lone person falls
        while (not poses or poses[0].score < self.pose_confidence_threshold) and rotations:
          angle = rotations.pop()
          transposed = image.transpose(angle)
          # we are interested in the poses but not the rotated thumbnail
          poses, _ = self._pose_engine.DetectPosesInImage(transposed)
        if poses and poses[0]:
            pose = poses[0]
        # lets check if we found a good pose candidate
        if (pose and pose.score >= self.pose_confidence_threshold):
            # if the image was rotated, we need to rotate back to the original image coordinates
            # before comparing with poses in other frames.
            if angle == Image.ROTATE_90:
                # ROTATE_90 rotates 90' counter clockwise from ^ to < orientation.
                for label, keypoint in pose.keypoints.items():
                    # keypoint.yx[0] is the x coordinate in an image
                    # keypoint.yx[0] is the y coordinate in an image, with 0,0 in the upper left corner (not lower left).
                    tmp_swap = keypoint.yx[0]
                    keypoint.yx[0] = width-keypoint.yx[1]
                    keypoint.yx[1] = tmp_swap
            elif  angle == Image.ROTATE_270: 
            # ROTATE_270 rotates 90' clockwise from ^ to > orientation.
                for label, keypoint in pose.keypoints.items():
                    tmp_swap = keypoint.yx[0]
                    keypoint.yx[0] = keypoint.yx[1]
                    keypoint.yx[1] = height-tmp_swap
        else:
            # we could not detect a pose with sufficient confidence
            pose = None
        return pose, thumbnail




    def fall_detect(self, image=None):
        assert image
        log.info("Calling TF engine for inference")
        start_time = time.monotonic()

        now = time.monotonic()
        lapse = now - self._prev_time
        if self._prev_vals and lapse < self.min_time_between_frames:
            log.info("This frame is too close to the previous frame. Only %.2f ms apart. Minimum %.2f ms distance required for fall detection.", lapse, self.min_time_between_frames)
            return None, self._prev_thumbnail
        else:
            # Detection using tensorflow posenet module
            pose, thumbnail = self.find_keypoints(image)
            inference_result = None
            if not pose:
                log.info("No pose with key-points found.")
                return inference_result, thumbnail
            else:
                pose_vals_list = [[], []]      # [[left shoulder, left hip], [right shoulder, right hip]]
                inference_result = []
                for label, keypoint in pose.keypoints.items():
                    if (label == 'left shoulder' or label == 'left hip'):
                        pose_vals_list[0].append((keypoint.yx[0], keypoint.yx[1]))
                    elif label == 'right shoulder' or label == 'right hip':
                        pose_vals_list[1].append((keypoint.yx[0], keypoint.yx[1]))
                log.info("Pose detected [[left shoulder, left hip], [right shoulder, right hip]]: %r", pose_vals_list) 
                # save an image with drawn lines for debugging
                draw = ImageDraw.Draw(thumbnail)
                for body_line in pose_vals_list:
                    draw.line(body_line, fill='red')
                # DEBUG: save template_image for debugging
                # DEBUG: timestr = int(time.monotonic()*1000)
                # DEBUG: thumbnail.save(f'tmp-thumbnail-body-line-time-{timestr}.jpg', format='JPEG')

                if not self._prev_vals or lapse > self.max_time_between_frames:
                    log.info("No recent pose to compare to. Will save this frame pose for subsequent comparison.")
                else:
                    left_angle = 0
                    left_body_line_detected = len(pose_vals_list[0]) == 2
                    if left_body_line_detected and (self._prev_vals[0] is not None):
                        try:
                            temp_left_point = [[self._prev_vals[0][0], self._prev_vals[0][1]], [pose_vals_list[0][0], pose_vals_list[0][1]]]
                            left_angle = self.calculate_angle(temp_left_point)
                            log.info("Left shoulder-hip angle: %r", left_angle)
                        except IndexError as e:
                            log.exception("Error while calculating angle: %r", e)
                    right_angle = 0
                    right_body_line_detected = len(pose_vals_list[1]) == 2
                    if right_body_line_detected and (self._prev_vals[1] is not None):
                        try:
                            temp_right_point = [[self._prev_vals[1][0], self._prev_vals[1][1]], [pose_vals_list[1][0], pose_vals_list[1][1]]]
                            right_angle = self.calculate_angle(temp_right_point)
                            log.info("Right shoulder-hip angle: %r", left_angle)
                        except IndexError as e:
                            log.exception("Error while calculating angle: %r", e)

                    angle_change = max(left_angle, right_angle)
                    if angle_change > self._fall_factor:
                        # insert a box that covers the whole image as a workaround
                        # to meet the expected format of the save_detections element
                        box = [0, 0, 1, 1]
                        inference_result.append(('FALL', pose.score, box, angle_change ))
                        log.info("Fall detected: %r", inference_result)
                log.info("Saving pose for subsequent comparison.")
                self._prev_vals = pose_vals_list
                self._prev_time = now
                self._prev_thumbnail = thumbnail
                log.info("Logging stats")
                self.log_stats(start_time=start_time)

            log.info("thumbnail: %r", thumbnail) 
            return inference_result, thumbnail

"""Fall detection pipe element."""
from ambianic.pipeline.ai.tf_detect import TFDetectionModel
from ambianic.pipeline.ai.pose_engine import PoseEngine
from ambianic.util import stacktrace
import logging
import math
import time
from PIL import Image, ImageDraw

log = logging.getLogger(__name__)


class FallDetector(TFDetectionModel):
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
                'ai_models/posenet_mobilenet_v1_100_257x257_multi_kpt_stripped.tflite'
            'edgetpu': 
                'ai_models/posenet_mobilenet_v1_075_721_1281_quant_decoder_edgetpu.tflite'
        }
        """
        super().__init__(model, **kwargs)
        # previous pose detection information to compare pose changes against
        self._prev_vals = []
        self._prev_time = time.monotonic()
        self._prev_thumbnail = None
        # angle b/w left shoulder-hip line with vertical axis
        self._prev_left_angle_with_yaxis = None
        # angle b/w right shoulder-hip line with vertical axis
        self._prev_right_angle_with_yaxis = None
        self.previous_body_vector_score = 0

        self._pose_engine = PoseEngine(self._tfengine)
        self._fall_factor = 60
        self.confidence_threshold = self._tfengine._confidence_threshold
        
        # Require a minimum amount of time between two video frames in seconds.
        # Otherwise on high performing hard, the poses could be too close to each other and have negligible difference
        # for fall detection purpose.
        self.min_time_between_frames = 1
        # Require the time distance between two video frames not to exceed a certain limit in seconds.
        # Otherwise there could be data noise which could lead false positive detections.
        self.max_time_between_frames = 10

        self.fall_detect_corr = ['left shoulder', 'left hip', 'right shoulder', 'right hip']


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
        '''
            Calculate angle b/w two lines such as 
            left shoulder-hip with prev frame's left shoulder-hip or
            right shoulder-hip with prev frame's right shoulder-hip or
            shoulder-hip line with vertical axis
        '''

        x1, y1 = p[0][0]
        x2, y2 = p[0][1]
    
        x3, y3 = p[1][0]
        x4, y4 = p[1][1]

        theta1 = math.degrees(math.atan2(y2-y1, x1-x2))
        theta2 = math.degrees(math.atan2(y4-y3, x3-x4))
            
        angle = abs(theta1-theta2)
        return angle


    def is_body_line_motion_downward(self, left_angle_with_yaxis, rigth_angle_with_yaxis):

        test = False
        l_angle = left_angle_with_yaxis and self._prev_left_angle_with_yaxis and left_angle_with_yaxis > self._prev_left_angle_with_yaxis
        r_angle = rigth_angle_with_yaxis and self._prev_right_angle_with_yaxis and rigth_angle_with_yaxis > self._prev_right_angle_with_yaxis 

        if l_angle or r_angle:
            test = True

        return test


    def find_keypoints(self, image):

        # this score value should be related to the configuration confidence_threshold parameter
        min_score = self.confidence_threshold
        rotations = [Image.ROTATE_270, Image.ROTATE_90]
        angle = 0
        pose = None
        poses, thumbnail = self._pose_engine.DetectPosesInImage(image)
        width, height = thumbnail.size
        # if no pose detected with high confidence, 
        # try rotating the image +/- 90' to find a fallen person
        # currently only looking at pose[0] because we are focused on a lone person falls
        #while (not poses or poses[0].score < min_score) and rotations:
        pose_score, pose_dix = self.estimate_spinalVector_score(poses[0])
        while pose_score < min_score and rotations:
          angle = rotations.pop()
          transposed = image.transpose(angle)
          # we are interested in the poses but not the rotated thumbnail
          poses, _ = self._pose_engine.DetectPosesInImage(transposed)
          pose_score, pose_dix = self.estimate_spinalVector_score(poses[0])

        if poses and poses[0]:
            pose = poses[0]

        # lets check if we found a good pose candidate
                
        if (pose and pose_score >= min_score):
            # if the image was rotated, we need to rotate back to the original image coordinates
            # before comparing with poses in other frames.
            if angle == Image.ROTATE_90:
                # ROTATE_90 rotates 90' counter clockwise from ^ to < orientation.
                for _, keypoint in pose.keypoints.items():
                    # keypoint.yx[0] is the x coordinate in an image
                    # keypoint.yx[0] is the y coordinate in an image, with 0,0 in the upper left corner (not lower left).
                    tmp_swap = keypoint.yx[0]
                    keypoint.yx[0] = width-keypoint.yx[1]
                    keypoint.yx[1] = tmp_swap
            elif  angle == Image.ROTATE_270: 
            # ROTATE_270 rotates 90' clockwise from ^ to > orientation.
                for _, keypoint in pose.keypoints.items():
                    tmp_swap = keypoint.yx[0]
                    keypoint.yx[0] = keypoint.yx[1]
                    keypoint.yx[1] = height-tmp_swap
        else:
            # we could not detect a pose with sufficient confidence
            pose = None
        return pose, thumbnail, pose_score, pose_dix


    def find_changes_in_angle(self, pose_dix):
        '''
            Find the changes in angle for shoulder-hip lines b/w current and previpus frame.
        '''

        prev_leftLine_corr_exist = all(e in self._prev_vals for e in ['left shoulder','left hip'])
        curr_leftLine_corr_exist = all(e in pose_dix for e in ['left shoulder','left hip'])

        prev_rightLine_corr_exist = all(e in self._prev_vals for e in ['right shoulder','right hip'])
        curr_rightLine_corr_exist = all(e in pose_dix for e in ['right shoulder','right hip'])
        
        left_angle = right_angle = 0

        if prev_leftLine_corr_exist and curr_leftLine_corr_exist:
            temp_left_vector = [[self._prev_vals['left shoulder'], self._prev_vals['left hip']], [pose_dix['left shoulder'], pose_dix['left hip']]]
            left_angle = self.calculate_angle(temp_left_vector)
            log.info("Left shoulder-hip angle: %r", left_angle)

        if prev_rightLine_corr_exist and curr_rightLine_corr_exist:
            temp_right_vector = [[self._prev_vals['right shoulder'], self._prev_vals['right hip']], [pose_dix['right shoulder'], pose_dix['right hip']]]
            right_angle = self.calculate_angle(temp_right_vector)
            log.info("Right shoulder-hip angle: %r", right_angle)

        angle_change = max(left_angle, right_angle)
        return angle_change

    def assign_prev_records(self, pose_dix, left_angle_with_yaxis, rigth_angle_with_yaxis, now, thumbnail, current_body_vector_score):
        self._prev_vals = pose_dix
        self._prev_left_angle_with_yaxis = left_angle_with_yaxis
        self._prev_right_angle_with_yaxis = rigth_angle_with_yaxis
        self._prev_time = now
        self._prev_thumbnail = thumbnail
        self.previous_body_vector_score = current_body_vector_score

    def draw_lines(self, thumbnail, pose_dix):
        # save an image with drawn lines for debugging
        draw = ImageDraw.Draw(thumbnail)

        body_line = [tuple(pose_dix['left shoulder']), tuple(pose_dix['left hip'])]
        draw.line(body_line, fill='red')

        body_line = [tuple(pose_dix['right shoulder']), tuple(pose_dix['right hip'])]
        draw.line(body_line, fill='red')
        # DEBUG: save template_image for debugging
        # DEBUG: timestr = int(time.monotonic()*1000)
        # DEBUG: thumbnail.save(f'tmp-thumbnail-body-line-time-{timestr}.jpg', format='JPEG')

    def get_line_angles_with_yaxis(self, pose_dix):
        '''
            Find the angle b/w shoulder-hip line with yaxis.
        '''
        y_axis_corr = [[0, 0], [0, self._pose_engine._tensor_image_height]]
        
        leftLine_corr_exist = all(e in pose_dix for e in ['left shoulder','left hip'])
        rightLine_corr_exist = all(e in pose_dix for e in ['right shoulder','right hip'])

        l_angle = r_angle = 0

        if leftLine_corr_exist:
            l_angle = self.calculate_angle([y_axis_corr, [pose_dix['left shoulder'], pose_dix['left hip']]])
        
        if rightLine_corr_exist:
            r_angle = self.calculate_angle([y_axis_corr, [pose_dix['right shoulder'], pose_dix['right hip']]])
        
        return (l_angle, r_angle)

    def estimate_spinalVector_score(self, pose):
        pose_dix = {}
        is_leftVector = is_rightVector = False

        # Calculate leftVectorScore & rightVectorScore
        leftVectorScore = min(pose.keypoints['left shoulder'].score, pose.keypoints['left hip'].score)
        rightVectorScore = min(pose.keypoints['right shoulder'].score, pose.keypoints['right hip'].score) 

        if leftVectorScore > self.confidence_threshold:
            is_leftVector = True
            pose_dix['left shoulder'] = pose.keypoints['left shoulder'].yx
            pose_dix['left hip'] = pose.keypoints['left hip'].yx

        if rightVectorScore > self.confidence_threshold:
            is_rightVector = True
            pose_dix['right shoulder'] = pose.keypoints['right shoulder'].yx
            pose_dix['right hip'] = pose.keypoints['right hip'].yx

        def find_spinalLine():
            left_spinal_x1 = (pose_dix['left shoulder'][0] + pose_dix['right shoulder'][0]) / 2
            left_spinal_y1 = (pose_dix['left shoulder'][1] + pose_dix['right shoulder'][1]) / 2

            right_spinal_x1 = (pose_dix['left hip'][0] + pose_dix['right hip'][0]) / 2
            right_spinal_y1 = (pose_dix['left hip'][1] + pose_dix['right hip'][1]) / 2

            return (left_spinal_x1, left_spinal_y1), (right_spinal_x1, right_spinal_y1)


        if is_leftVector and is_rightVector:
            spinalVectorEstimate = find_spinalLine()
            spinalVectorScore = (leftVectorScore + rightVectorScore) / 2.0
        elif is_leftVector:
            spinalVectorEstimate = pose_dix['left shoulder'], pose_dix['left hip']
            # 10% score penalty in conficence as only left shoulder-hip line is detected
            spinalVectorScore = leftVectorScore * 0.9
        elif is_rightVector:
            spinalVectorEstimate = pose_dix['right shoulder'], pose_dix['right hip']
            # 10% score penalty in conficence as only right shoulder-hip line is detected
            spinalVectorScore = rightVectorScore * 0.9
        else:
            spinalVectorScore = 0

        pose_score = spinalVectorScore

        return pose_score, pose_dix

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
            pose, thumbnail, pose_score, pose_dix = self.find_keypoints(image)
            log.info("Pose detected : %r", pose_dix)

            inference_result = None
            if not pose:
                log.info("No pose with key-points found.")
                return inference_result, thumbnail
            else:
                inference_result = []
                                
                current_body_vector_score = pose_score

                # Find line angle with vertcal axis
                left_angle_with_yaxis, rigth_angle_with_yaxis = self.get_line_angles_with_yaxis(pose_dix)

                # save an image with drawn lines for debugging
                self.draw_lines(thumbnail, pose_dix)

                if not self._prev_vals or lapse > self.max_time_between_frames:
                    log.info("No recent pose to compare to. Will save this frame pose for subsequent comparison.")
                elif not self.is_body_line_motion_downward(left_angle_with_yaxis, rigth_angle_with_yaxis):
                    log.info("The body-line angle with vertical axis is decreasing from the previous frame.")
                else:
                    leaning_angle = self.find_changes_in_angle(pose_dix)

                    leaning_probability = 1 if leaning_angle > self._fall_factor else 0
                    fall_score = leaning_probability * (self.previous_body_vector_score + current_body_vector_score) / 2

                    #if leaning_angle > self._fall_factor:
                    if fall_score >= self.confidence_threshold:
                        # insert a box that covers the whole image as a workaround
                        # to meet the expected format of the save_detections element
                        box = [0, 0, 1, 1]
                        inference_result.append(('FALL', fall_score, box, leaning_angle))
                        log.info("Fall detected: %r", inference_result)

                log.info("Saving pose for subsequent comparison.")
                self.assign_prev_records(pose_dix, left_angle_with_yaxis, rigth_angle_with_yaxis, now, thumbnail, current_body_vector_score)
                
                log.info("Logging stats")
                self.log_stats(start_time=start_time)

            log.info("thumbnail: %r", thumbnail) 
            return inference_result, thumbnail
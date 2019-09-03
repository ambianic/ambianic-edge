import logging
import time
import os

from .inference import TfInference

log = logging.getLogger(__name__)


class FaceDetect(TfInference):
    """ FaceDetect is a pipeline element responsible for detecting objects in an image """

    def __init__(self, element_config=None):
        TfInference.__init__(self, element_config)
        self.topk = element_config.get('top-k', 3)  # default to top 3 person detections

    @staticmethod
    def crop_image(image, box):
        # Size of the image in pixels (size of orginal image)
        # (This is not mandatory)
        width, height = image.size

        # Setting the points for cropped image
        left = box[0]*width
        top = box[1]*height
        right = box[2]*width
        bottom = box[3]*height

        # Cropped image of above dimension
        # (It will not change orginal image)
        im1 = image.crop((left, top, right, bottom))
        return im1

    def receive_next_sample(self, image, inference_result=None, **kwargs):
        # - crop out top-k person detections
        # - apply face detection to cropped person areas
        # - pass face detections on to next pipe element
        face_regions = []
        for category, confidence, box in inference_result:
            if category == 'person' and confidence >= self.confidence_threshold:
                face_regions.append(box)
        face_regions = face_regions[:self.topk]  # get only topk person detecions
        log.debug('Detected %d faces', len(face_regions))
        for box in face_regions:
            person_image = self.crop_image(image, box)
            inference_result = super().detect(image=person_image)
            if self.next_element:
                self.next_element.receive_next_sample(person_image, inference_result)


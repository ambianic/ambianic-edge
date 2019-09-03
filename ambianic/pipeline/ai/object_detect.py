import logging
import time
import os

from .inference import TfInference

log = logging.getLogger(__name__)


class ObjectDetect(TfInference):
    """ ObjectDetect is a pipeline element responsible for detecting objects in an image """

    def __init__(self, element_config=None):
        TfInference.__init__(self, element_config)

    def receive_next_sample(self, image):
        log.debug("received new sample")
        inference_result = super().detect(image=image)
        # pass on the results to the next connected pipe element
        if self.next_element:
            self.next_element.receive_next_sample(image, inference_result)

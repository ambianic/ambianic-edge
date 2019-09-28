"""Object detection pipe element."""
import logging

from .image_detection import TFImageDetection
from ambianic.service import stacktrace

log = logging.getLogger(__name__)


class ObjectDetector(TFImageDetection):
    """Detects objects in an image."""

    def __init__(self, element_config=None):
        super().__init__(element_config=element_config)

    def receive_next_sample(self, **sample):
        log.debug("%s received new sample", self.__class__.__name__)
        if not sample:
            # pass through empty samples to next element
            if self.next_element:
                self.next_element.receive_next_sample()
        else:
            try:
                image = sample['image']
                inference_result = self.detect(image=image)
                # pass on the results to the next connected pipe element
                if self.next_element:
                    self.next_element.receive_next_sample(
                        image=image,
                        inference_result=inference_result)
            except Exception as e:
                log.error('Error "%s" while processing sample. '
                          'Dropping sample: %s',
                          str(e),
                          str(sample)
                          )
                stacktrace(logging.WARNING)

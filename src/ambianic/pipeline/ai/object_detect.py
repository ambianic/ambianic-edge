"""Object detection pipe element."""
import logging

from .image_detection import TFImageDetection
from ambianic.util import stacktrace

log = logging.getLogger(__name__)


class ObjectDetector(TFImageDetection):
    """Detects objects in an image."""

    def __init__(self, element_config=None):
        super().__init__(element_config=element_config)

    def process_sample(self, **sample):
        log.debug("%s received new sample", self.__class__.__name__)
        if not sample:
            # pass through empty samples to next element
            yield None
        else:
            try:
                image = sample['image']
                inference_result = self.detect(image=image)
                # pass on the results to the next connected pipe element
                processed_sample = {
                    'image': image,
                    'inference_result': inference_result
                    }
                yield processed_sample
            except Exception as e:
                log.error('Error "%s" while processing sample. '
                          'Dropping sample: %s',
                          str(e),
                          str(sample)
                          )
                stacktrace(logging.WARNING)

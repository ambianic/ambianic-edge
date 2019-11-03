"""Object detection pipe element."""
import logging

from .image_detection import TFImageDetection
from ambianic.util import stacktrace

log = logging.getLogger(__name__)


class ObjectDetector(TFImageDetection):
    """Detects objects in an image."""

    def process_sample(self, **sample):
        """Detect objects in sample image."""
        log.debug("%s received new sample", self.__class__.__name__)
        if not sample:
            # pass through empty samples to next element
            yield None
        else:
            try:
                image = sample['image']
                inference_result = self.detect(image=image)
                inf_meta = {
                    'display': 'Object Detection'
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

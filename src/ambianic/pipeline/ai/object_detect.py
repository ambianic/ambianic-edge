"""Object detection pipe element."""
import logging
from .image_boundingBox_detection import TFBoundingBoxDetection
from ambianic.util import stacktrace

log = logging.getLogger(__name__)


class ObjectDetector(TFBoundingBoxDetection):
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
                thumbnail, tensor_image, inference_result = \
                    self.detect(image=image)
                log.debug('Object detection inference_result: %r',
                          inference_result)
                inf_meta = {
                    'display': 'Object Detection',
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
                log.error('Error "%s" while processing sample. '
                          'Dropping sample: %s',
                          str(e),
                          str(sample)
                          )
                log.warning(stacktrace())

"""Object detection pipe element."""
import logging

from ambianic.util import stacktrace

from .image_boundingBox_detection import TFBoundingBoxDetection

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
                image = sample["image"]
                thumbnail, tensor_image, inference_result = self.detect(image=image)

                inference_result = self.convert_inference_result(inference_result)
                log.debug("Object detection inference_result: %r", inference_result)
                inf_meta = {
                    "display": "Object Detection",
                }
                # pass on the results to the next connected pipe element
                processed_sample = {
                    "image": image,
                    "thumbnail": thumbnail,
                    "inference_result": inference_result,
                    "inference_meta": inf_meta,
                }
                yield processed_sample
            except Exception as e:
                log.error(
                    'Error "%s" while processing sample. ' "Dropping sample: %s",
                    str(e),
                    str(sample),
                )
                log.warning(stacktrace())

    def convert_inference_result(self, inference_result):

        inf_json = []
        if inference_result:
            for inf in inference_result:
                label, confidence, box = inf[0:3]
                log.info(
                    "label: %s , confidence: %.0f, box: %s", label, confidence, box
                )
                one_inf = {
                    "label": label,
                    "confidence": confidence,
                    "box": {
                        "xmin": box[0],
                        "ymin": box[1],
                        "xmax": box[2],
                        "ymax": box[3],
                    },
                }
                inf_json.append(one_inf)

        return inf_json

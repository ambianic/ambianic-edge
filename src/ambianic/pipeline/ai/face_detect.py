"""Face detection pipe element."""
import logging
from .image_boundingBox_detection import TFBoundingBoxDetection

log = logging.getLogger(__name__)


class FaceDetector(TFBoundingBoxDetection):
    """Detecting faces in an image."""

    @staticmethod
    def crop_image(image, box):
        """Crop image to given box."""
        # Size of the image in pixels (size of orginal image)
        # (This is not mandatory)
        width, height = image.size

        # Setting the points for cropped image
        left = box['xmin']*width
        top = box['ymin']*height
        right = box['xmax']*width
        bottom = box['ymax']*height

        # Cropped image of above dimension
        # (It will not change orginal image)
        im1 = image.crop((left, top, right, bottom))
        return im1

    def process_sample(self, **sample):
        """Detect faces in the given image sample."""
        log.debug("Pipe element %s received new sample with keys %s.",
                  self.__class__.__name__,
                  str([*sample]))
        if not sample:
            # pass through empty samples to next element
            yield None
        else:
            try:
                image = sample['image']
                prev_inference_result = sample.get('inference_result', None)

                log.debug("Received sample with inference_result: %s",
                          str(prev_inference_result))
                person_regions = []
                if not prev_inference_result:
                    yield None
                else:
                    # - apply face detection to cropped person areas
                    # - pass face detections on to next pipe element
                    for e_result in prev_inference_result:
                        label, confidence, box = e_result['label'], e_result['confidence'], e_result['box']

                        if label == 'person' and \
                          confidence >= self._tfengine.confidence_threshold:
                            person_regions.append(box)
                    log.debug('Received %d person boxes for face detection',
                              len(person_regions))
                    for box in person_regions:
                        person_image = self.crop_image(image, box)
                        thumbnail, tensor_image, inference_result = \
                            self.detect(image=person_image)

                        inference_result = self.convert_inference_result(inference_result)

                        log.debug('Face detection inference_result: %r',
                                  inference_result)
                        inf_meta = {
                            'display': 'Face Detection',
                        }
                        processed_sample = {
                            'image': person_image,
                            'thumbnail': thumbnail,
                            'inference_result': inference_result,
                            'inference_meta': inf_meta
                            }
                        yield processed_sample
            except Exception as e:
                log.exception('Error %r while processing sample. '
                              'Dropping sample: %r',
                              e,
                              sample)

    def convert_inference_result(self, inference_result):

        inf_json = []
        if inference_result:
            for inf in inference_result:
                label, confidence, box = inf[0:3]
                log.info('label: %s , confidence: %.0f, box: %s',
                        label,
                        confidence,
                        box)
                one_inf = {
                    'label': label,
                    'confidence': float(confidence),
                    'box': {
                        'xmin': float(box[0]),
                        'ymin': float(box[1]),
                        'xmax': float(box[2]),
                        'ymax': float(box[3]),
                    }
                }
                inf_json.append(one_inf)

        return inf_json

"""Fall detection pipe element."""
import logging
import time

from .image_detection import TFImageDetection
from .pose_engine import PoseEngine
from ambianic.util import stacktrace

log = logging.getLogger(__name__)


class FallDetector(TFImageDetection):
    """
    Detects falls in an image.

    :Parameters:
    ----------
    model: dict
      {
        'tflite': 
    'ai_models/posenet_mobilenet_v1_075_721_1281_quant_decoder.tflite'
        'edgetpu': 
    'ai_models/posenet_mobilenet_v1_075_721_1281_quant_decoder_edgetpu.tflite'

        labels: ai_models/pose_labels.txt
    """

    def __init(self):
        self._prev_vals = []
        self._prev_infer_time = time.monotonic()
        self._pose_engine = PoseEngine(self._model_edgetpu_path)
        # This value would need to be tuned experimentally
        # It represents the proportion of full-body distance a person's
        # top body part would need to drop in one second to constitute a fall
        self._fall_factor = 1.5

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
                    self.fall_detect(image=image)
                log.debug('Fall detection inference_result: %r',
                          inference_result)
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
                log.error('Error "%s" while processing sample. '
                          'Dropping sample: %s',
                          str(e),
                          str(sample)
                          )
                log.warning(stacktrace())

    def fall_detect(self, image=None):
        assert image
        start_time = time.monotonic()
        log.debug("Calling TF engine for inference")

        # Width and height input values used in PoseNet tutorial
        width, height = 641, 481

        # thumbnail is a proportionately resized image
        thumbnail = self.thumbnail(image=image, desired_size=(width, height))

        # convert thumbnail into an image with the exact size
        # as the input tensor
        # preserving proportions by padding as needed
        new_im = self.resize(image=thumbnail, desired_size=(width, height))

        w_factor = thumbnail.size[0] / new_im.size[0]
        h_factor = thumbnail.size[1] / new_im.size[1]

        # Detection using tensorflow posenet module
        poses, inference_time = self._pose_engine.DetectPosesInImage(\
                                                  np.uint8(new_im))

        # Obtain time difference between consecutive frames
        time_diff = time.monotonic() - self._prev_infer_time
        self._prev_infer_time = time.monotonic()

        inference_result = []
        pose_vals_list = []
        for i, pose in enumerate(poses):
            if pose.score < 0.5:
                continue
            y0 = min(pose.keypoints.items(), lambda item: item[1].yx[0])
            x0 = min(pose.keypoints.items(), lambda item: item[1].yx[1])
            y1 = max(pose.keypoints.items(), lambda item: item[1].yx[0])
            x1 = min(pose.keypoints.items(), lambda item: item[1].yx[1])
            # Record pose values for comparison
            pose_vals_list.append((y0, y1))
            # Compare poses to the corresponding pose in the last frame
            # This could cause errors if pose detections change between frames
            try:
                # Algorithm for fall detection is based on high and low y vals
                if y0 >= self._prev_vals[i][0] - self._fall_factor * \
            time_diff * (self._prev_vals[i][0] - self._prev_vals[i][1]):

                    inference_result.append((
                        'FALL',
                        pose.score,
                        (x0 / w_factor, y0 / h_factor, \
                         x1 / w_factor, y1 / h_factor)))
            except:
                pass

        self._prev_vals = pose_vals_list

        return thumbnail, new_im, inference_result

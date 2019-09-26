"""Tensorflow image detection wrapper."""
import logging
import time
import re
import abc
import numpy as np
# from importlib import import_module
from ambianic.pipeline import PipeElement
from .inference import TFInferenceEngine
from PIL import Image, ImageOps

log = logging.getLogger(__name__)


class TFImageDetection(PipeElement):
    """Applies Tensorflow image detection."""

    def __init__(self, element_config=None):
        """Initialize detector with config parameters.

        :Parameters:
        ----------
        element_config : dict from yaml config
            Example:
                model: ai_models/mobilenet_ssd_v2_face.tflite
                labels: ai_models/coco_labels.txt
                confidence_threshold: 0.6
                top-k: 3

        """
        super()
        self._tfengine = TFInferenceEngine(*element_config)
        self._labels = self.load_labels(self.labels_path())
        self.last_time = time.monotonic()

    def load_labels(self, label_path=None):
        """Load label mapping from integer code to text.

        :Parameters:
        ----------
        label_path : string
            Path to label mapping file.

        :Returns:
        -------
        dict
            {label_code, label_text}

        """
        assert label_path
        p = re.compile(r'\s*(\d+)(.+)')
        with open(label_path, 'r', encoding='utf-8') as f:
            lines = (p.match(line).groups() for line in f.readlines())
            return {int(num): text.strip() for num, text in lines}

    def resize_to_fit(self, image=None, desired_size=None):
        """Resizes original image to size expected by input tensor.

        :Parameters:
        ----------
        image : PIL.Image
            Input Image for AI model detection.

        desired_size : (width, height)
            Size expected by the AI model.

        Preserves aspect ratio to avoid confusing the AI model with
        an unnatural distortion. Pads resulting image
        with solid black color pixels as necessary.

        Does not modify the original image.

        :Returns:
        -------
        PIL.Image
            Resized image fitting for the AI model input tensor.

        """
        assert isinstance(image, Image)
        assert desired_size
        log.debug('current image size = %r', image.size)
        thumb = image.copy()
        thumb.thumbnail(desired_size)
        log.debug('thmubnail image size = %r', thumb.size)
        delta_w = desired_size[0] - thumb.size[0]
        delta_h = desired_size[1] - thumb.size[1]
        padding = (0, 0, delta_w, delta_h)
        new_im = ImageOps.expand(thumb, padding)
        log.debug('new image size = %r', new_im.size)
        assert new_im.size == desired_size
        return new_im

    def _log_stats(self, start_time=None):
        assert start_time
        log.debug("TF engine returned inference results")
        end_time = time.monotonic()
        inf_time = (end_time - start_time) * 1000
        fps = 1.0/(end_time - self.last_time)
        inf_info = 'Inference: %.2f ms  FPS: %.2f fps'
        log.debug(inf_info, inf_time, fps)
        self.last_time = end_time

    def detect(self, image=None):
        """Detect objects in image.

        :Parameters:
        ----------
        image : PIL.Image
            Input image in raw RGB format.

        :Returns:
        -------
        list of tuples
            List of top-k detections above confidence_threshold.
            Each detection is a tuple of:
            (category, confidence, (x0, y0, x1, y1))

        """
        assert image
        start_time = time.monotonic()
        log.debug("Calling TF engine for inference")

        # NxHxWxC, H:1, W:2
        height = self.input_details[0]['shape'][1]
        width = self.input_details[0]['shape'][2]

        new_im = self.resize_to_fit(image=image, desired_size=(width, height))

        # add N dim
        input_data = np.expand_dims(new_im, axis=0)

        if not self.is_quantized():
            # normalize floating point values
            input_mean = 127.5
            input_std = 127.5
            input_data = \
                (np.float32(input_data) - input_mean) / input_std

        self._tfengine.set_tensor(self.input_details[0]['index'], input_data)

        self._tfengine.invoke()

        self._log_stats(start_time=start_time)

        # get output tensor
        boxes = self._tfengine.get_tensor(self.output_details[0]['index'])
        label_codes = self._tfengine.get_tensor(
            self.output_details[1]['index'])
        scores = self._tfengine.get_tensor(self.output_details[2]['index'])
        # num = self._tfengine.get_tensor(self.output_details[3]['index'])
        # detections_count = min(num, boxes.shape[1])

        inference_result = []

        # get a list of indices for the top_k results
        # ordered from highest to lowest confidence
        top_k_indices = np.argsort(scores[0])[-1*self.top_k:][::-1]
        # from the top_k results, only take the ones that score
        # above the confidence threshold criteria.
        for i in top_k_indices:
            if scores[0, i] >= self.confidence_threshold:
                confidence = scores[0, i]
                category = self._labels[int(label_codes[0, i])]
                box = boxes[0, i, :]
                x0 = box[1]
                y0 = box[0]
                x1 = box[3]
                y1 = box[2]
                inference_result.append((
                    category,
                    confidence,
                    (x0, y0, x1, y1)))
        return inference_result
#        objs = self.engine.DetectWithImage(
#            image,
#            threshold=self.confidence_threshold,
#            keep_aspect_ratio=True,
#            relative_coord=True,
#            top_k=3)
#
#        for obj in objs:
#            x0, y0, x1, y1 = obj.bounding_box.flatten().tolist()
#            confidence = obj.score
#            category = self.labels[obj.label_id]
#            inference_result.append((category, confidence, (x0, y0, x1, y1)))
#        return inference_result

    @abc.abstractmethod
    def receive_next_sample(self, image):
        """Handle the next sample presented from the previous pipe element.

        :Parameters:
        ----------
        image : PIL.Image
            Image produced by the previous pipe element.

        """
        pass

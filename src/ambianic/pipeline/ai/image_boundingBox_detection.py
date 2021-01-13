"""Tensorflow image detection wrapper."""
import logging
import time
import re
import numpy as np
# from importlib import import_module
from PIL import ImageOps
from .inference import TFInferenceEngine
from ambianic.pipeline import PipeElement
from ambianic.pipeline.ai.tf_detect import TFDetectionModel

log = logging.getLogger(__name__)


class TFBoundingBoxDetection(PipeElement):
    """Applies Tensorflow image detection."""

    def __init__(self,
                 model=None,
                 labels=None,
                 label_filter=None,
                 confidence_threshold=0.6,
                 top_k=3,
                 **kwargs
                 ):
        """Initialize detector with config parameters.

        :Parameters:
        ----------
        model: ai_models/mobilenet_ssd_v2_face.tflite
        labels: ai_models/coco_labels.txt
        confidence_threshold: 0.6
        top_k: 3

        """
        # log.warning('TFImageDetection __init__ invoked')
        super().__init__(**kwargs)

        self._tfDetect = TFDetectionModel(model=model,
                    labels=labels,
                    confidence_threshold=confidence_threshold,
                    top_k=top_k, **kwargs)

        self._tfengine = self._tfDetect._tfengine
        self._labels = self._tfDetect._labels
        self._label_filter = label_filter


    def detect(self, image=None):
        """Detect objects in image.

        :Parameters:
        ----------
        image : PIL.Image
            Input image in raw RGB format
            with the exact size of the input tensor.

        :Returns:
        -------
        list of tuples
            List of top_k detections above confidence_threshold.
            Each detection is a tuple of:
            (label, confidence, (x0, y0, x1, y1))

        """
        assert image
        start_time = time.monotonic()
        log.debug("Calling TF engine for inference")

        tfe = self._tfengine

        # NxHxWxC, H:1, W:2
        height = tfe.input_details[0]['shape'][1]
        width = tfe.input_details[0]['shape'][2]

        desired_size = (width, height)
        # thumbnail is a proportionately resized image
        thumbnail = self._tfDetect.thumbnail(image=image, desired_size=desired_size)
        # convert thumbnail into an image with the exact size
        # as the input tensor
        # preserving proportions by padding as needed
        new_im = self._tfDetect.resize(image=thumbnail, desired_size=desired_size)

        # calculate what fraction of the new image is the thumbnail size
        # we will use these factors to adjust detection box coordinates
        w_factor = thumbnail.size[0] / new_im.size[0]
        h_factor = thumbnail.size[1] / new_im.size[1]

        # add N dim
        input_data = np.expand_dims(new_im, axis=0)
        # log.warning('input_data.shape: %r', input_data.shape)
        # log.warning('input_data.dtype: %r', input_data.dtype)
        # input_data = input_data.astype(np.uint8)
        # log.warning('input_data.dtype: %r', input_data.dtype)
        # input_data = np.asarray(input_data).flatten()

        # Note: Floating models are not tested thoroughly yet.
        # Its not clear yet whether floating models will be a good fit
        # for Ambianic use cases. Optimized quantized models seem to do
        # a good job in terms of accuracy and speed.
        if not tfe.is_quantized:  # pragma: no cover
            # normalize floating point values
            input_mean = 127.5
            input_std = 127.5
            input_data = \
                (np.float32(input_data) - input_mean) / input_std

        tfe.set_tensor(tfe.input_details[0]['index'], input_data)

        # invoke inference on the new input data
        # with the configured model
        tfe.infer()

        self._tfDetect.log_stats(start_time=start_time)

        # log.debug('output_details: %r', tfe.output_details)
        # od = tfe.output_details[0]['index']
        # log.debug('output_data[0]: %r',
        #             tfe.get_tensor(od))
        # log.debug('output_data[0]: %r',
        #             tfe._tf_interpreter.get_tensor(od))

        # get output tensor
        boxes = tfe.get_tensor(tfe.output_details[0]['index'])
        label_codes = tfe.get_tensor(
            tfe.output_details[1]['index'])
        scores = tfe.get_tensor(tfe.output_details[2]['index'])
        num = tfe.get_tensor(tfe.output_details[3]['index'])
        # log.warning('Detections:\n num: %r\n label_codes: %r\n scores: %r\n',
        #             num, label_codes, scores)
        # log.warning('Required confidence: %r',
        #             tfe.confidence_threshold)
        detections_count = int(num[0])

        inference_result = []
        # get a list of indices for the top_k results
        # ordered from highest to lowest confidence.
        # We are only interested in scores within detections_count range
        indices_of_sorted_scores = np.argsort(scores[0, :detections_count])
        # log.warning('Indices of sorted scores: %r:',
        #             indices_of_sorted_scores)
        top_k_indices = indices_of_sorted_scores[-1*tfe.top_k:][::-1]
        # log.warning('Indices of top_k scores: %r:', top_k_indices)
        # from the top_k results, only take the ones that score
        # above the confidence threshold criteria.
        for i in top_k_indices:
            confidence = scores[0, i]
            if confidence >= tfe.confidence_threshold:
                # log.warning('Sample confidence: %r, required confidence %r',
                #             confidence, tfe.confidence_threshold)
                li = int(label_codes[0, i])
                # protect against models that return arbitrary labels
                # when the confidence is low
                if (li < len(self._labels)):
                    label = self._labels[li]
                    # If a label filter is specified, apply it.
                    if (not self._label_filter or label in self._label_filter):
                        box = boxes[0, i, :]
                        # refit detections into original image size
                        # without overflowing outside image borders
                        x0 = box[1] / w_factor
                        y0 = box[0] / h_factor
                        x1 = min(box[3] / w_factor, 1)
                        y1 = min(box[2] / h_factor, 1)
                        log.debug('thumbnail image size: %r , '
                                'tensor image size: %r',
                                thumbnail.size,
                                new_im.size)
                        log.debug('resizing detection box (x0, y0, x1, y1) '
                                'from: %r to %r',
                                (box[1], box[0], box[3], box[2]),
                                (x0, y0, x1, y1))
                        inference_result.append((
                            label,
                            confidence,
                            (x0, y0, x1, y1)))
        return thumbnail, new_im, inference_result

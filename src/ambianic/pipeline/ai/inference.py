"""Tensorflow inference engine wrapper."""
import logging
import time
import re
import os
import abc
import numpy as np
# from importlib import import_module
from tflite_runtime.interpreter import Interpreter
from tflite_runtime.interpreter import load_delegate
from ambianic.pipeline import PipeElement

log = logging.getLogger(__name__)


class TFInferenceEngine:
    """Wraps a TF engine.

    Dynamically detects if EdgeTPU is available and uses it.
    Otherwise falls back to TFLite Runtime.
    """

    def __init__(self,
                 model_tflite=None,
                 model_edgetpu=None,
                 labels=None,
                 confidence_threshold=0.8,
                 top_k=10
                 ):
        """Create an instance of Tensorflow inference engine.

        :Parameters:
        ----------
        model_tflite : string
            Location of frozen TFLite graph file.
        model_edgetpu : string
            Location of frozen TF EdgeTPU graph file.
        labels : string
            Location of labels file.
        confidence_threshold : float
            Inference confidence threshold.
        top_k : type
            Inference top-k threshold.

        """
        assert model_tflite, 'TFLite AI model path required.'
        assert os.path.isfile(model_tflite), \
            'TFLite AI model file does not exist: {}' \
            .format(model_tflite)
        self._model_tflite_path = model_tflite
        if model_edgetpu:
            assert os.path.isfile(model_edgetpu), \
                'EdgeTPU AI model file does not exist: {}' \
                .format(model_edgetpu)
        self._model_edgetpu_path = model_edgetpu
        assert labels, 'AI model labels path required.'
        assert os.path.isfile(labels), \
            'AI model labels file does not exist: {}' \
            .format(labels)
        self._labels_path = labels
        self._confidence_threshold = confidence_threshold
        self._top_k = top_k
        log.debug('Loading AI model:\n'
                  'TFLite graph: %s\n'
                  'EdgeTPU graph: %s\n'
                  'Labels %s.',
                  'Condidence threshod: %.0f%%',
                  'top-k: %d',
                  model_tflite,
                  model_edgetpu,
                  labels,
                  confidence_threshold*100,
                  top_k)
        # EdgeTPU is not available in testing and other environments
        # load dynamically as needed
#        edgetpu_class = 'DetectionEngine'
#        module_object = import_module('edgetpu.detection.engine',
#                                      packaage=edgetpu_class)
#        target_class = getattr(module_object, edgetpu_class)
        if (model_edgetpu):
            self._tf_interpreter = Interpreter(
                model_path=model_edgetpu,
                experimental_delegates=[load_delegate('libedgetpu.so.1.0')])
        if self._tf_interpreter:
            log.debug('EdgeTPU installed. Will use EdgeTPU model.')
        else:
            log.debug('EdgeTPU not installed. Will use TFLite model.')
            self._tf_interpreter = Interpreter(model_path=model_tflite)
        self._tf_interpreter.allocate_tensors()

        self._tf_input_details = self._tf_interpreter.get_input_details()
        self._tf_output_details = self._tf_interpreter.get_output_details()

        # check the type of the input tensor
        self._tf_is_quantized_model = \
            self._tf_input_details[0]['dtype'] != np.float32

        @property
        def input_details(self):
            return self._tf_input_details

        @property
        def output_details(self):
            return self._tf_output_details

        @property
        def is_quantized():
            return self._tf_is_quantized_model

        @property
        def model_tflite_path(self):
            """
            Location of frozen TFLite graph file (AI model).

            :Returns:
            -------
            string
                Path to a TFLite ready inference graph.

            """
            return self._model_tflite_path

        @property
        def model_edgetpu_path(self):
            """
            Location of frozen TF EdgeTPU graph file (AI model).

            :Returns:
            -------
            string
                Path to a Google Coral EdgeTPU ready inference graph.

            """
            return self._model_edgetpu_path

        @property
        def labels_path(self):
            """
            Location of labels file.

            :Returns:
            -------
            string
                Path to AI model labels.

            """
            return self._model_labels_path

        @property
        def confidence_threshold(self):
            """
            Inference confidence threshold.

            :Returns:
            -------
            float
                Confidence threshold for inference results.
                Only results at or above
                this threshold should be returned by each engine inference.

            """
            return self._confidence_threshold

        @property
        def top_k(self):
            """
            Inference top-k threshold.

            :Returns:
            -------
            int
                Max number of results to be returned by each inference.
                Ordered by confidence score.

            """
            return self._top_k

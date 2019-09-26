import pytest
from ambianic.pipeline.ai.inference import TFInferenceEngine


def test_inference_init_no_params():
    with pytest.raises(AssertionError):
        TFInferenceEngine()


def test_inference_init_no_model_yes_labels():
    pass


def test_inference_init_no_tflite_model_yes_edgemodel():
    with pytest.raises(AssertionError):
        TFInferenceEngine()


def test_inference_init_yes_tflite_model_no_edgemodel():
    with pytest.raises(AssertionError):
        TFInferenceEngine()


def test_inference_init_yes_model_yes_labels():
    with pytest.raises(AssertionError):
        TFInferenceEngine()

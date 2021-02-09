"""Test fall detection pipe element."""
from ambianic.pipeline.ai.fall_detect import FallDetector
from ambianic.pipeline.ai.object_detect import ObjectDetector
from ambianic.pipeline import PipeElement
import os
import time
from PIL import Image


def _fall_detect_config():

    _dir = os.path.dirname(os.path.abspath(__file__))
    _good_tflite_model = os.path.join(
        _dir,
        'posenet_mobilenet_v1_100_257x257_multi_kpt_stripped.tflite'
        )
    _good_edgetpu_model = os.path.join(
        _dir,
        'posenet_mobilenet_v1_075_721_1281_quant_decoder_edgetpu.tflite'
        )
    _good_labels = os.path.join(_dir, 'pose_labels.txt')
    config = {
        'model': {
            'tflite': _good_tflite_model,
            'edgetpu': _good_edgetpu_model,
            },
        'labels': _good_labels,
        'top_k': 3,
        'confidence_threshold': 0.235,
    }
    return config


def test_model_inputs():
    """Verify against known model inputs."""
    config = _fall_detect_config()
    fall_detector = FallDetector(**config)
    tfe = fall_detector._tfengine

    samples = tfe.input_details[0]['shape'][0]
    assert samples == 1
    height = tfe.input_details[0]['shape'][1]
    assert height == 257
    width = tfe.input_details[0]['shape'][2]
    assert width == 257
    colors = tfe.input_details[0]['shape'][3]
    assert colors == 3

def test_config_confidence_threshold():
    """Verify against known confidence threshold. Make sure it propagates at all levels."""
    config = _fall_detect_config()
    fall_detector = FallDetector(**config)
    tfe = fall_detector._tfengine
    pe = fall_detector._pose_engine
    assert fall_detector.confidence_threshold == config['confidence_threshold']
    assert pe.confidence_threshold == config['confidence_threshold']
    assert tfe.confidence_threshold == config['confidence_threshold']
    config['confidence_threshold'] = 0.457
    fall_detector = FallDetector(**config)
    tfe = fall_detector._tfengine
    pe = fall_detector._pose_engine
    assert fall_detector.confidence_threshold == config['confidence_threshold']
    assert pe.confidence_threshold == config['confidence_threshold']
    assert tfe.confidence_threshold == config['confidence_threshold']

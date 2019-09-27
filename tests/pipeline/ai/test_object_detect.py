"""Test object detection pipe element."""
import pytest
import os
from ambianic.pipeline.ai.object_detect import ObjectDetector
from ambianic.pipeline import PipeElement
from PIL import Image

def _object_detect_config():
    dir = os.path.dirname(os.path.abspath(__file__))
    _good_tflite_model = os.path.join(
        dir,
        'mobilenet_ssd_v2_coco_quant_postprocess.tflite'
        )
    _good_edgetpu_model = os.path.join(
        dir,
        'mobilenet_ssd_v2_coco_quant_postprocess_edgetpu.tflite'
        )
    _good_labels = os.path.join(dir, 'coco_labels.txt')
    config = {
        'model': {
            'tflite': _good_tflite_model,
            'edgetpu': _good_edgetpu_model,
            },
        'labels': _good_labels,
        'top_k': 3,
        'confidence_threshold': 0.8,
    }
    return config


def _get_image(file_name=None):
    assert file_name
    dir = os.path.dirname(os.path.abspath(__file__))
    image_file = os.path.join(dir, file_name)
    img = Image.open(image_file)
    return img


class OutPipeElement(PipeElement):

    def __init__(self, sample_callback=None):
        super()
        assert sample_callback
        self._sample_callback = sample_callback

    def receive_next_sample(self, **sample):
        self._sample_callback(**sample)
        pass


def test_backgground_image():
    """Expect to not detect anything interesting in a background image."""
    config = _object_detect_config()
    result = None

    def sample_callback(image=None, inference_result=None):
        nonlocal result
        result = inference_result
    object_detector = ObjectDetector(element_config=config)
    output = OutPipeElement(sample_callback=sample_callback)
    object_detector.connect_to_next_element(output)
    img = _get_image(file_name='background.jpg')
    object_detector.receive_next_sample(image=img)
    assert not result


def no_test_one_person():
    """Expect to detect one person."""
    config = _object_detect_config()
    result = None

    def sample_callback(image=None, inference_result=None):
        nonlocal result

        result = inference_result
    object_detector = ObjectDetector(element_config=config)
    output = OutPipeElement(sample_callback=sample_callback)
    object_detector.connect_to_next_element(output)
    img = _get_image(file_name='person.jpg')
    object_detector.receive_next_sample(image=img)
    assert result
    assert len(result) == 1
    category, confidence, (x0, y0, x1, y1) = result[0]
    assert category == 'person'
    assert confidence > 0.9
    assert x0 > 0 and x0 < x1
    assert y0 > 0 and y0 < y1

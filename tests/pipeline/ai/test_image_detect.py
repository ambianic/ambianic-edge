"""Test image detection pipe element."""
import pytest
import os
from PIL import Image

from ambianic.pipeline.ai.image_detection import TFImageDetection


def test_inference_init_no_config():
    with pytest.raises(AssertionError):
        TFImageDetection()


def test_inference_init_bad_config():
    config = {
        'model': {
            'tflite': 'some_bad_tflite_model',
            },
        'labels': 'no_labels',
        'top_k': 123,
        'confidence_threshold': 654,
    }
    with pytest.raises(AssertionError):
        TFImageDetection(config)


def _good_config():
    _dir = os.path.dirname(os.path.abspath(__file__))
    _good_tflite_model = os.path.join(
        _dir,
        'mobilenet_ssd_v2_coco_quant_postprocess.tflite'
        )
    _good_edgetpu_model = os.path.join(
        _dir,
        'mobilenet_ssd_v2_coco_quant_postprocess_edgetpu.tflite'
        )
    _good_labels = os.path.join(_dir, 'coco_labels.txt')
    config = {
        'model': {
            'tflite': _good_tflite_model,
            'edgetpu': _good_edgetpu_model,
            },
        'labels': _good_labels,
        'top_k': 123,
        'confidence_threshold': 0.654,
    }
    return config


def test_inference_init_good_config():
    config = _good_config()
    img_detect = TFImageDetection(config)
    assert img_detect
    assert img_detect._tfengine
    assert img_detect._tfengine._model_tflite_path.endswith('.tflite')
    assert img_detect._tfengine._model_edgetpu_path.endswith('.tflite')
    assert img_detect._tfengine.confidence_threshold == 0.654
    assert img_detect._tfengine.top_k == 123
    assert img_detect._tfengine.is_quantized
    assert img_detect._tfengine._model_labels_path.endswith('.txt')


def test_model_inputs():
    """Verify against known model inputs."""
    config = _good_config()
    img_detect = TFImageDetection(config)
    tfe = img_detect._tfengine
    samples = tfe.input_details[0]['shape'][0]
    assert samples == 1
    height = tfe.input_details[0]['shape'][1]
    assert height == 300
    width = tfe.input_details[0]['shape'][2]
    assert width == 300
    colors = tfe.input_details[0]['shape'][3]
    assert colors == 3


def test_model_outputs():
    """Verify against known model outputs."""
    config = _good_config()
    img_detect = TFImageDetection(config)
    tfe = img_detect._tfengine
    assert tfe.output_details[0]['shape'][0] == 1
    scores = tfe.output_details[0]['shape'][1]
    assert scores == 20
    assert tfe.output_details[1]['shape'][0] == 1
    boxes = tfe.output_details[1]['shape'][1]
    assert boxes == 20
    assert tfe.output_details[2]['shape'][0] == 1
    labels = tfe.output_details[2]['shape'][1]
    assert labels == 20
    num = tfe.output_details[3]['shape'][0]
    assert num == 1


def test_resize():
    config = _good_config()
    img_detect = TFImageDetection(config)
    _dir = os.path.dirname(os.path.abspath(__file__))
    img_path = os.path.join(_dir, 'background.jpg')
    image = Image.open(img_path)
    orig_width = image.size[0]
    assert orig_width == 1280
    orig_height = image.size[1]
    assert orig_height == 720
    new_size = (300, 300)
    new_image = img_detect.resize(image=image, desired_size=new_size)
    new_width = new_image.size[0]
    assert new_width == new_size[0]
    new_height = new_image.size[1]
    assert new_height == new_size[1]


def test_receive_next_sample():
    config = _good_config()
    img_detect = TFImageDetection(config)
    # no action expected from the abstract method
    img_detect.receive_next_sample(image=None)


def test_load_labels():
    config = _good_config()
    img_detect = TFImageDetection(config)
    labels = img_detect._labels
    assert labels[0] == 'person'
    assert labels[15] == 'bird'

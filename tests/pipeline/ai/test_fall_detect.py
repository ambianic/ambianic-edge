"""Test fall detection pipe element."""
import os
from ambianic.pipeline.ai.fall_detect import FallDetector
from ambianic.pipeline.ai.object_detect import ObjectDetector
from ambianic.pipeline import PipeElement
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
        'confidence_threshold': 0.8,
    }
    return config


def _get_image(file_name=None):
    assert file_name
    _dir = os.path.dirname(os.path.abspath(__file__))
    image_file = os.path.join(_dir, file_name)
    img = Image.open(image_file)
    return img


class _OutPipeElement(PipeElement):

    def __init__(self, sample_callback=None):
        super().__init__()
        assert sample_callback
        self._sample_callback = sample_callback

    def receive_next_sample(self, **sample):
        self._sample_callback(**sample)


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


def test_fall_detection_case_1():
    """Expected to not detect a fall as key-points are not detected."""
    config = _fall_detect_config()
    result = None

    def sample_callback(image=None, inference_result=None, **kwargs):
        nonlocal result
        result = inference_result

    fall_detector = FallDetector(**config)

    output = _OutPipeElement(sample_callback=sample_callback)
    fall_detector.connect_to_next_element(output)

    img_1 = _get_image(file_name='fall_img_1.png')
    img_2 = _get_image(file_name='fall_img_3.png')
    fall_detector.receive_next_sample(image=img_1)
    fall_detector.receive_next_sample(image=img_2)

    assert not result
    
def test_fall_detection_case_2():
    """Expected to detect a fall as key-points are detected."""
    config = _fall_detect_config()
    result = None

    def sample_callback(image=None, inference_result=None, **kwargs):
        nonlocal result
        result = inference_result

    fall_detector = FallDetector(**config)

    output = _OutPipeElement(sample_callback=sample_callback)
    
    fall_detector.connect_to_next_element(output)

    img_1 = _get_image(file_name='fall_img_1.png')
    img_2 = _get_image(file_name='fall_img_2.png')
    fall_detector.receive_next_sample(image=img_1)
    fall_detector.receive_next_sample(image=img_2)

    assert result
    assert len(result) == 1
    category, confidence = result[0]
    assert category == 'FALL'
    assert confidence > 0.7
    
def test_fall_detection_case_3():
    """Expected to detect a fall as key-points are detected by rotating the image."""
    config = _fall_detect_config()
    result = None

    def sample_callback(image=None, inference_result=None, **kwargs):
        nonlocal result
        result = inference_result

    fall_detector = FallDetector(**config)

    output = _OutPipeElement(sample_callback=sample_callback)
    
    fall_detector.connect_to_next_element(output)

    img_1 = _get_image(file_name='fall_img_1.png')
    img_2 = _get_image(file_name='fall_img_5.png')
    fall_detector.receive_next_sample(image=img_1)
    fall_detector.receive_next_sample(image=img_2)

    assert result
    assert len(result) == 1
    category, confidence = result[0]
    assert category == 'FALL'
    assert confidence > 0.25


def test_background_image():
    """Expect to not detect anything interesting in a background image."""
    config = _fall_detect_config()
    result = None

    def sample_callback(image=None, inference_result=None, **kwargs):
        nonlocal result
        result = inference_result
    fall_detector = FallDetector(**config)
    output = _OutPipeElement(sample_callback=sample_callback)
    fall_detector.connect_to_next_element(output)
    img = _get_image(file_name='background.jpg')
    fall_detector.receive_next_sample(image=img)
    assert not result


def test_no_sample():
    """Expect element to pass empty sample to next element."""
    config = _fall_detect_config()
    result = 'Something'

    def sample_callback(image=None, inference_result=None, **kwargs):
        nonlocal result
        result = image is None and inference_result is None
    fall_detector = FallDetector(**config)
    output = _OutPipeElement(sample_callback=sample_callback)
    fall_detector.connect_to_next_element(output)
    fall_detector.receive_next_sample()
    assert result is True


def test_bad_sample_good_sample():
    """One bad sample should not prevent good samples from being processed."""
    config = _fall_detect_config()
    result = 'nothing passed to me'

    def sample_callback(image=None, inference_result=None, **kwargs):
        nonlocal result
        result = inference_result
    object_detector = ObjectDetector(**config)
    output = _OutPipeElement(sample_callback=sample_callback)
    object_detector.connect_to_next_element(output)
    # bad sample
    object_detector.receive_next_sample(image=None)
    assert result == 'nothing passed to me'

    # good sample
    fall_detector = FallDetector(**config)
    fall_detector.connect_to_next_element(output)

    img_1 = _get_image(file_name='fall_img_1.png')
    img_2 = _get_image(file_name='fall_img_2.png')
    fall_detector.receive_next_sample(image=img_1)
    fall_detector.receive_next_sample(image=img_2)

    assert result
    assert len(result) == 1
    category, confidence = result[0]
    assert category == 'FALL'
    assert confidence > 0.7

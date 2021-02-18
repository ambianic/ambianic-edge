"""Test audio/video source pipeline element."""
import pytest
from ambianic.pipeline.avsource.av_element \
    import AVSourceElement, MIN_HEALING_INTERVAL
import threading
import os
import pathlib
import time
from ambianic.pipeline import PipeElement
from ambianic.pipeline.ai.object_detect import ObjectDetector
import logging

log = logging.getLogger()
log.setLevel(logging.DEBUG)


def _object_detect_config():
    _dir = os.path.dirname(os.path.abspath(__file__))
    _good_tflite_model = os.path.join(
        _dir,
        '../ai/mobilenet_ssd_v2_coco_quant_postprocess.tflite'
        )
    _good_edgetpu_model = os.path.join(
        _dir,
        '../ai/mobilenet_ssd_v2_coco_quant_postprocess_edgetpu.tflite'
        )
    _good_labels = os.path.join(_dir, '../ai/coco_labels.txt')
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


class _TestAVSourceElement(AVSourceElement):

    def __init__(self, **source_conf):
        super().__init__(**source_conf)
        self._run_http_fetch_called = False

    def _run_http_fetch(self, url=None, continuous=False):
        self._run_http_fetch_called = True
        super()._run_http_fetch(url=url, continuous=continuous)

class _OutPipeElement(PipeElement):

    def __init__(self, sample_callback=None):
        super().__init__()
        assert sample_callback
        self._sample_callback = sample_callback

    def receive_next_sample(self, **sample):
        self._sample_callback(**sample)


def test_http_still_image_input_detect_person_exit():
    """Process a single jpg image. Detect a person and exit pipeline."""
    source_uri = 'https://raw.githubusercontent.com/ambianic/ambianic-edge/master/tests/pipeline/ai/person.jpg'
    avsource = _TestAVSourceElement(uri=source_uri, type='image', live=False)
    object_config = _object_detect_config()
    detection_received = threading.Event()
    sample_image = None
    detections = None

    def sample_callback(image=None, inference_result=None, **kwargs):
        nonlocal sample_image
        nonlocal detection_received
        sample_image = image
        nonlocal detections
        detections = inference_result
        print('detections: {det}'.format(det=detections))
        print('len(detections): {len}'.format(len=len(detections)))
        if detections:
            label, confidence, _ = detections[0]
            if label == 'person' and confidence > 0.9:
                # skip video image samples until we reach a person detection
                # with high level of confidence
                detection_received.set()

    object_detector = ObjectDetector(**object_config)
    avsource.connect_to_next_element(object_detector)
    output = _OutPipeElement(sample_callback=sample_callback)
    object_detector.connect_to_next_element(output)
    t = threading.Thread(
        name="Test AVSourceElement",
        target=avsource.start, daemon=True
        )
    t.start()
    detection_received.wait(timeout=10)
    assert avsource._run_http_fetch_called
    assert sample_image
    assert sample_image.size[0] == 1280
    assert sample_image.size[1] == 720
    assert detections
    assert len(detections) == 1
    label, confidence, (x0, y0, x1, y1) = detections[0]
    assert label == 'person'
    assert confidence > 0.9
    assert x0 > 0 and x0 < x1
    assert y0 > 0 and y0 < y1
    t.join(timeout=10)
    assert not t.is_alive()


def test_http_still_image_input_detect_person_exit_stop_signal():
    """Proces a single jpg image. Detect a person. Exit via stop signal."""
    source_uri = 'https://raw.githubusercontent.com/ambianic/ambianic-edge/master/tests/pipeline/ai/person.jpg'
    avsource = AVSourceElement(uri=source_uri, type='image', live=True)
    object_config = _object_detect_config()
    detection_received = threading.Event()
    sample_image = None
    detections = None

    def sample_callback(image=None, inference_result=None, **kwargs):
        nonlocal sample_image
        nonlocal detection_received
        sample_image = image
        nonlocal detections
        detections = inference_result
        print('detections: {det}'.format(det=detections))
        print('len(detections): {len}'.format(len=len(detections)))
        if detections:
            label, confidence, _ = detections[0]
            if label == 'person' and confidence > 0.9:
                # skip video image samples until we reach a person detection
                # with high level of confidence
                detection_received.set()
    object_detector = ObjectDetector(**object_config)
    avsource.connect_to_next_element(object_detector)
    output = _OutPipeElement(sample_callback=sample_callback)
    object_detector.connect_to_next_element(output)
    t = threading.Thread(
        name="Test AVSourceElement",
        target=avsource.start, daemon=True
        )
    t.start()
    detection_received.wait(timeout=10)
    assert sample_image
    assert sample_image.size[0] == 1280
    assert sample_image.size[1] == 720
    assert detections
    assert len(detections) == 1
    label, confidence, (x0, y0, x1, y1) = detections[0]
    assert label == 'person'
    assert confidence > 0.9
    assert x0 > 0 and x0 < x1
    assert y0 > 0 and y0 < y1
    avsource.stop()
    t.join(timeout=10)
    assert not t.is_alive()

class _TestAVSourceElement2(AVSourceElement):

    def __init__(self, **source_conf):
        super().__init__(**source_conf)
        self._bad_sample_processed_re = False
        self._bad_sample_processed_ae = False

    def _get_sample_queue(self):
        q = super()._get_sample_queue()
        # put a fake bad sample on the queue to test exception handling
        q.put('A bad sample to test RuntimeError.')
        q.put('Another bad sample to test AssertionError.')
        return q

    def _on_new_sample(self, sample=None):
        if not self._bad_sample_processed_re:
            # through a RuntimeError once then proceed as normal
            # the pipe element should log the exception but keep running
            print('RuntimeError during processing.')
            self._bad_sample_processed_re = True
            raise RuntimeError('Something went wrong during processing.')
        if not self._bad_sample_processed_ae:
            # through an AssertionError once then proceed as normal
            # the pipe element should log the exception but keep running
            print('AssertionError during processing.')
            self._bad_sample_processed_ae = True
            raise AssertionError('Something went wrong during processing.')
        super()._on_new_sample(sample)


def test_exception_on_new_sample():
    """Exception from _on_new_sample() should not break the pipe loop."""
    source_uri = 'https://raw.githubusercontent.com/ambianic/ambianic-edge/master/tests/pipeline/ai/person.jpg'
    avsource = _TestAVSourceElement2(uri=source_uri, type='image', live=False)
    object_config = _object_detect_config()
    detection_received = threading.Event()
    sample_image = None
    detections = None

    def sample_callback(image=None, inference_result=None, **kwargs):
        nonlocal sample_image
        nonlocal detection_received
        sample_image = image
        nonlocal detections
        detections = inference_result
        print('detections: {det}'.format(det=detections))
        print('len(detections): {len}'.format(len=len(detections)))
        if detections:
            label, confidence, _ = detections[0]
            if label == 'person' and confidence > 0.9:
                # skip video image samples until we reach a person detection
                # with high level of confidence
                detection_received.set()
    object_detector = ObjectDetector(**object_config)
    avsource.connect_to_next_element(object_detector)
    output = _OutPipeElement(sample_callback=sample_callback)
    object_detector.connect_to_next_element(output)
    t = threading.Thread(
        name="Test AVSourceElement",
        target=avsource.start, daemon=True
        )
    t.start()
    detection_received.wait(timeout=10)
    assert sample_image
    assert sample_image.size[0] == 1280
    assert sample_image.size[1] == 720
    assert detections
    assert len(detections) == 1
    label, confidence, (x0, y0, x1, y1) = detections[0]
    assert label == 'person'
    assert confidence > 0.9
    assert x0 > 0 and x0 < x1
    assert y0 > 0 and y0 < y1
    t.join(timeout=3)
    assert not t.is_alive()


class _TestAVSourceElement3(AVSourceElement):

    def __init__(self, **source_conf):
        super().__init__(**source_conf)
        self._run_http_fetch_called = False
        self._on_fetch_img_exception_called = False
        self._fetch_img_exception_recovery_called = threading.Event()

    def _run_http_fetch(self, url=None, continuous=False):
        self._run_http_fetch_called = True
        super()._run_http_fetch(url=url, continuous=continuous)

    def _on_fetch_img_exception(self, _exception=None):
        self._on_fetch_img_exception_called = True
        super()._on_fetch_img_exception(_exception=_exception)

    def _fetch_img_exception_recovery(self):
        self._fetch_img_exception_recovery_called.set()
        super()._fetch_img_exception_recovery()


def test_exception_on_http_fetch_single_snapshot():
    """Exception from http image fetch should not break the pipe loop."""
    source_uri = 'http://bad.url.non.ex1st3nt'
    avsource = _TestAVSourceElement3(uri=source_uri, type='image', live=False)
    t = threading.Thread(
        name="Test AVSourceElement",
        target=avsource.start, daemon=True
        )
    t.start()
    t.join(timeout=10)
    assert not t.is_alive()
    assert avsource._run_http_fetch_called
    assert avsource._on_fetch_img_exception_called
    assert not avsource._fetch_img_exception_recovery_called.isSet()


def test_exception_on_http_fetch_continuous():
    """Exception from http image fetch should not break the pipe loop."""
    source_uri = 'http://bad.url.non.ex1st3nt'
    avsource = _TestAVSourceElement3(uri=source_uri, type='image', live=True)
    t = threading.Thread(
        name="Test AVSourceElement",
        target=avsource.start, daemon=True
        )
    t.start()
    avsource.stop()
    assert avsource._fetch_img_exception_recovery_called.wait(timeout=10)
    t.join(timeout=10)
    assert not t.is_alive()
    assert avsource._run_http_fetch_called
    assert avsource._on_fetch_img_exception_called

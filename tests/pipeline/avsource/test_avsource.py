"""Test audio/video source pipeline element."""
import pytest
from ambianic.pipeline.avsource.av_element \
    import AVSourceElement, MIN_HEALING_INTERVAL
import threading
import os
import pathlib
from ambianic.pipeline import PipeElement
from ambianic.pipeline.ai.object_detect import ObjectDetector
import logging

log = logging.getLogger()
log.setLevel(logging.DEBUG)


def test_no_config():
    with pytest.raises(AssertionError):
        AVSourceElement()


class _TestAVSourceElement(AVSourceElement):

    def __init__(self, **source_conf):
        super().__init__(**source_conf)
        self._run_gst_service_called = False
        self._stop_gst_service_called = False

    def _run_gst_service(self):
        self._run_gst_service_called = True
        pass

    def _stop_gst_service(self):
        self._stop_gst_service_called = True
        pass


class _OutPipeElement(PipeElement):

    def __init__(self, sample_callback=None):
        super().__init__()
        assert sample_callback
        self._sample_callback = sample_callback

    def receive_next_sample(self, **sample):
        self._sample_callback(**sample)
        pass


def test_no_config():
    with pytest.raises(AssertionError):
        AVSourceElement()


def test_start_stop_dummy_source():
    avsource = _TestAVSourceElement(uri='rstp://blah', type='video')
    t = threading.Thread(
        name="Test AVSourceElement",
        target=avsource.start, daemon=True
        )
    t.start()
    t.join(timeout=1)
    assert avsource._run_gst_service_called
    assert t.is_alive()
    avsource.stop()
    t.join(timeout=1)
    assert avsource._stop_gst_service_called
    assert not t.is_alive()


def test_start_stop_file_source_image_size():
    """Expect to receive an image with dimentions of the input video frame."""
    dir = os.path.dirname(os.path.abspath(__file__))
    video_file = os.path.join(
        dir,
        'test2-cam-person1.mkv'
        )
    abs_path = os.path.abspath(video_file)
    video_uri = pathlib.Path(abs_path).as_uri()
    avsource = AVSourceElement(uri=video_uri, type='video')
    sample_received = threading.Event()
    sample_image = None

    def sample_callback(image=None, inference_result=None):
        nonlocal sample_image
        nonlocal sample_received
        sample_image = image
        sample_received.set()
    output = _OutPipeElement(sample_callback=sample_callback)
    avsource.connect_to_next_element(output)
    t = threading.Thread(
        name="Test AVSourceElement",
        target=avsource.start, daemon=True
        )
    t.start()
    sample_received.wait(timeout=5)
    assert sample_image
    assert sample_image.size[0] == 1280
    assert sample_image.size[1] == 720
    assert t.is_alive()
    avsource.stop()
    t.join(timeout=20)
    assert not t.is_alive()


def _object_detect_config():
    dir = os.path.dirname(os.path.abspath(__file__))
    _good_tflite_model = os.path.join(
        dir,
        '../ai/mobilenet_ssd_v2_coco_quant_postprocess.tflite'
        )
    _good_edgetpu_model = os.path.join(
        dir,
        '../ai/mobilenet_ssd_v2_coco_quant_postprocess_edgetpu.tflite'
        )
    _good_labels = os.path.join(dir, '../ai/coco_labels.txt')
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


def test_start_stop_file_source_person_detect():
    """Expect to detect a person in the video sample."""
    dir = os.path.dirname(os.path.abspath(__file__))
    video_file = os.path.join(
        dir,
        'test2-cam-person1.mkv'
        )
    abs_path = os.path.abspath(video_file)
    video_uri = pathlib.Path(abs_path).as_uri()
    avsource = AVSourceElement(uri=video_uri, type='video')
    object_config = _object_detect_config()
    detection_received = threading.Event()
    sample_image = None
    detections = None

    def sample_callback(image=None, inference_result=None):
        nonlocal sample_image
        nonlocal detection_received
        sample_image = image
        nonlocal detections
        detections = inference_result
        print('detections: {det}'.format(det=detections))
        print('len(detections): {len}'.format(len=len(detections)))
        if detections and len(detections) > 0:
            category, confidence, _ = detections[0]
            if category == 'person' and confidence > 0.9:
                # skip video image samples until we reach a person detection
                # with high lelvel of confidence
                detection_received.set()
    object_detector = ObjectDetector(element_config=object_config)
    avsource.connect_to_next_element(object_detector)
    output = _OutPipeElement(sample_callback=sample_callback)
    object_detector.connect_to_next_element(output)
    t = threading.Thread(
        name="Test AVSourceElement",
        target=avsource.start, daemon=True
        )
    t.start()
    detection_received.wait(timeout=5)
    assert sample_image
    assert sample_image.size[0] == 1280
    assert sample_image.size[1] == 720
    assert detections
    assert len(detections) == 1
    category, confidence, (x0, y0, x1, y1) = detections[0]
    assert category == 'person'
    assert confidence > 0.9
    assert x0 > 0 and x0 < x1
    assert y0 > 0 and y0 < y1
    avsource.stop()
    t.join(timeout=10)
    assert not t.is_alive()


def test_stop_on_video_EOS():
    """Processing should stop when AVSource reaches end of input stream."""
    dir = os.path.dirname(os.path.abspath(__file__))
    video_file = os.path.join(
        dir,
        'test2-cam-person1.mkv'
        )
    abs_path = os.path.abspath(video_file)
    video_uri = pathlib.Path(abs_path).as_uri()
    avsource = AVSourceElement(uri=video_uri, type='video')
    sample_received = threading.Event()
    sample_image = None

    def sample_callback(image=None, inference_result=None):
        nonlocal sample_image
        nonlocal sample_received
        sample_image = image
        sample_received.set()
    output = _OutPipeElement(sample_callback=sample_callback)
    avsource.connect_to_next_element(output)
    t = threading.Thread(
        name="Test AVSourceElement",
        target=avsource.start, daemon=True
        )
    t.start()
    sample_received.wait(timeout=5)
    assert sample_image
    assert sample_image.size[0] == 1280
    assert sample_image.size[1] == 720
    assert t.is_alive()
    avsource._gst_process_eos_reached.wait(timeout=60)
    assert avsource._gst_process_eos_reached.is_set()
    t.join(timeout=10)
    assert not t.is_alive()


def test_still_image_input_detect_person_exit_eos():
    """Process a single jpg image. Detect a person. Exit via EOS."""
    dir = os.path.dirname(os.path.abspath(__file__))
    video_file = os.path.join(
        dir,
        '../ai/person.jpg'
        )
    abs_path = os.path.abspath(video_file)
    video_uri = pathlib.Path(abs_path).as_uri()
    avsource = AVSourceElement(uri=video_uri, type='video')
    object_config = _object_detect_config()
    detection_received = threading.Event()
    sample_image = None
    detections = None

    def sample_callback(image=None, inference_result=None):
        nonlocal sample_image
        nonlocal detection_received
        sample_image = image
        nonlocal detections
        detections = inference_result
        print('detections: {det}'.format(det=detections))
        print('len(detections): {len}'.format(len=len(detections)))
        if detections and len(detections) > 0:
            category, confidence, _ = detections[0]
            if category == 'person' and confidence > 0.9:
                # skip video image samples until we reach a person detection
                # with high lelvel of confidence
                detection_received.set()
    object_detector = ObjectDetector(element_config=object_config)
    avsource.connect_to_next_element(object_detector)
    output = _OutPipeElement(sample_callback=sample_callback)
    object_detector.connect_to_next_element(output)
    t = threading.Thread(
        name="Test AVSourceElement",
        target=avsource.start, daemon=True
        )
    t.start()
    detection_received.wait(timeout=5)
    assert sample_image
    assert sample_image.size[0] == 1280
    assert sample_image.size[1] == 720
    assert detections
    assert len(detections) == 1
    category, confidence, (x0, y0, x1, y1) = detections[0]
    assert category == 'person'
    assert confidence > 0.9
    assert x0 > 0 and x0 < x1
    assert y0 > 0 and y0 < y1
    t.join(timeout=10)
    assert avsource._gst_process_eos_reached.is_set()
    assert not t.is_alive()


def test_still_image_input_detect_person_exit_stop_signal():
    """Proces a single jpg image. Detect a person. Exit via stop signal."""
    dir = os.path.dirname(os.path.abspath(__file__))
    video_file = os.path.join(
        dir,
        '../ai/person.jpg'
        )
    abs_path = os.path.abspath(video_file)
    video_uri = pathlib.Path(abs_path).as_uri()
    avsource = AVSourceElement(uri=video_uri, type='video')
    object_config = _object_detect_config()
    detection_received = threading.Event()
    sample_image = None
    detections = None

    def sample_callback(image=None, inference_result=None):
        nonlocal sample_image
        nonlocal detection_received
        sample_image = image
        nonlocal detections
        detections = inference_result
        print('detections: {det}'.format(det=detections))
        print('len(detections): {len}'.format(len=len(detections)))
        if detections and len(detections) > 0:
            category, confidence, _ = detections[0]
            if category == 'person' and confidence > 0.9:
                # skip video image samples until we reach a person detection
                # with high lelvel of confidence
                detection_received.set()
    object_detector = ObjectDetector(element_config=object_config)
    avsource.connect_to_next_element(object_detector)
    output = _OutPipeElement(sample_callback=sample_callback)
    object_detector.connect_to_next_element(output)
    t = threading.Thread(
        name="Test AVSourceElement",
        target=avsource.start, daemon=True
        )
    t.start()
    detection_received.wait(timeout=5)
    assert sample_image
    assert sample_image.size[0] == 1280
    assert sample_image.size[1] == 720
    assert detections
    assert len(detections) == 1
    category, confidence, (x0, y0, x1, y1) = detections[0]
    assert category == 'person'
    assert confidence > 0.9
    assert x0 > 0 and x0 < x1
    assert y0 > 0 and y0 < y1
    avsource.stop()
    t.join(timeout=10)
    assert not t.is_alive()


def test_heal():
    avsource = _TestAVSourceElement(uri='rstp://blah', type='video')
    t = threading.Thread(
        name="Test AVSourceElement",
        target=avsource.start, daemon=True
        )
    t.start()
    t.join(timeout=1)
    # simulate the pipe element has been unhealthy for long enough
    avsource._latest_healing = \
        avsource._latest_healing - 2*MIN_HEALING_INTERVAL
    avsource.heal()
    # heal should have done its job and stopped the gst service for repair
    assert avsource._stop_gst_service_called
    latest = avsource._latest_healing
    avsource.heal()
    # heal should ignore back to back requests
    # latest healing timestamp should be unchanged
    assert latest == avsource._latest_healing
    # set the latest healing clock back by more than the min interval
    avsource._latest_healing = \
        avsource._latest_healing - 2*MIN_HEALING_INTERVAL
    avsource.heal()
    # now the healing process should have ran and
    # set the latest timestamp to a more recent time than the last healing run
    assert latest < avsource._latest_healing
    assert t.is_alive()
    # reset the gst stop flag to test if
    # the method will be called again by stop()
    avsource._stop_gst_service_called = False
    avsource.stop()
    t.join(timeout=1)
    assert avsource._stop_gst_service_called
    assert not t.is_alive()

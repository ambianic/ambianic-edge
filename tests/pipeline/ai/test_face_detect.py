"""Test face detection pipe element."""
import os
from ambianic.pipeline.ai.object_detect import ObjectDetector
from ambianic.pipeline.ai.face_detect import FaceDetector
from ambianic.pipeline import PipeElement
from PIL import Image


def _object_detect_config():
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
        'top_k': 3,
        'confidence_threshold': 0.82,
    }
    return config


def _face_detect_config():
    _dir = os.path.dirname(os.path.abspath(__file__))
    _good_tflite_model = os.path.join(
        _dir,
        'mobilenet_ssd_v2_face_quant_postprocess.tflite'
        )
    _good_edgetpu_model = os.path.join(
        _dir,
        'mobilenet_ssd_v2_face_quant_postprocess_edgetpu.tflite'
        )
    _good_labels = os.path.join(_dir, 'coco_labels.txt')
    config = {
        'model': {
            'tflite': _good_tflite_model,
            'edgetpu': _good_edgetpu_model,
            },
        'labels': _good_labels,
        'top_k': 2,
        'confidence_threshold': 0.6,
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
    config = _face_detect_config()
    face_detector = FaceDetector(**config)
    tfe = face_detector._tfengine
    samples = tfe.input_details[0]['shape'][0]
    assert samples == 1
    height = tfe.input_details[0]['shape'][1]
    assert height == 320
    width = tfe.input_details[0]['shape'][2]
    assert width == 320
    colors = tfe.input_details[0]['shape'][3]
    assert colors == 3


def test_model_outputs():
    """Verify against known model outputs."""
    config = _face_detect_config()
    face_detector = FaceDetector(**config)
    tfe = face_detector._tfengine
    assert tfe.output_details[0]['shape'][0] == 1
    scores = tfe.output_details[0]['shape'][1]
    assert scores == 50
    assert tfe.output_details[1]['shape'][0] == 1
    boxes = tfe.output_details[1]['shape'][1]
    assert boxes == 50
    assert tfe.output_details[2]['shape'][0] == 1
    labels = tfe.output_details[2]['shape'][1]
    assert labels == 50
    num = tfe.output_details[3]['shape'][0]
    assert num == 1


def test_no_sample():
    """Expect element to pass empty sample to next element."""
    config = _object_detect_config()
    result = 'Something'

    def sample_callback(image=None, inference_result=None, **kwargs):
        nonlocal result
        result = image is None and inference_result is None
    face_detector = FaceDetector(**config)
    output = _OutPipeElement(sample_callback=sample_callback)
    face_detector.connect_to_next_element(output)
    face_detector.receive_next_sample()
    assert result is True


def test_bad_sample_good_sample():
    """One bad sample should not prevent good samples from being processed."""
    config = _face_detect_config()
    result = 'Something'

    def sample_callback(image=None, inference_result=None, **kwargs):
        nonlocal result
        result = inference_result
    face_detector = FaceDetector(**config)
    output = _OutPipeElement(sample_callback=sample_callback)
    face_detector.connect_to_next_element(output)
    # bad sample
    face_detector.receive_next_sample(
        image=None,
        inference_result=[{'label': 'person', 'confidence': 1,
                           'box': {'xmin': -1, 'ymin': -2,
                                   'xmax': -3, 'ymax': -4}}]
        )
    # good sample
    img = _get_image(file_name='person-face.jpg')
    face_detector.receive_next_sample(
        image=img,
        inference_result=[{'label': 'person', 'confidence': 1,
                           'box': {'xmin': 0, 'ymin': 0,
                                   'xmax': 1, 'ymax': 1}}]
        )
    assert result
    assert len(result) == 1

    label = result[0]['label']
    confidence = result[0]['confidence']
    (x0, y0) = result[0]['box']['xmin'], result[0]['box']['ymin']
    (x1, y1) = result[0]['box']['xmax'], result[0]['box']['ymax']

    assert label == 'person'
    assert confidence > 0.8
    assert x0 > 0 and x0 < x1
    assert y0 > 0 and y0 < y1


def test_background_image_no_person():
    """Expect to not detect anything interesting in a background image."""
    config = _face_detect_config()
    result = None

    def sample_callback(image=None, inference_result=None, **kwargs):
        nonlocal result
        result = not image and not inference_result
    face_detector = FaceDetector(**config)
    output = _OutPipeElement(sample_callback=sample_callback)
    face_detector.connect_to_next_element(output)
    img = _get_image(file_name='background.jpg')
    face_detector.receive_next_sample(image=img)
    assert result is True


def test_one_person_high_confidence_face_low_confidence_two_stage_pipe():
    """Expect to detect a person but not a face."""
    object_config = _object_detect_config()
    face_config = _face_detect_config()
    result = None

    def sample_callback(image=None, inference_result=None, **kwargs):
        nonlocal result
        result = inference_result
    # test stage one, obect detection -> out
    object_detector = ObjectDetector(**object_config)
    output = _OutPipeElement(sample_callback=sample_callback)
    object_detector.connect_to_next_element(output)
    img = _get_image(file_name='person.jpg')
    object_detector.receive_next_sample(image=img)
    assert result
    assert len(result) == 1

    label = result[0]['label']
    confidence = result[0]['confidence']
    (x0, y0) = result[0]['box']['xmin'], result[0]['box']['ymin']
    (x1, y1) = result[0]['box']['xmax'], result[0]['box']['ymax']

    assert label == 'person'
    assert confidence > 0.9
    assert x0 > 0 and x0 < x1
    assert y0 > 0 and y0 < y1

    # test stage 2, rearrange pipe elements: object->face->out
    face_detector = FaceDetector(**face_config)
    object_detector.connect_to_next_element(face_detector)
    face_detector.connect_to_next_element(output)
    object_detector.receive_next_sample(image=img)
    assert not result


def test_thermal_one_person_face_two_stage_pipe():
    """Expect to detect a person but not a face."""
    object_config = _object_detect_config()
    face_config = _face_detect_config()
    result = None

    def sample_callback(image=None, inference_result=None, **kwargs):
        nonlocal result
        result = inference_result
    # test stage one, obect detection -> out
    object_detector = ObjectDetector(**object_config)
    output = _OutPipeElement(sample_callback=sample_callback)
    object_detector.connect_to_next_element(output)
    img = _get_image(file_name='person_thermal_bw_inverted.jpg')
    object_detector.receive_next_sample(image=img)
    assert result
    assert len(result) == 1
    label = result[0]['label']
    confidence = result[0]['confidence']
    (x0, y0) = result[0]['box']['xmin'], result[0]['box']['ymin']
    (x1, y1) = result[0]['box']['xmax'], result[0]['box']['ymax']
    assert label == 'person'
    assert confidence > 0.8
    assert x0 > 0 and x0 < x1
    assert y0 > -0.05 and y0 < y1

    # test stage 2, rearrange pipe elements: object->face->out
    face_detector = FaceDetector(**face_config)
    object_detector.connect_to_next_element(face_detector)
    face_detector.connect_to_next_element(output)
    object_detector.receive_next_sample(image=img)
    assert result
    assert len(result) == 1
    label = result[0]['label']
    confidence = result[0]['confidence']
    (x0, y0) = result[0]['box']['xmin'], result[0]['box']['ymin']
    (x1, y1) = result[0]['box']['xmax'], result[0]['box']['ymax']
    assert label == 'person'
    assert confidence > 0.8
    assert x0 > 0 and x0 < x1
    assert y0 > 0 and y0 < y1


def test_thermal_one_person_miss_face_two_stage_pipe():
    """Expect to detect a person but not a face."""
    object_config = _object_detect_config()
    face_config = _face_detect_config()
    result = None

    def sample_callback(image=None, inference_result=None, **kwargs):
        nonlocal result
        result = inference_result
    # test stage one, obect detection -> out
    object_detector = ObjectDetector(**object_config)
    output = _OutPipeElement(sample_callback=sample_callback)
    object_detector.connect_to_next_element(output)
    img = _get_image(file_name='person_thermal_bw.jpg')
    object_detector.receive_next_sample(image=img)
    assert result
    assert len(result) == 1
    label = result[0]['label']
    confidence = result[0]['confidence']
    (x0, y0) = result[0]['box']['xmin'], result[0]['box']['ymin']
    (x1, y1) = result[0]['box']['xmax'], result[0]['box']['ymax']
    assert label == 'person'
    assert confidence > 0.8
    assert x0 > 0 and x0 < x1
    assert y0 > 0 and y0 < y1

    # test stage 2, rearrange pipe elements: object->face->out
    face_detector = FaceDetector(**face_config)
    object_detector.connect_to_next_element(face_detector)
    face_detector.connect_to_next_element(output)
    object_detector.receive_next_sample(image=img)
    assert not result


def test2_one_person_high_confidence_face_low_confidence_two_stage_pipe():
    """Expect to detect a person but not a face."""
    object_config = _object_detect_config()
    face_config = _face_detect_config()
    result = None

    def sample_callback(image=None, inference_result=None, **kwargs):
        nonlocal result

        result = inference_result
    # test stage one, obect detection -> out
    object_detector = ObjectDetector(**object_config)
    output = _OutPipeElement(sample_callback=sample_callback)
    object_detector.connect_to_next_element(output)
    img = _get_image(file_name='person-face2.jpg')
    object_detector.receive_next_sample(image=img)
    assert result
    assert len(result) == 1
    label = result[0]['label']
    confidence = result[0]['confidence']
    (x0, y0) = result[0]['box']['xmin'], result[0]['box']['ymin']
    (x1, y1) = result[0]['box']['xmax'], result[0]['box']['ymax']
    assert label == 'person'
    assert confidence > 0.9
    assert x0 > 0 and x0 < x1
    assert y0 > 0 and y0 < y1

    # test stage 2, rearrange pipe elements: object->face->out
    face_detector = FaceDetector(**face_config)
    object_detector.connect_to_next_element(face_detector)
    face_detector.connect_to_next_element(output)
    object_detector.receive_next_sample(image=img)
    assert not result


def test_one_person_two_stage_pipe_high_face_confidence():
    """Detect a person in 1st stage and a face in 2nd stage."""
    object_config = _object_detect_config()
    face_config = _face_detect_config()
    result = None

    def sample_callback(image=None, inference_result=None, **kwargs):
        nonlocal result

        result = inference_result
    object_detector = ObjectDetector(**object_config)
    face_detector = FaceDetector(**face_config)
    object_detector.connect_to_next_element(face_detector)
    output = _OutPipeElement(sample_callback=sample_callback)
    face_detector.connect_to_next_element(output)
    img = _get_image(file_name='person-face.jpg')
    object_detector.receive_next_sample(image=img)
    assert result
    assert len(result) == 1
    label = result[0]['label']
    confidence = result[0]['confidence']
    (x0, y0) = result[0]['box']['xmin'], result[0]['box']['ymin']
    (x1, y1) = result[0]['box']['xmax'], result[0]['box']['ymax']
    assert label == 'person'
    assert confidence > 0.9
    assert x0 > 0 and x0 < x1
    assert y0 > 0 and y0 < y1


def test_two_person_high_confidence_one_face_high_confidence_two_stage_pipe():
    """Expect to detect two persons but only one face."""
    object_config = _object_detect_config()
    face_config = _face_detect_config()
    result = None

    def sample_callback(image=None, inference_result=None, **kwargs):
        nonlocal result

        result = inference_result
    # test stage one, obect detection -> out
    object_detector = ObjectDetector(**object_config)
    output = _OutPipeElement(sample_callback=sample_callback)
    object_detector.connect_to_next_element(output)
    img = _get_image(file_name='person2-face1.jpg')
    object_detector.receive_next_sample(image=img)
    assert result
    assert len(result) == 2
    label = result[0]['label']
    confidence = result[0]['confidence']
    (x0, y0) = result[0]['box']['xmin'], result[0]['box']['ymin']
    (x1, y1) = result[0]['box']['xmax'], result[0]['box']['ymax']
    assert label == 'person'
    assert confidence > 0.9
    assert x0 > 0 and x0 < x1
    assert y0 > 0 and y0 < y1
    label = result[1]['label']
    confidence = result[1]['confidence']
    (x0, y0) = result[1]['box']['xmin'], result[1]['box']['ymin']
    (x1, y1) = result[1]['box']['xmax'], result[1]['box']['ymax']
    assert label == 'person'
    assert confidence > 0.9
    assert x0 > 0 and x0 < x1
    assert y0 > 0 and y0 < y1

    # test stage 2, rearrange pipe elements: object->face->out
    face_detector = FaceDetector(**face_config)
    object_detector.connect_to_next_element(face_detector)
    face_detector.connect_to_next_element(output)
    object_detector.receive_next_sample(image=img)
    assert result
    assert len(result) == 1
    label = result[0]['label']
    confidence = result[0]['confidence']
    (x0, y0) = result[0]['box']['xmin'], result[0]['box']['ymin']
    (x1, y1) = result[0]['box']['xmax'], result[0]['box']['ymax']
    assert label == 'person'
    assert confidence > 0.6
    assert x0 > 0 and x0 < x1
    assert y0 > 0 and y0 < y1


def test_two_person_with_faces_no_confidence_one_stage_pipe():
    """No faces detected when the whole jpg is fed directly to face detect.
    Illustrates the point of piping models from more generic to specialized.
    The object detection model detects people and feeds a zoomed in image
    to the face detector. Instead of resizing 1280x720 to 320x320, which
    results in face detector missing faces, the piping feeds a smaller region
    of the original image where a person was detected to face detection.
    That resizes approximately a 500x400 image to 320x320, which preserves
    more feature information.
    """
    face_config = _face_detect_config()
    result = None

    def sample_callback(image=None, inference_result=None, **kwargs):
        nonlocal result
        result = inference_result
    face_detector = FaceDetector(**face_config)
    output = _OutPipeElement(sample_callback=sample_callback)
    face_detector.connect_to_next_element(output)
    img = _get_image(file_name='person2-face1.jpg')
    face_detector.receive_next_sample(
        image=img,
        inference_result=[('person', 1, [0, 0, 1, 1]), ]
        )
    assert not result


def test_one_person_face_high_confidence_one_stage_pipe():
    """Expect to detect one person face."""
    face_config = _face_detect_config()
    result = None

    def sample_callback(image=None, inference_result=None, **kwargs):
        nonlocal result

        result = inference_result
    face_detector = FaceDetector(**face_config)
    output = _OutPipeElement(sample_callback=sample_callback)
    face_detector.connect_to_next_element(output)
    img = _get_image(file_name='person-face.jpg')
    face_detector.receive_next_sample(
        image=img,
        inference_result=[{'label': 'person', 'confidence': 1,
                           'box': {'xmin': 0, 'ymin': 0,
                                   'xmax': 1, 'ymax': 1}}]
        )
    assert result
    assert len(result) == 1
    label = result[0]['label']
    confidence = result[0]['confidence']
    (x0, y0) = result[0]['box']['xmin'], result[0]['box']['ymin']
    (x1, y1) = result[0]['box']['xmax'], result[0]['box']['ymax']
    assert label == 'person'
    assert confidence > 0.8
    assert x0 > 0 and x0 < x1
    assert y0 > 0 and y0 < y1


def test_one_person_no_face_two_stage():
    """Expect to detect one person."""
    object_config = _object_detect_config()
    face_config = _face_detect_config()
    result = None

    def sample_callback(image=None, inference_result=None, **kwargs):
        nonlocal result

        result = inference_result
    object_detector = ObjectDetector(**object_config)
    face_detector = FaceDetector(**face_config)
    object_detector.connect_to_next_element(face_detector)
    output = _OutPipeElement(sample_callback=sample_callback)
    face_detector.connect_to_next_element(output)
    img = _get_image(file_name='person-no-face.jpg')
    object_detector.receive_next_sample(image=img)
    assert not result

"""Test cases for SaveDetectionEvents."""
import json
import logging
import os
import shutil
from pathlib import Path

import numpy as np
import pytest
from ambianic.configuration import get_root_config, init_config
from ambianic.pipeline.pipeline_event import PipelineContext
from ambianic.pipeline.save_event import JsonEncoder, SaveDetectionEvents
from PIL import Image

log = logging.getLogger(__name__)

inf_meta = {"display": "Test Detection"}


# test setup and teardown
# ref: https://docs.pytest.org/en/6.2.x/fixture.html#autouse-fixtures-fixtures-you-don-t-have-to-request
@pytest.fixture(autouse=True, scope="function")
def setup(request, tmp_path):
    """setup any state specific to the execution of the given module."""
    # save original env settings
    saved_amb_load = os.environ.get("AMBIANIC_CONFIG_FILES", "")
    saved_amb_dir = os.environ.get("AMBIANIC_DIR", "")
    saved_amb_config_save = os.environ.get("AMBIANIC_SAVE_CONFIG_TO", "")
    # change env settings
    save_config_path = str(Path(tmp_path / "test-config.save.yaml"))
    os.environ["AMBIANIC_CONFIG_FILES"] = (
        str(Path(request.fspath.dirname) / "test-config-no-pipelines.yaml")
        + ","
        + save_config_path
    )
    os.environ["AMBIANIC_SAVE_CONFIG_TO"] = save_config_path
    log.debug(
        f'os.environ["AMBIANIC_CONFIG_FILES"] = {os.environ["AMBIANIC_CONFIG_FILES"]}'
    )
    init_config()
    yield
    # restore env settings
    os.environ["AMBIANIC_CONFIG_FILES"] = saved_amb_load
    os.environ["AMBIANIC_SAVE_CONFIG_TO"] = saved_amb_config_save
    os.environ["AMBIANIC_DIR"] = saved_amb_dir
    init_config()


@pytest.fixture(scope="function")
def config():
    return get_root_config()


def test_json_encoder():
    inp = {
        "label": "FALL",
        "confidence": np.float32(12.3),
        "leaning_angle": np.float32(24.3),
        "keypoint_corr": {
            "left shoulder": [np.float32(1.2), np.float32(1.23)],
            "left hip": [np.float32(1.2), np.float32(1.23)],
            "right shoulder": [np.float32(1.2), np.float32(1.23)],
            "right hip": [np.float32(1.2), np.float32(1.23)],
        },
    }
    encode = json.dumps(inp, cls=JsonEncoder)
    decode = json.loads(encode)

    assert isinstance(decode["confidence"], float)
    assert isinstance(decode["leaning_angle"], float)
    assert isinstance(decode["keypoint_corr"]["left shoulder"][0], float)
    assert isinstance(decode["keypoint_corr"]["left shoulder"][1], float)


def test_json_encoder_integerData():
    inp = np.int32(10)
    encode = json.dumps(inp, cls=JsonEncoder)
    decode = json.loads(encode)

    assert isinstance(decode, int)


def test_json_encoder_arrayData():
    inp = np.array([1, 2, 3, 4, 5])
    encode = json.dumps(inp, cls=JsonEncoder)
    decode = json.loads(encode)

    assert isinstance(decode, list)


def test_process_sample_none():
    store = SaveDetectionEvents()
    processed_samples = store.process_sample(image=None, inference_result=None)
    processed_samples = list(processed_samples)
    assert len(processed_samples) == 1
    assert processed_samples[0] is None


def test_process_sample():
    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(out_dir, "tmp/")
    out_dir = os.path.abspath(out_dir)
    context = PipelineContext(unique_pipeline_name="test pipeline")
    context.data_dir = out_dir
    store = _TestSaveDetectionSamples(context=context, event_log=logging.getLogger())
    img = Image.new("RGB", (60, 30), color="red")

    detections = [
        {
            "label": "person",
            "confidence": np.float32(0.98),
            "box": {
                "xmin": np.float32(0.1),
                "ymin": np.float32(1.1),
                "xmax": np.float32(2.1),
                "ymax": np.float32(3.1),
            },
        }
    ]

    processed_samples = list(
        store.process_sample(image=img, thumbnail=img, inference_result=detections)
    )
    assert len(processed_samples) == 1
    print(processed_samples)
    img_out = processed_samples[0]["image"]
    assert img_out == img
    inf = processed_samples[0]["inference_result"]
    print(inf)

    category = inf[0]["label"]
    confidence = inf[0]["confidence"]
    (x0, y0) = inf[0]["box"]["xmin"], inf[0]["box"]["ymin"]
    (x1, y1) = inf[0]["box"]["xmax"], inf[0]["box"]["ymax"]

    assert category == "person"
    assert isinstance(confidence, np.float32)
    assert isinstance(x0, np.float32)
    assert isinstance(y0, np.float32)
    assert isinstance(x1, np.float32)
    assert isinstance(y1, np.float32)
    assert store._save_sample_called
    assert store._inf_result == detections
    assert store._img_path
    img_dir = os.path.dirname(os.path.abspath(store._img_path / "../../"))
    assert img_dir == out_dir
    out_img = Image.open(store._img_path)
    print(img_dir)
    print(store._img_path)
    assert out_img.mode == "RGB"
    assert out_img.size[0] == 60
    assert out_img.size[1] == 30
    json_dir = os.path.dirname(os.path.abspath(store._json_path / "../../"))
    assert json_dir == out_dir
    print(json_dir)
    print(store._json_path)
    with open(store._json_path) as f:
        json_inf = json.load(f)
        print(json_inf)
        img_fname = json_inf["image_file_name"]
        rel_dir = json_inf["rel_dir"]
        img_fpath = os.path.join(out_dir, rel_dir, img_fname)
        assert img_fpath == str(store._img_path)
        assert os.path.exists(img_fpath)
        json_inf_res = json_inf["inference_result"]
        assert len(json_inf_res) == 1
        json_inf_res = json_inf_res[0]
        assert json_inf_res["label"] == "person"
        assert isinstance(json_inf_res["confidence"], float)
        assert isinstance(json_inf_res["box"]["xmin"], float)
        assert isinstance(json_inf_res["box"]["ymin"], float)
        assert isinstance(json_inf_res["box"]["xmax"], float)
        assert isinstance(json_inf_res["box"]["ymax"], float)

    shutil.rmtree(out_dir)


class _TestSaveDetectionSamples(SaveDetectionEvents):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _save_sample(
        self,
        inf_time=None,
        image=None,
        thumbnail=None,
        inference_result=None,
        inference_meta=None,
    ):
        self._save_sample_called = True
        self._inf_result = inference_result
        self._img_path, self._json_path = super()._save_sample(
            inf_time=inf_time,
            image=image,
            thumbnail=thumbnail,
            inference_result=inference_result,
            inference_meta=inf_meta,
        )


def test_store_positive_detection():
    """The first time a positive sample is processed, it should be saved."""
    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(out_dir, "tmp/")
    out_dir = os.path.abspath(out_dir)
    context = PipelineContext(unique_pipeline_name="test pipeline")
    context.data_dir = out_dir
    store = _TestSaveDetectionSamples(context=context, event_log=logging.getLogger())
    img = Image.new("RGB", (60, 30), color="red")

    detections = [
        {
            "label": "person",
            "confidence": 0.98,
            "box": {"xmin": 0, "ymin": 1, "xmax": 2, "ymax": 3},
        }
    ]

    processed_samples = list(
        store.process_sample(
            image=img,
            thumbnail=img,
            inference_result=detections,
            inference_meta=inf_meta,
        )
    )
    assert len(processed_samples) == 1
    print(processed_samples)
    img_out = processed_samples[0]["image"]
    assert img_out == img
    inf = processed_samples[0]["inference_result"]
    print(inf)

    category = inf[0]["label"]
    confidence = inf[0]["confidence"]
    (x0, y0) = inf[0]["box"]["xmin"], inf[0]["box"]["ymin"]
    (x1, y1) = inf[0]["box"]["xmax"], inf[0]["box"]["ymax"]

    assert category == "person"
    assert confidence == 0.98
    assert x0 == 0 and y0 == 1 and x1 == 2 and y1 == 3
    assert store._save_sample_called
    assert store._inf_result == detections
    assert store._img_path
    img_dir = os.path.dirname(os.path.abspath(store._img_path / "../../"))
    assert img_dir == out_dir
    out_img = Image.open(store._img_path)
    print(img_dir)
    print(store._img_path)
    assert out_img.mode == "RGB"
    assert out_img.size[0] == 60
    assert out_img.size[1] == 30
    json_dir = os.path.dirname(os.path.abspath(store._json_path / "../../"))
    assert json_dir == out_dir
    print(json_dir)
    print(store._json_path)
    with open(store._json_path) as f:
        json_inf = json.load(f)
        print(json_inf)
        img_fname = json_inf["image_file_name"]
        rel_dir = json_inf["rel_dir"]
        img_fpath = os.path.join(out_dir, rel_dir, img_fname)
        assert img_fpath == str(store._img_path)
        assert os.path.exists(img_fpath)
        json_inf_res = json_inf["inference_result"]
        assert len(json_inf_res) == 1
        json_inf_res = json_inf_res[0]
        assert json_inf_res["label"] == "person"
        assert json_inf_res["confidence"] == 0.98
        assert json_inf_res["box"]["xmin"] == 0
        assert json_inf_res["box"]["ymin"] == 1
        assert json_inf_res["box"]["xmax"] == 2
        assert json_inf_res["box"]["ymax"] == 3

    shutil.rmtree(out_dir)


def test_store_negative_detection():
    """The first time a negative sample is processed, it should be saved."""
    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(out_dir, "tmp/")
    out_dir = os.path.abspath(out_dir)
    out_dir = os.path.abspath(out_dir)
    context = PipelineContext(unique_pipeline_name="test pipeline")
    context.data_dir = out_dir
    store = _TestSaveDetectionSamples(context=context, event_log=logging.getLogger())
    img = Image.new("RGB", (60, 30), color="red")
    detections = []
    processed_samples = list(
        store.process_sample(
            image=img,
            thumbnail=img,
            inference_result=detections,
            inference_meta=inf_meta,
        )
    )
    assert len(processed_samples) == 1
    print(processed_samples)
    img_out = processed_samples[0]["image"]
    assert img_out == img
    inf = processed_samples[0]["inference_result"]
    print(inf)
    assert not inf
    assert store._save_sample_called
    assert store._inf_result == detections
    assert store._img_path
    img_dir = os.path.dirname(os.path.abspath(store._img_path / "../../"))
    assert img_dir == out_dir
    out_img = Image.open(store._img_path)
    print(img_dir)
    print(store._img_path)
    assert out_img.mode == "RGB"
    assert out_img.size[0] == 60
    assert out_img.size[1] == 30
    json_dir = os.path.dirname(os.path.abspath(store._json_path / "../../"))
    assert json_dir == out_dir
    print(json_dir)
    print(store._json_path)
    with open(store._json_path) as f:
        json_inf = json.load(f)
        print(json_inf)
        img_fname = json_inf["image_file_name"]
        rel_dir = json_inf["rel_dir"]
        img_fpath = os.path.join(out_dir, rel_dir, img_fname)
        assert img_fpath == str(store._img_path)
        assert os.path.exists(img_fpath)
        json_inf_res = json_inf["inference_result"]
        assert not json_inf_res

    shutil.rmtree(out_dir)


def test_store_negative_detection_no_inference():
    """
    Expect store to save the image from an inference without any detection.
    """
    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(out_dir, "tmp/")
    out_dir = os.path.abspath(out_dir)
    out_dir = os.path.abspath(out_dir)
    context = PipelineContext(unique_pipeline_name="test pipeline")
    context.data_dir = out_dir
    store = _TestSaveDetectionSamples(context=context, event_log=logging.getLogger())
    img = Image.new("RGB", (60, 30), color="red")
    detections = None
    processed_samples = list(
        store.process_sample(
            image=img,
            thumbnail=img,
            inference_result=detections,
            inference_meta=inf_meta,
        )
    )
    assert len(processed_samples) == 1
    print(processed_samples)
    img_out = processed_samples[0]["image"]
    assert img_out == img
    inf = processed_samples[0]["inference_result"]
    print(inf)
    assert not inf
    assert store._save_sample_called
    assert store._inf_result == detections
    assert store._img_path
    img_dir = os.path.dirname(os.path.abspath(store._img_path / "../../"))
    assert img_dir == out_dir
    out_img = Image.open(store._img_path)
    print(img_dir)
    print(store._img_path)
    assert out_img.mode == "RGB"
    assert out_img.size[0] == 60
    assert out_img.size[1] == 30
    json_dir = os.path.dirname(os.path.abspath(store._json_path / "../../"))
    assert json_dir == out_dir
    print(json_dir)
    print(store._json_path)
    with open(store._json_path) as f:
        json_inf = json.load(f)
        print(json_inf)
        img_fname = json_inf["image_file_name"]
        rel_dir = json_inf["rel_dir"]
        img_fpath = os.path.join(out_dir, rel_dir, img_fname)
        assert img_fpath == str(store._img_path)
        assert os.path.exists(img_fpath)
        json_inf_res = json_inf["inference_result"]
        assert not json_inf_res

    shutil.rmtree(out_dir)


class _TestSaveDetectionSamples2(SaveDetectionEvents):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        result = {
            "id": "140343867415240",
            "datetime": "2021-05-05 14:04:45.428473",
            "inference_result": [
                {
                    "confidence": 0.98828125,
                    "datetime": "2021-05-05 14:04:45.428473",
                    "label": "cat",
                    "id": "140343867415240",
                }
            ],
            "inference_meta": {"display": "Test Object Detection"},
        }
        context = PipelineContext(unique_pipeline_name="test pipeline")
        context.data_dir = "./tmp/"
        store = _TestSaveDetectionSamples(
            context=context, event_log=logging.getLogger()
        )
        data = {"message": "Test Event", "priority": "INFO", "args": result}
        store.notify(event_data=data)

    def _save_sample(
        self,
        inf_time=None,
        image=None,
        thumbnail=None,
        inference_result=None,
        inference_meta=None,
    ):
        self._save_sample_called = True


def test_process_sample_exception():
    """Exception during processing should not prevent passing the sample on."""
    context = PipelineContext(unique_pipeline_name="test pipeline")
    context.data_dir = "./tmp/"
    store = _TestSaveDetectionSamples2(context=context, event_log=logging.getLogger())
    img = Image.new("RGB", (60, 30), color="red")

    detections = [
        {
            "label": "person",
            "confidence": 0.98,
            "box": {"xmin": 0, "ymin": 1, "xmax": 2, "ymax": 3},
        }
    ]

    processed_samples = list(
        store.process_sample(
            image=img, inference_result=detections, inference_meta=inf_meta
        )
    )
    assert store._save_sample_called
    assert len(processed_samples) == 1
    print(processed_samples)
    img_out = processed_samples[0]["image"]
    assert img_out == img
    inf = processed_samples[0]["inference_result"]
    print(inf)

    category = inf[0]["label"]
    confidence = inf[0]["confidence"]
    (x0, y0) = inf[0]["box"]["xmin"], inf[0]["box"]["ymin"]
    (x1, y1) = inf[0]["box"]["xmax"], inf[0]["box"]["ymax"]

    assert category == "person"
    assert confidence == 0.98
    assert x0 == 0 and y0 == 1 and x1 == 2 and y1 == 3
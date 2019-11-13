"""Test cases for SaveDetectionSamples."""

from ambianic.pipeline.store import SaveDetectionSamples
from PIL import Image
import os
import json
import logging
from ambianic.pipeline.timeline import PipelineContext


def test_process_sample_none():
    store = SaveDetectionSamples()
    processed_samples = store.process_sample(
        image=None,
        inference_result=None)
    processed_samples = list(processed_samples)
    assert len(processed_samples) == 1
    assert processed_samples[0] is None


class _TestSaveDetectionSamples(SaveDetectionSamples):

    _save_sample_called = False
    _img_path = None
    _json_path = None
    _inf_result = None

    def _save_sample(self,
                     inf_time=None,
                     image=None,
                     thumbnail=None,
                     inference_result=None,
                     inference_meta=None):
        self._save_sample_called = True
        self._inf_result = inference_result
        self._img_path, self._json_path = \
            super()._save_sample(inf_time=inf_time,
                                 image=image,
                                 thumbnail=thumbnail,
                                 inference_result=inference_result,
                                 inference_meta=inference_meta)


def test_store_positive_detection():
    """The first time a positive sample is processed, it should be saved."""
    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(
        out_dir,
        'tmp/'
        )
    out_dir = os.path.abspath(out_dir)
    context = PipelineContext(unique_pipeline_name='test pipeline')
    context.data_dir = out_dir
    store = _TestSaveDetectionSamples(context=context,
                                      event_log=logging.getLogger())
    img = Image.new('RGB', (60, 30), color='red')
    detections = [
            ('person', 0.98, (0, 1, 2, 3))
    ]
    processed_samples = list(store.process_sample(image=img,
                                                  thumbnail=img,
                                                  inference_result=detections))
    assert len(processed_samples) == 1
    print(processed_samples)
    img_out = processed_samples[0]['image']
    assert img_out == img
    inf = processed_samples[0]['inference_result']
    print(inf)
    category, confidence, box = inf[0]
    assert category == 'person'
    assert confidence == 0.98
    assert box[0] == 0 and box[1] == 1 and box[2] == 2 and box[3] == 3
    assert store._save_sample_called
    assert store._inf_result == detections
    assert store._img_path
    img_dir = os.path.dirname(os.path.abspath(store._img_path / "../../"))
    assert img_dir == out_dir
    out_img = Image.open(store._img_path)
    print(img_dir)
    print(store._img_path)
    assert out_img.mode == 'RGB'
    assert out_img.size[0] == 60
    assert out_img.size[1] == 30
    json_dir = os.path.dirname(os.path.abspath(store._json_path / "../../"))
    assert json_dir == out_dir
    print(json_dir)
    print(store._json_path)
    with open(store._json_path) as f:
        json_inf = json.load(f)
        print(json_inf)
        img_fname = json_inf['image_file_name']
        rel_dir = json_inf['rel_dir']
        img_fpath = os.path.join(out_dir, rel_dir, img_fname)
        assert img_fpath == str(store._img_path)
        json_inf_res = json_inf['inference_result']
        assert len(json_inf_res) == 1
        json_inf_res = json_inf_res[0]
        assert json_inf_res['label'] == 'person'
        assert json_inf_res['confidence'] == 0.98
        assert json_inf_res['box']['xmin'] == 0
        assert json_inf_res['box']['ymin'] == 1
        assert json_inf_res['box']['xmax'] == 2
        assert json_inf_res['box']['ymax'] == 3


def test_store_negative_detection():
    """The first time a negative sample is processed, it should be saved."""
    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(
        out_dir,
        'tmp/'
        )
    out_dir = os.path.abspath(out_dir)
    out_dir = os.path.abspath(out_dir)
    context = PipelineContext(unique_pipeline_name='test pipeline')
    context.data_dir = out_dir
    store = _TestSaveDetectionSamples(context=context,
                                      event_log=logging.getLogger())
    img = Image.new('RGB', (60, 30), color='red')
    detections = []
    processed_samples = list(store.process_sample(image=img,
                                                  thumbnail=img,
                                                  inference_result=detections))
    assert len(processed_samples) == 1
    print(processed_samples)
    img_out = processed_samples[0]['image']
    assert img_out == img
    inf = processed_samples[0]['inference_result']
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
    assert out_img.mode == 'RGB'
    assert out_img.size[0] == 60
    assert out_img.size[1] == 30
    json_dir = os.path.dirname(os.path.abspath(store._json_path / "../../"))
    assert json_dir == out_dir
    print(json_dir)
    print(store._json_path)
    with open(store._json_path) as f:
        json_inf = json.load(f)
        print(json_inf)
        img_fname = json_inf['image_file_name']
        rel_dir = json_inf['rel_dir']
        img_fpath = os.path.join(out_dir, rel_dir, img_fname)
        assert img_fpath == str(store._img_path)
        json_inf_res = json_inf['inference_result']
        assert not json_inf_res


class _TestSaveDetectionSamples2(SaveDetectionSamples):

    _save_sample_called = False

    def _save_sample(self,
                     inf_time=None,
                     image=None,
                     thumbnail=None,
                     inference_result=None,
                     inference_meta=None):
        self._save_sample_called = True
        raise RuntimeError()


def test_process_sample_exception():
    """Exception during processing should not prevent passing the sample on."""
    context = PipelineContext(unique_pipeline_name='test pipeline')
    context.data_dir = "./tmp/"
    store = _TestSaveDetectionSamples2(context=context,
                                       event_log=logging.getLogger())
    img = Image.new('RGB', (60, 30), color='red')
    detections = [
            ('person', 0.98, (0, 1, 2, 3))
    ]
    processed_samples = list(store.process_sample(image=img,
                                                  inference_result=detections,
                                                  inference_meta=None))
    assert store._save_sample_called
    assert len(processed_samples) == 1
    print(processed_samples)
    img_out = processed_samples[0]['image']
    assert img_out == img
    inf = processed_samples[0]['inference_result']
    print(inf)
    category, confidence, box = inf[0]
    assert category == 'person'
    assert confidence == 0.98
    assert box[0] == 0 and box[1] == 1 and box[2] == 2 and box[3] == 3

"""Test cases for SaveDetectionSamples."""

from ambianic.pipeline.store import SaveDetectionSamples
from PIL import Image


def test_proess_sample_none():
    store = SaveDetectionSamples()
    processed_samples = store.process_sample(
        image=None,
        inference_result=None)
    processed_samples = list(processed_samples)
    assert len(processed_samples) == 1
    assert processed_samples[0] is None


def test_store_positive_detection():
    """The first time a positive sample is processed, it should be saved."""
    store = SaveDetectionSamples(output_directory="./tmp/")
    img = Image.new('RGB', (60, 30), color='red')
    detections = [
            ('person', 0.98, (0, 1, 2, 3))
    ]
    processed_samples = list(store.process_sample(image=img,
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


def test_store_negative_detection():
    """The first time a negative sample is processed, it should be saved."""
    store = SaveDetectionSamples(output_directory="./tmp/")
    img = Image.new('RGB', (60, 30), color='red')
    detections = []
    processed_samples = list(store.process_sample(image=img,
                                                  inference_result=detections))
    assert len(processed_samples) == 1
    print(processed_samples)
    img_out = processed_samples[0]['image']
    assert img_out == img
    inf = processed_samples[0]['inference_result']
    print(inf)
    assert not inf


class _TestSaveDetectionSamples(SaveDetectionSamples):

    def _save_sample(self):
        raise RuntimeError()


def test_process_sample_exception():
    """Exception during processing should not prevent passing the sample on."""
    store = _TestSaveDetectionSamples(output_directory="./tmp/")
    img = Image.new('RGB', (60, 30), color='red')
    detections = [
            ('person', 0.98, (0, 1, 2, 3))
    ]
    processed_samples = list(store.process_sample(image=img,
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

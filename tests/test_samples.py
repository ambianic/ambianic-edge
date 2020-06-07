# logs size is 24 records long, splitted in 3 files of 8 events each

import pytest
import os
from ambianic.webapp.server import samples
import logging

log = logging.getLogger(__name__)

sample_id = "test_id"
sample = {
        'file': '20190913-063945-json.txt',
        'id': sample_id,
        "datetime": "2019-09-13T16:32:34.704797",
        "image": "20190913-163234-image.jpg",
        "inference_result": [{
            "category": "person",
            "confidence": 0.98046875,
            "box": {
                "xmin": 0.5251423732654468,
                "ymin": 0.0021262094378471375,
                "xmax": 0.9498447340887946,
                "ymax": 0.23079824447631836
            }
        }]
    }


def test_add_sample():
    assert not samples.add_sample(sample)


def test_update_sample():
    samples.add_sample(sample)
    assert samples.update_sample(sample)


def test_delete_sample():
    samples.add_sample(sample)
    assert samples.delete_sample(sample["id"])

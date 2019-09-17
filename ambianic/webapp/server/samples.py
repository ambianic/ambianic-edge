"""Restful services related to pipeline samples."""
import logging
import uuid
import datetime
from pathlib import Path
import os
import json

log = logging.getLogger()

SAMPLES = [
    {
        'file': '20190913-063945-json.txt',
        'id': '2a34987234324324',
        "datetime": "2019-09-13T16:32:34.704797",
        "image": "20190913-163234-image.jpg",
        "inference_result": [
            {
                "category": "person",
                "confidence": 0.98046875,
                "box": {
                    "xmin": 0.5251423732654468,
                    "ymin": 0.0021262094378471375,
                    "xmax": 0.9498447340887946,
                    "ymax": 0.23079824447631836
                }
            }
            ]
    },
    {
        'file': '20190913-064945-json.txt',
        'id': '3ea34987234345424',
        "datetime": "2019-09-15T06:38:30.019847",
        "image": "20190915-063830-image.jpg",
        "inference_result": []
    },
    {
        'file': '20190913-064945-json.txt',
        'id': '2c349bb74234324324',
        "datetime": "2019-09-12T15:20:47.550151",
        "image": "20190912-152047-image.jpg",
        "inference_result": [
            {
                "category": "person",
                "confidence": 0.9921875,
                "box": {
                    "xmin": 0.349978506565094,
                    "ymin": 0.09689526346356389,
                    "xmax": 0.5911635756492615,
                    "ymax": 0.40339951629117893
                }
            }
        ]
    },
]


def get_samples(before_datetime=None, max_count=10):
    """Get stored pipeline samples.

    Parameters
    ----------
    before_datetime : date time in ISO 8601 compatible format,
        YYYY-MM-DDTHH:MM:SS. For example '2002-12-25 00:00:00-06:39'.
        It uses python's standard function datetime.fromisoformat().
        If not provided, the function will start with the most recent available
        sample.
    max_count : positive integer
        Maximum number of samples returned. Defaults to 10.

    Returns
    -------
    dictionary
        Returns a dictionary of previously saved pipeline samples.

    """
    parsed_datetime = None
    if before_datetime:
        try:
            parsed_datetime = datetime.fromisoformat(before_datetime)
            log.debug('Fetching %d samples before %s', max_count,
                      parsed_datetime)
        except ValueError as e:
            log.warning('Unable to parse before_datetime parameter: %s. '
                        ' Error: %s', before_datetime, str(e))
    if not parsed_datetime:
        log.debug('Fetching %d most recent samples.', max_count)
    p = Path('./data/faces/')
    log.debug('Samples path: %s', p.resolve())
    files = list(p.glob("*-json.txt"))
    log.debug('Fetched %d file names.', len(files))
    files = sorted(files, key=os.path.getmtime, reverse=True)
    samples = []
    for json_file in files:
        with open(json_file) as f:
            sample = json.load(f)
            sample['id'] = uuid.uuid4().hex
            sample['file'] = str(json_file)
            samples.append(sample)
    # lines = map(str, files)
    # log.debug('File names follow:\n %s', "\n".join(lines))
    return samples


def add_sample(new_sample=None):
    assert new_sample
    log.debug('add_sample new_sample 0 %s', new_sample)
    new_sample['id'] = uuid.uuid4().hex
    log.debug('add_sample 1 %s', new_sample)
    SAMPLES.append(new_sample)


def update_sample(edited_sample=None):
    assert edited_sample
    for i, old_sample in enumerate(SAMPLES):
        old_sample = SAMPLES[i]
        if old_sample['id'] == edited_sample['id']:
            SAMPLES[i] = edited_sample
            return True
    log.debug('sample not found %s', edited_sample)
    return False


def delete_sample(sample_id):
    for sample in SAMPLES:
        if sample['id'] == sample_id:
            SAMPLES.remove(sample)
            log.debug('sample deleted %s', sample)
            return True
    log.debug('sample not found %s', sample)
    return False

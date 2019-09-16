"""Restful services related to pipeline samples."""
import logging
import uuid
import datetime
from pathlib import Path
import os

log = logging.getLogger(__name__)

SAMPLES = [
    {
        'id': uuid.uuid4().hex,
        'title': 'On the Road',
        'author': 'Jack Kerouac',
        'read': True
    },
    {
        'id': uuid.uuid4().hex,
        'title': 'Harry Potter and the Philosopher\'s Stone',
        'author': 'J. K. Rowling',
        'read': False
    },
    {
        'id': uuid.uuid4().hex,
        'title': 'Green Eggs and Ham',
        'author': 'Dr. Seuss',
        'read': True
    }
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
    lines = map(str, files)
    log.debug('File names follow:\n %s', "\n".join(lines))
    return SAMPLES


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

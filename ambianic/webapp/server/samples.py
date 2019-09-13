"""Restful services related to pipeline samples."""
import logging

log = logging.getLogger(__name__)

SAMPLES = [
    {
        'title': 'On the Road',
        'author': 'Jack Kerouac',
        'read': True
    },
    {
        'title': 'Harry Potter and the Philosopher\'s Stone',
        'author': 'J. K. Rowling',
        'read': False
    },
    {
        'title': 'Green Eggs and Ham',
        'author': 'Dr. Seuss',
        'read': True
    }
]


def get_samples():
    """Return a dictionary of pipeline samples."""
    log.debug('returning SAMPLES')
    return SAMPLES

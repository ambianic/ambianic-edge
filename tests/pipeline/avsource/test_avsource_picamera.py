"""Test audio/video source pipeline element."""
import pytest
from ambianic.pipeline.avsource.av_element import picam
import logging
from io import BytesIO
import time
import os
from PIL import Image

log = logging.getLogger()
log.setLevel(logging.DEBUG)

class _TestPiCamera():

    def __init__(self):

        _dir = os.path.dirname(os.path.abspath(__file__))
        self.img_path = os.path.join(
            _dir,
            '../ai/person.jpg'
        )

        self.led = False
    
    def start_preview(self):
        pass

    def capture(self, stream, format):
        img = Image.open(self.img_path, mode='r')
        img.save(stream, format=format)

    def close(self): 
        pass


class picamera_override():
    PiCamera = _TestPiCamera

def test_fail_import():
    picam.picamera_override = None
    cam = picam.Picamera()
    assert cam.has_failure()

def test_acquire():
    picam.picamera_override = picamera_override
    cam = picam.Picamera()
    assert not cam.has_failure()
    raw = cam.acquire()
    assert raw is not None
    cam.stop()

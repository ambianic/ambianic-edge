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

    def __init__(self, fail_read=False):

        _dir = os.path.dirname(os.path.abspath(__file__))
        self.img_path = os.path.join(
            _dir,
            '../ai/person.jpg'
        )
        self.read = 0
        self.fail_read = fail_read
        self.led = False
    
    def start_preview(self):
        pass

    def capture(self, stream, format):
        if self.fail_read and (self.read > 0 and self.read % 2 == 0):
            raise Exception("Read failed")
        img = Image.open(self.img_path, mode='r')
        img.save(stream, format=format)
        self.read += 1

    def close(self): 
        pass


class _TestPiCameraFailure(_TestPiCamera):
    def __init__(self):
        super().__init__(fail_read=True)

class picamera_override():
    PiCamera = _TestPiCamera

class picamera_override_failure():
    PiCamera = _TestPiCameraFailure

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

def test_acquire_failure():
    picam.picamera_override = picamera_override_failure
    cam = picam.Picamera()
    assert not cam.has_failure()
    failed = False
    try:
        cam.acquire()
        cam.acquire()
        cam.acquire()
    except Exception:
        failed = True
        pass
    assert failed
    cam.stop()

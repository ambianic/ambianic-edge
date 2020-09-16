import logging
from io import BytesIO
import time
from PIL import Image

log = logging.getLogger(__name__)

picamera_override = None

class Picamera():

    def __init__(self, image_format='jpeg'):

        self.error = None
        self.format = image_format

        if picamera_override is None:

            try:
                import picamera
                self.camera = picamera.PiCamera()
            except ImportError as err:
                log.warn("Failed to import picamera module: %s" % err)
                self.error = err
                return
            except Exception as err:
                log.warn("Error importing picamera module: %s" % err)
                self.error = err
                return
        else:
            self.camera = picamera_override.PiCamera()

        self.stream = BytesIO()
        self.camera.led = True
        # note: setup or expose properties (ISO shutter awb)
        time.sleep(2)

    def has_failure(self):
        return self.error is not None

    def acquire(self):
        if self.has_failure():
            return None
        self.camera.capture(self.stream, format=self.format)
        self.stream.seek(0)
        return Image.open(self.stream)

    def stop(self):
        if self.stream is not None:
            self.stream.close()
        if self.camera is not None:
            self.camera.led = False
            self.camera.close()

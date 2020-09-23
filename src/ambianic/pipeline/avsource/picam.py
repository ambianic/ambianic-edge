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
        self.stream = BytesIO()
        # test picamera import works
        self._get_camera()

    def has_failure(self):
        return self.error is not None

    def _get_camera(self):
        if picamera_override is None:
            try:
                import picamera
                return picamera.PiCamera()
            except Exception as err:
                log.warning("Error importing picamera module: %s" % err)
                self.error = err
                return None
        else:
            return picamera_override.PiCamera()

    def acquire(self):
        with self._get_camera() as camera:
            self.stream.truncate()
            self.stream.seek(0)
            camera.capture(self.stream, format=self.format)
            return Image.open(self.stream)

    def stop(self):
        if self.stream is not None:
            self.stream.close()

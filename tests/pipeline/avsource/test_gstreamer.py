"""Test GStreamer Service."""
from ambianic.pipeline.avsource.gst_process import GstService
import threading
import os
import time
import pathlib
from queue import Queue
import logging
from PIL import Image

log = logging.getLogger()
log.setLevel(logging.DEBUG)


class _TestGstService(GstService):

    def __init__(self):
        self._source_shape = self.ImageShape()


class _TestSourceCaps:

    def get_structure(self, index=None):
        assert index == 0
        struct = {
            'width': 200,
            'height': 100,
        }
        return struct


def test_on_auto_plugin():
    gst = _TestGstService()
    gst.on_autoplug_continue(None, None, _TestSourceCaps())
    assert gst._source_shape.width == 200
    assert gst._source_shape.height == 100


class _TestGstService2(GstService):

    def _register_sys_signal_handler(self):
        print('skipping sys handler registration')
        # system handlers can be only registered in
        # the main process thread
        pass


def _test_start_gst_service2(source_conf=None,
                             out_queue=None,
                             stop_signal=None,
                             eos_reached=None):
    print('_test_start_gst_service2 starting _TestGstService2')
    try:
        svc = _TestGstService2(source_conf=source_conf,
                               out_queue=out_queue,
                               stop_signal=stop_signal,
                               eos_reached=eos_reached)
    except Exception as e:
        print('Exception caught while starting _TestGstService2: %r'
              % e)
    else:
        svc.run()
    print('_test_start_gst_service2: Exiting GST thread')


def test_image_source_one_sample():
    """An jpg image source should produce one sample."""
    dir = os.path.dirname(os.path.abspath(__file__))
    source_file = os.path.join(
        dir,
        '../ai/person.jpg'
        )
    abs_path = os.path.abspath(source_file)
    source_uri = pathlib.Path(abs_path).as_uri()
    _gst_out_queue = Queue(10)
    _gst_stop_signal = threading.Event()
    _gst_eos_reached = threading.Event()
    _gst_thread = threading.Thread(
        target=_test_start_gst_service2,
        name='Gstreamer Service Process',
        daemon=True,
        kwargs={'source_conf': {'uri': source_uri, 'type': 'image'},
                'out_queue': _gst_out_queue,
                'stop_signal': _gst_stop_signal,
                'eos_reached': _gst_eos_reached,
                }
        )
    _gst_thread.daemon = True
    _gst_thread.start()
    print('Gst service started. Waiting for a sample.')
    sample_img = _gst_out_queue.get(timeout=5)
    print('sample: %r' % (sample_img.keys()))
    assert sample_img
    type = sample_img['type']
    # only image type supported at this time
    assert type == 'image'
    # make sure the sample is in RGB format
    format = sample_img['format']
    assert format == 'RGB'
    width = sample_img['width']
    assert width == 1280
    height = sample_img['height']
    assert height == 720
    bytes = sample_img['bytes']
    img = Image.frombytes(format, (width, height),
                          bytes, 'raw')
    assert img
    _gst_stop_signal.set()
    _gst_thread.join(timeout=30)
    assert not _gst_thread.is_alive()

"""Test cases for SaveDetectionEvents."""

import json
import logging
import os
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Event, Thread

import httpretty
from ambianic import config
from ambianic.notification import sendCloudNotification
from ambianic.pipeline.pipeline_event import PipelineContext
from ambianic.pipeline.store import SaveDetectionEvents
from PIL import Image

log = logging.getLogger(__name__)


class MockRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, event, *args):
        self.event: Event = event
        BaseHTTPRequestHandler.__init__(self, *args)

    def do_POST(self):
        # read the message and convert it into a python dictionary
        length = int(self.headers.get("content-length"))
        message = json.loads(self.rfile.read(length))

        assert message.get("title") is not None

        self.send_response(200)
        self.end_headers()

        self.event.set()


def get_free_port():
    s = socket.socket(socket.AF_INET, type=socket.SOCK_STREAM)
    s.bind(("localhost", 0))
    _, port = s.getsockname()
    s.close()
    return port


class HTTPMockServer:
    def __init__(self, ev):
        def handler(*args):
            MockRequestHandler(ev, *args)

        self.port = get_free_port()
        self.mock_server = HTTPServer(("localhost", self.port), handler)
        self.thread = Thread(target=self.mock_server.serve_forever)
        self.thread.start()

    def stop(self):
        self.mock_server.shutdown()
        self.thread.join()


class _TestSaveDetectionSamples(SaveDetectionEvents):
    _save_sample_called = False
    _img_path = None
    _json_path = None
    _inf_result = None

    def _save_sample(
        self,
        inf_time=None,
        image=None,
        thumbnail=None,
        inference_result=None,
        inference_meta=None,
    ):
        self._save_sample_called = True
        self._inf_result = inference_result
        self._img_path, self._json_path = super()._save_sample(
            inf_time=inf_time,
            image=image,
            thumbnail=thumbnail,
            inference_result=inference_result,
            inference_meta=inference_meta,
        )

    data = {
        "confidence": 0.98828125,
        "datetime": "2021-05-05 14:04:45.428473",
        "label": "cat",
        "id": "140343867415240",
    }

    httpretty.register_uri(
        httpretty.POST,
        "http://localhost:5050/.netlify/functions/notification",
        status=200,
    )

    sendCloudNotification(data=data)


def test_notification_with_attachments():
    """Ensure a positive detection is notified"""
    called: Event = Event()
    mock_server = HTTPMockServer(called)

    # register the mock server endpoint
    config.update(
        {
            "notifications": {
                "test": {
                    "include_attachments": True,
                    "providers": ["json://localhost:%s/webhook" % (mock_server.port)],
                }
            }
        }
    )

    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(out_dir, "tmp/")
    out_dir = os.path.abspath(out_dir)
    context = PipelineContext(unique_pipeline_name="test pipeline notify")
    context.data_dir = out_dir
    notify = {"providers": ["test"]}
    store = _TestSaveDetectionSamples(
        context=context,
        event_log=logging.getLogger(),
        notify=notify,
    )
    img = Image.new("RGB", (60, 30), color="red")

    detections = [
        {
            "label": "person",
            "confidence": 0.98,
            "box": {"xmin": 0, "ymin": 1, "xmax": 2, "ymax": 3},
        }
    ]

    processed_samples = list(
        store.process_sample(image=img, thumbnail=img, inference_result=detections)
    )
    assert len(processed_samples) == 1
    mock_server.stop()
    assert called.is_set()


def test_notification_without_attachments():
    """Ensure a positive detection is notified"""
    called: Event = Event()
    mock_server = HTTPMockServer(called)

    # register the mock server endpoint
    config.update(
        {
            "notifications": {
                "test": {
                    "include_attachments": False,
                    "providers": [],
                }
            }
        }
    )

    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(out_dir, "tmp/")
    out_dir = os.path.abspath(out_dir)
    context = PipelineContext(unique_pipeline_name="test pipeline notify")
    context.data_dir = out_dir
    notify = {"providers": ["test"]}
    store = _TestSaveDetectionSamples(
        context=context,
        event_log=logging.getLogger(),
        notify=notify,
    )
    img = Image.new("RGB", (60, 30), color="red")

    detections = [
        {
            "label": "person",
            "confidence": 0.98,
            "box": {"xmin": 0, "ymin": 1, "xmax": 2, "ymax": 3},
        }
    ]

    processed_samples = list(
        store.process_sample(image=img, thumbnail=img, inference_result=detections)
    )
    assert len(processed_samples) == 1
    mock_server.stop()


def test_plain_notification():
    """Ensure a positive detection is notified"""
    called: Event = Event()
    mock_server = HTTPMockServer(called)

    # register the mock server endpoint
    config.update(
        {
            "notifications": {
                "test": {
                    "include_attachments": True,
                    "providers": ["json://localhost:%s/webhook" % (mock_server.port)],
                }
            }
        }
    )

    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(out_dir, "tmp/")
    out_dir = os.path.abspath(out_dir)
    context = PipelineContext(unique_pipeline_name="test pipeline notify")
    context.data_dir = out_dir
    notify = {"providers": ["test"]}
    store = _TestSaveDetectionSamples(
        context=context,
        event_log=logging.getLogger(),
        notify=notify,
    )
    img = Image.new("RGB", (60, 30), color="red")

    detections = [
        {
            "label": "person",
            "confidence": 0.98,
            "box": {"xmin": 0, "ymin": 1, "xmax": 2, "ymax": 3},
        }
    ]

    processed_samples = list(
        store.process_sample(image=img, thumbnail=img, inference_result=detections)
    )
    assert len(processed_samples) == 1
    mock_server.stop()
    assert called.is_set()

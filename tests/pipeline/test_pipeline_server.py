"""More test cases for ambianic.interpreter module."""
from ambianic import pipeline
from ambianic.config_mgm import Config, ConfigChangedEvent
from ambianic import config_manager
from ambianic.pipeline import interpreter
from ambianic.pipeline.avsource.av_element import AVSourceElement
from ambianic.pipeline.interpreter import \
    PipelineServer, Pipeline, HealingThread, PipelineServerJob
import logging
import time
import threading
import os


log = logging.getLogger()
log.setLevel(logging.DEBUG)

def test_pipeline_server_start_stop():


    _dir = os.path.dirname(os.path.abspath(__file__))

    config_manager.set(Config({
        "sources": {
            "test": {
                "uri": os.path.join(
                    _dir,
                    "./avsource/test2-cam-person1.mkv"
                )
            }
        },
        "pipelines": {
            "test": [
                { "source": "test" }
            ]
        }
    }))

    srv = PipelineServer(config_manager.get_pipelines())
    srv.start()
    srv.stop()


class PipelineServerEv(PipelineServer):

    def __init__(self, config):
        super().__init__(config)
        self.triggered = False

    def trigger_event(self, event: ConfigChangedEvent):
        log.debug("trigger restart")
        super().trigger_event(event)
        self.triggered = True


def test_pipeline_server_config_change():


    _dir = os.path.dirname(os.path.abspath(__file__))

    source_cfg = {
        "uri": os.path.join(
            _dir,
            "./avsource/test2-cam-person1.mkv"
        )
    }

    config_manager.set(Config({
        "pipelines": {
            "test": [
                { "source": "test" }
            ]
        }
    }))

    srv = PipelineServerEv(config_manager.get_pipelines())
    srv.start()

    config_manager.get().add_callback(srv.trigger_event)
    config_manager.get_sources().set("test", source_cfg)
    # the callback will restart the process    
    assert srv.triggered




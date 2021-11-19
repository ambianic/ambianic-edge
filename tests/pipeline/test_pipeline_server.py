"""More test cases for ambianic.interpreter module."""
import logging
import os

from ambianic.configuration import get_root_config
from ambianic.pipeline.interpreter import PipelineServer

# mocked_settings = DynaconfDict({'FOO': 'BAR'})


log = logging.getLogger()
log.setLevel(logging.DEBUG)


def test_pipeline_server_start_stop():

    _dir = os.path.dirname(os.path.abspath(__file__))

    config = get_root_config()

    config.update(
        {
            "sources": {
                "test": {
                    "uri": "file://"
                    + os.path.join(_dir, "avsource/test2-cam-person1.mkv")
                }
            },
            "pipelines": {"test": [{"source": "test"}]},
        }
    )

    srv = PipelineServer(config)
    srv.start()
    srv.stop()

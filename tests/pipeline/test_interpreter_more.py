"""More test cases for ambianic.interpreter module."""
from ambianic import pipeline
from ambianic.pipeline.interpreter import PipelineServer, Pipeline
import logging
import time
import threading


log = logging.getLogger()
log.setLevel(logging.DEBUG)


class _TestSourceElement(pipeline.PipeElement):
    """Produce one sample and exit start loop."""

    def __init__(self, element_config=None):
        super().__init__()
        self.config = element_config
        self.start_called = False
        self.stop_called = False

    def start(self):
        self.start_called = True
        super().start()
        # send one sample down the pipe
        self.receive_next_sample(sample=[1, 2, 3])

    def stop(self):
        self.stop_called = True
        super().stop()


def _get_config(source_class=None):
    # override source op with a mock test class
    Pipeline.PIPELINE_OPS['source'] = source_class
    server_config = {
        'pipelines': {
            'pipeline_one': [
                      {'source': 'some_source'}
                      ]
            },
        }
    return server_config


def test_pipeline_server_init():
    conf = _get_config(_TestSourceElement)
    server = PipelineServer(conf)
    assert len(server._pipelines) == 1
    assert len(server._threaded_jobs) == 1


class _TestSourceElement2(pipeline.PipeElement):
    """Produce samples until stop signal."""

    def __init__(self, element_config=None):
        super().__init__()
        self.config = element_config

    def start(self):
        super().start()
        # send one samples until stopped
        while self.state == pipeline.PIPE_STATE_RUNNING:
            self.receive_next_sample(sample=[1, 2, 3])


def test_pipeline_server_start_stop():
    conf = _get_config(_TestSourceElement2)
    server = PipelineServer(conf)
    assert len(server._pipelines) == 1
    assert len(server._threaded_jobs) == 1
    source_pe = server._pipelines[0]._pipe_elements[0]
    assert source_pe.state == pipeline.PIPE_STATE_STOPPED
    assert not server._threaded_jobs[0].is_alive()
    server.start()
    assert source_pe.state == pipeline.PIPE_STATE_RUNNING
    assert server._threaded_jobs[0].is_alive()
    server.stop()
    assert source_pe.state == pipeline.PIPE_STATE_STOPPED
    assert not server._threaded_jobs[0].is_alive()


class _TestSourceElement3(pipeline.PipeElement):
    """Produce samples until stop signal."""

    def __init__(self, element_config=None):
        super().__init__()
        self._test_heal_called = threading.Event()
        self._test_sample_released = threading.Event()
        log.debug('heal() not called yet')

    def heal(self):
        self._test_heal_called.set()
        log.debug('heal() called')

    def start(self):
        super().start()
        # send one samples until stopped
        while self.state == pipeline.PIPE_STATE_RUNNING:
            self.receive_next_sample(sample=[1, 2, 3])
            # artifitial delay to force heal()
            log.debug('delaying next sample to cause heal()')
            time.sleep(2)
            self._test_sample_released.set()
            time.sleep(2)


def test_pipeline_server_heal():
    conf = _get_config(_TestSourceElement3)
    server = PipelineServer(conf)
    assert len(server._pipelines) == 1
    assert len(server._threaded_jobs) == 1
    source_pe = server._pipelines[0]._pipe_elements[0]
    assert source_pe.state == pipeline.PIPE_STATE_STOPPED
    assert not server._threaded_jobs[0].is_alive()
    server.MAX_HEARTBEAT_INTERVAL = 1
    server.start()
    assert source_pe.state == pipeline.PIPE_STATE_RUNNING
    assert server._threaded_jobs[0].is_alive()
    source_pe._test_sample_released.wait(timeout=5)
    server.healthcheck()
    assert source_pe._test_heal_called.wait(timeout=5)
    server.stop()
    assert source_pe.state == pipeline.PIPE_STATE_STOPPED
    assert not server._threaded_jobs[0].is_alive()


class _TestPipelineServer(PipelineServer):

    def __init__(self, config=None):
        super().__init__(config=config)
        self._test_on_terminal_health_called = threading.Event()

    def _on_terminal_pipeline_health(self, pipeline=None, lapse=None):
        log.debug('_on_terminal_pipeline_health called')
        super()._on_terminal_pipeline_health(pipeline, lapse)
        self._test_on_terminal_health_called.set()


def test_pipeline_server_terminal():
    conf = _get_config(_TestSourceElement3)
    server = _TestPipelineServer(conf)
    assert len(server._pipelines) == 1
    assert len(server._threaded_jobs) == 1
    source_pe = server._pipelines[0]._pipe_elements[0]
    server.TERMINAL_HEALTH_INTERVAL = 1
    server.start()
    source_pe._test_sample_released.wait(timeout=5)
    server.healthcheck()
    assert server._test_on_terminal_health_called.wait(timeout=5)
    server.stop()
    assert source_pe.state == pipeline.PIPE_STATE_STOPPED
    assert not server._threaded_jobs[0].is_alive()

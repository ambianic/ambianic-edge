
import pytest
import ambianic
from ambianic import __main__
from ambianic.server import AmbianicServer
import os
import threading


def test_no_work_dir():
    with pytest.raises(AssertionError):
        srv = AmbianicServer(work_dir=None)


def test_bad_work_dir():
    srv = AmbianicServer(work_dir='/_/_/_dir_does_not_exist___')
    with pytest.raises(AssertionError):
        srv.start()


class TestAmbianicServer(AmbianicServer):

    def __init__(self, work_dir=None, heartbeat_flag=None):
        super().__init__(work_dir)
        self._heartbeat_flag = heartbeat_flag
        assert heartbeat_flag

    def _heartbeat(self):
        super()._heartbeat()
        self._heartbeat_flag.set()

    def _register_sys_handlers(self):
        # skipping actual implementation
        # which interferes with pytest infrastructure
        pass


def test_no_pipelines():
    ambianic.server.CONFIG_FILE = 'test-config-no-pipelines.yaml'
    dir = os.path.dirname(os.path.abspath(__file__))
    hb_flag = threading.Event()
    srv = TestAmbianicServer(work_dir=dir, heartbeat_flag=hb_flag)
    t = threading.Thread(
        target=srv.start,
        daemon=True)
    t.start()
    hb_flag.wait(timeout=3)
    assert hb_flag.is_set()
    pps = srv._servers[0]
    assert isinstance(pps, ambianic.pipeline.interpreter.PipelineServer)
    assert not pps._pipelines
    srv.stop()
    t.join(timeout=3)
    assert not t.is_alive()


def test_main():
    ambianic.server.CONFIG_FILE = 'test-config-no-pipelines.yaml'
    dir = os.path.dirname(os.path.abspath(__file__))
    os.environ['AMBIANIC_DIR'] = dir
    t = threading.Thread(
        target=__main__.main,
        daemon=True)
    t.start()
    __main__.stop()
    t.join(timeout=3)
    assert not t.is_alive()


def test_one_pipeline():
    pass


def test_two_pipelines():
    pass


def test_flask_config_good():
    pass


def test_flask_config_bad():
    pass

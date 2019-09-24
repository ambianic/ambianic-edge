
import pytest
import ambianic
from ambianic import __main__
from ambianic.server import AmbianicServer
from ambianic.service import ServiceExit, ManagedService
from ambianic.pipeline.interpreter import PipelineServer
import os
import threading
import signal
import time


def test_no_work_dir():
    with pytest.raises(AssertionError):
        srv = AmbianicServer(work_dir=None)


def test_bad_work_dir():
    srv = AmbianicServer(work_dir='/_/_/_dir_does_not_exist___')
    with pytest.raises(AssertionError):
        srv.start()


class MockAmbianicServer(AmbianicServer):

    def __init__(self, work_dir=None, heartbeat_flag=None):
        super().__init__(work_dir)
        self._heartbeat_flag = heartbeat_flag
        self._main_heartbeat_logged = False

    def _heartbeat(self):
        super()._heartbeat()
        if self._heartbeat_flag:
            self._heartbeat_flag.set()

    def _log_heartbeat(self):
        self._main_heartbeat_logged = True


def _start_mock_server(**kwargs):
    srv = MockAmbianicServer(**kwargs)
    t = threading.Thread(
        target=srv.start,
        daemon=True)
    t.start()
    return (srv, t)


def _stop_mock_server(server=None, thread=None):
    assert server
    assert thread
    server.stop()
    thread.join(timeout=3)
    assert not thread.is_alive()


def test_no_pipelines():
    ambianic.server.CONFIG_FILE = 'test-config-no-pipelines.yaml'
    dir = os.path.dirname(os.path.abspath(__file__))
    hb_flag = threading.Event()
    srv, t = _start_mock_server(work_dir=dir, heartbeat_flag=hb_flag)
    hb_flag.wait(timeout=3)
    assert hb_flag.is_set()
    pps = srv._servers['pipelines']
    assert isinstance(pps, ambianic.pipeline.interpreter.PipelineServer)
    assert not pps._pipelines
    _stop_mock_server(server=srv, thread=t)


def test_main():
    ambianic.server.CONFIG_FILE = 'test-config-no-pipelines.yaml'
    dir = os.path.dirname(os.path.abspath(__file__))
    os.environ['AMBIANIC_DIR'] = dir
    t = threading.Thread(
        target=__main__.main,
        daemon=True)
    t.start()
    t.join(timeout=1)
    __main__.stop()
    t.join(timeout=3)
    assert not t.is_alive()


def test_system_shutdown_signal():
    with pytest.raises(ServiceExit):
        __main__._service_shutdown(signum=signal.SIGINT, frame=None)


class _BadPipelineServer(ManagedService):

    def __init__(self, config=None, **kwargs):
        super().__init__(**kwargs)
        self._heal_called = False

    def healthcheck(self):
        # return an old enough heartbeat time to trigger a health concern
        latest_heartbeat = time.monotonic() - \
            ambianic.server.MANAGED_SERVICE_HEARTBEAT_THRESHOLD - 10
        print('_BadPipelineServer latest_heartbeat - now: {}'.
              format(latest_heartbeat))
        return latest_heartbeat, "BAD"

    def heal(self):
        self._heal_called = True


def test_heartbeat_threshold():
    ambianic.server.CONFIG_FILE = 'test-config-no-pipelines.yaml'
    dir = os.path.dirname(os.path.abspath(__file__))
    # replace default with test pipeline server
    # remove all root servers which we won't test here
    ambianic.server.ROOT_SERVERS.clear()
    ambianic.server.ROOT_SERVERS['pipelines'] = _BadPipelineServer
    srv, t = _start_mock_server(work_dir=dir)
    t.join(timeout=2)
    pps = srv._servers['pipelines']
    assert isinstance(pps, _BadPipelineServer)
    assert pps._heal_called
    _stop_mock_server(server=srv, thread=t)


def test_main_heartbeat_log():
    ambianic.server.CONFIG_FILE = 'test-config-no-pipelines.yaml'
    dir = os.path.dirname(os.path.abspath(__file__))
    # remove all root servers which we will not test here
    ambianic.server.ROOT_SERVERS.clear()
    # set heartbeat log interval to a small enough
    # interval so the test passes faster
    ambianic.server.MAIN_HEARTBEAT_LOG_INTERVAL = 0.1
    srv, t = _start_mock_server(work_dir=dir)
    t.join(timeout=2)
    assert srv._main_heartbeat_logged
    _stop_mock_server(server=srv, thread=t)

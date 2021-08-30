import pytest
import ambianic
from ambianic import __main__, config, load_config
from ambianic.server import AmbianicServer
from ambianic.util import ServiceExit, ManagedService
from ambianic.pipeline.interpreter import PipelineServer
import os
import threading
import signal
import time
from pathlib import Path

@pytest.fixture
def my_dir():
    return os.path.dirname(os.path.abspath(__file__))

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
        self.config_changed = False

    def _heartbeat(self):
        super()._heartbeat()
        if self._heartbeat_flag:
            self._heartbeat_flag.set()

    def _log_heartbeat(self):
        super()._log_heartbeat()
        self._main_heartbeat_logged = True

    def dispatch(self, event):
        super().dispatch(event)
        self.config_changed = True


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
    thread.join(timeout=10)
    assert not thread.is_alive()


def test_no_pipelines(my_dir):
    load_config(os.path.join(my_dir, 'test-config-no-pipelines.yaml'), clean=True)    
    assert config.get("pipelines") is None
    hb_flag = threading.Event()
    srv, t = None, None
    try:
        srv, t = _start_mock_server(work_dir=my_dir, heartbeat_flag=hb_flag)
        assert srv
        assert t
        hb_flag.wait(timeout=3)
        assert hb_flag.is_set()
        pps = srv._servers['pipelines']
        assert isinstance(pps, ambianic.pipeline.interpreter.PipelineServer)
        assert not pps.pipeline_server_job.job._pipelines
    finally:
        _stop_mock_server(server=srv, thread=t)


def test_main(my_dir):

    os.environ['AMBIANIC_DIR'] = my_dir

    config.clean()
    load_config(os.path.join(my_dir, 'test-config-no-pipelines.yaml'), clean=True)    

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
        super().healthcheck()
        # return an old enough heartbeat time to trigger a health concern
        latest_heartbeat = time.monotonic() - \
            ambianic.server.MANAGED_SERVICE_HEARTBEAT_THRESHOLD - 10
        print('_BadPipelineServer latest_heartbeat - now: {}'.
              format(latest_heartbeat))
        return latest_heartbeat, "BAD"

    def heal(self):
        super().heal()
        self._heal_called = True


def test_heartbeat_threshold(my_dir):
    load_config(os.path.join(my_dir, 'test-config-no-pipelines.yaml'), clean=True)    
    # replace default with test pipeline server
    # remove all root servers which we won't test here
    ambianic.server.ROOT_SERVERS.clear()
    ambianic.server.ROOT_SERVERS['pipelines'] = _BadPipelineServer
    srv, t = _start_mock_server(work_dir=my_dir)
    t.join(timeout=2)
    pps = srv._servers['pipelines']
    assert isinstance(pps, _BadPipelineServer)
    assert pps._heal_called
    _stop_mock_server(server=srv, thread=t)


def test_main_heartbeat_log(my_dir):
    load_config(os.path.join(my_dir, 'test-config-no-pipelines.yaml'), True)
    # remove all root servers which we will not test here
    ambianic.server.ROOT_SERVERS.clear()
    # set heartbeat log interval to a small enough
    # interval so the test passes faster
    ambianic.server.MAIN_HEARTBEAT_LOG_INTERVAL = 0.1
    srv, t = _start_mock_server(work_dir=my_dir)
    t.join(timeout=2)
    assert srv._main_heartbeat_logged
    _stop_mock_server(server=srv, thread=t)

def test_config_change(my_dir):
    config_file = os.path.join(my_dir, 'test-config-no-pipelines.yaml')
    load_config(config_file, True)
    hb_flag = threading.Event()
    srv, t = None, None
    try:
        srv, t = _start_mock_server(work_dir=my_dir, heartbeat_flag=hb_flag)
        hb_flag.wait(timeout=3)
        Path(config_file).touch()
        time.sleep(3)
        assert hb_flag.is_set()
        assert srv.config_changed
    finally:
        _stop_mock_server(server=srv, thread=t)
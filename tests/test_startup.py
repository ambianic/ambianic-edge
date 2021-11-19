import logging
import os
import signal
import threading
import time
from pathlib import Path

import ambianic
import pytest
from ambianic import __main__
from ambianic.configuration import get_root_config, init_config
from ambianic.server import AmbianicServer
from ambianic.util import ManagedService, ServiceExit

log = logging.getLogger(__name__)


@pytest.fixture
def my_dir(request):
    return request.fspath.dirname


# module scoped test setup and teardown
# ref: https://docs.pytest.org/en/6.2.x/fixture.html#autouse-fixtures-fixtures-you-don-t-have-to-request
@pytest.fixture(autouse=True, scope="function")
def setup_module(request):
    """setup any state specific to the execution of the given module."""
    # save original env settings
    saved_amb_load = os.environ.get("AMBIANIC_CONFIG_FILES", "")
    saved_amb_dir = os.environ.get("AMBIANIC_DIR", "")
    # change env settings
    os.environ["AMBIANIC_CONFIG_FILES"] = str(
        Path(request.fspath.dirname) / "test-config-no-pipelines.yaml"
    )
    log.debug(
        f'os.environ["AMBIANIC_CONFIG_FILES"] = {os.environ["AMBIANIC_CONFIG_FILES"]}'
    )
    os.environ["AMBIANIC_DIR"] = saved_amb_dir
    init_config()
    yield
    # restore env settings
    os.environ["AMBIANIC_CONFIG_FILES"] = saved_amb_load
    os.environ["AMBIANIC_DIR"] = saved_amb_dir
    init_config()


@pytest.fixture(scope="function")
def config():
    return get_root_config()


def test_no_work_dir():
    with pytest.raises(AssertionError):
        AmbianicServer(work_dir=None)


def test_bad_work_dir():
    srv = AmbianicServer(work_dir="/_/_/_dir_does_not_exist___")
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
    t = threading.Thread(target=srv.start, daemon=True)
    t.start()
    return (srv, t)


def _stop_mock_server(server=None, thread=None):
    assert server
    assert thread
    server.stop()
    thread.join(timeout=10)
    assert not thread.is_alive()


def test_no_pipelines(my_dir, config):
    assert config.get("pipelines") is None
    hb_flag = threading.Event()
    srv, t = None, None
    try:
        srv, t = _start_mock_server(work_dir=my_dir, heartbeat_flag=hb_flag)
        assert srv
        assert t
        hb_flag.wait(timeout=3)
        assert hb_flag.is_set()
        pps = srv._servers["pipelines"]
        assert isinstance(pps, ambianic.pipeline.interpreter.PipelineServer)
        assert not pps.pipeline_server_job.job._pipelines
    finally:
        _stop_mock_server(server=srv, thread=t)


def test_main(my_dir, config):
    t = threading.Thread(target=__main__.start, daemon=True)
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
        latest_heartbeat = (
            time.monotonic() - ambianic.server.MANAGED_SERVICE_HEARTBEAT_THRESHOLD - 10
        )
        print(f"_BadPipelineServer latest_heartbeat - now: {latest_heartbeat}")
        return latest_heartbeat, "BAD"

    def heal(self):
        super().heal()
        self._heal_called = True


def test_heartbeat_threshold(my_dir):
    # replace default with test pipeline server
    # remove all root servers which we won't test here
    ambianic.server.ROOT_SERVERS.clear()
    ambianic.server.ROOT_SERVERS["pipelines"] = _BadPipelineServer
    srv, t = _start_mock_server(work_dir=my_dir)
    t.join(timeout=2)
    pps = srv._servers["pipelines"]
    assert isinstance(pps, _BadPipelineServer)
    assert pps._heal_called
    _stop_mock_server(server=srv, thread=t)


def test_main_heartbeat_log(my_dir, config):
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
    config_file = os.path.join(my_dir, "test-config-no-pipelines.yaml")
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

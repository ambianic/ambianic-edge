"""Test configuration functions."""
import logging
import logging.handlers
import os
from pathlib import Path

import ambianic
import pytest
from ambianic.configuration import get_root_config, get_work_dir, init_config

log = logging.getLogger(__name__)


# module scoped test setup and teardown
# ref: https://docs.pytest.org/en/6.2.x/fixture.html#autouse-fixtures-fixtures-you-don-t-have-to-request
@pytest.fixture(autouse=True, scope="module")
def setup_module(request):
    """setup any state specific to the execution of the given module."""
    # save original env settings
    saved_amb_load = os.environ.get("AMBIANIC_CONFIG_FILES", "")
    saved_amb_dir = os.environ.get("AMBIANIC_DIR", "")
    # change env settings
    os.environ["AMBIANIC_CONFIG_FILES"] = (
        str(Path(request.fspath.dirname) / "test-config-no-pipelines.yaml")
        + ","
        + str(Path(request.fspath.dirname) / "test-config-secrets.yaml")
        + ","
        + str(Path(request.fspath.dirname) / "test-secrets.yaml")
    )
    log.debug(
        f'os.environ["AMBIANIC_CONFIG_FILES"] = {os.environ["AMBIANIC_CONFIG_FILES"]}'
    )
    init_config()
    yield
    # restore env settings
    os.environ["AMBIANIC_CONFIG_FILES"] = saved_amb_load
    os.environ["AMBIANIC_DIR"] = saved_amb_dir
    init_config()


@pytest.fixture(scope="function")
def config():
    return get_root_config()


def test_get_workdir_env():
    os.environ["AMBIANIC_DIR"] = "/foo"
    assert get_work_dir() == "/foo"
    os.environ["AMBIANIC_DIR"] = ""
    assert get_work_dir() == ambianic.configuration.DEFAULT_WORK_DIR


def test_no_pipelines(config):
    assert config.get("pipelines", None) is None


def test_secrets(config):
    assert config.get("question") == "question answer is 42"
    assert config.deeeper.question.on.life == "42"

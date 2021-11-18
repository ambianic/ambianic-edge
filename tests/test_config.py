"""Test configuration functions."""
import logging
import logging.handlers
import os

import ambianic
from ambianic.configuration import (
    get_root_config,
    get_work_dir,
    init_config,
    load_config,
)

log = logging.getLogger(__name__)

_dir = os.path.dirname(os.path.abspath(__file__))


def setup_module(module):
    """setup any state specific to the execution of the given module."""
    init_config()


def test_get_workdir_env():
    os.environ["AMBIANIC_DIR"] = "/foo"
    assert get_work_dir() == "/foo"
    os.environ["AMBIANIC_DIR"] = ""
    assert get_work_dir() == ambianic.configuration.DEFAULT_WORK_DIR


def test_no_pipelines():
    load_config(os.path.join(_dir, "test-config-no-pipelines.yaml"), True)
    assert get_root_config().get("pipelines", None) is None


def test_secrets():
    default_secret = ambianic.configuration.__secrets_file
    ambianic.configuration.__secrets_file = os.path.join(_dir, "test-secrets.yaml")
    cfg = load_config(os.path.join(_dir, "test-config-secrets.yaml"), True)
    ambianic.configuration.__secrets_file = default_secret
    assert cfg.get("question") == "question answer is 42"
    assert cfg.deeeper.question.on.life == "42"

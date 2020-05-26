"""Test configuration functions."""
import pytest
import logging
import logging.handlers
import ambianic
from ambianic.server import AmbianicServer
from ambianic import server, config_manager
from ambianic import config_manager
import os
import yaml
import pathlib
from time import sleep


class Watch:
    """Utililty to watch for changes"""

    def __init__(self):
        self.changed = False

    def on_change(self):
        self.changed = True


def write_config(config_file, config):
    """Write YAML configuration to file"""
    with open(config_file, 'w') as fh:
        yaml.dump(config, fh, default_flow_style=False)


def setup_module(module):
    """ setup any state specific to the execution of the given module."""
    pass


def teardown_module(module):
    """ teardown any state that was previously setup with a setup_module
     method."""
    config_manager.stop()


def test_no_config():
    conf = server._configure('/')
    assert not conf


def test_log_config_with_file():
    _dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(_dir, '.__test-log.txt')
    log_config = {
        'file': log_path,
    }
    server._configure_logging(config=log_config)
    handlers = logging.getLogger().handlers
    log_fn = None
    for h in handlers:
        if isinstance(h, logging.handlers.RotatingFileHandler):
            log_fn = h.baseFilename
            assert log_fn == log_config['file']
    # at least one log file name should be configured
    assert log_fn


def test_log_config_without_file():
    log_config = {
    }
    server._configure_logging(config=log_config)
    handlers = logging.getLogger().handlers
    for h in handlers:
        assert not isinstance(h, logging.handlers.RotatingFileHandler)


def test_log_config_with_debug_level():
    log_config = {
        'level': 'DEBUG'
    }
    server._configure_logging(config=log_config)
    root_logger = logging.getLogger()
    effective_level = root_logger.getEffectiveLevel()
    lname = logging.getLevelName(effective_level)
    assert lname == log_config['level']


def test_log_config_with_warning_level():
    log_config = {
        'level': 'WARNING'
    }
    server._configure_logging(config=log_config)
    root_logger = logging.getLogger()
    effective_level = root_logger.getEffectiveLevel()
    lname = logging.getLevelName(effective_level)
    assert lname == log_config['level']


def test_log_config_without_level():
    log_config = {}
    server._configure_logging(config=log_config)
    root_logger = logging.getLogger()
    effective_level = root_logger.getEffectiveLevel()
    assert effective_level == server.DEFAULT_LOG_LEVEL


def test_log_config_bad_level1():
    log_config = {
        'level': '_COOCOO_'
    }
    server._configure_logging(config=log_config)
    root_logger = logging.getLogger()
    effective_level = root_logger.getEffectiveLevel()
    assert effective_level == server.DEFAULT_LOG_LEVEL


def test_log_config_bad_level2():
    log_config = {
        'level': 2.56
    }
    server._configure_logging(config=log_config)
    root_logger = logging.getLogger()
    effective_level = root_logger.getEffectiveLevel()
    assert effective_level == server.DEFAULT_LOG_LEVEL


def test_config_with_secrets():
    config_manager.SECRETS_FILE = 'test-config-secrets.yaml'
    config_manager.CONFIG_FILE = 'test-config.yaml'
    _dir = os.path.dirname(os.path.abspath(__file__))
    conf = server._configure(_dir)
    assert conf
    assert conf['logging']['level'] == 'DEBUG'
    assert conf['sources']['front_door_camera']['uri'] == 'secret_uri'


def test_config_without_secrets_failed_ref():
    config_manager.SECRETS_FILE = '__no__secrets__.lmay__'
    config_manager.CONFIG_FILE = 'test-config.yaml'
    _dir = os.path.dirname(os.path.abspath(__file__))
    conf = server._configure(_dir)
    assert not conf


def test_config_without_secrets_no_ref():
    config_manager.SECRETS_FILE = '__no__secrets__.lmay__'
    config_manager.CONFIG_FILE = 'test-config2.yaml'
    _dir = os.path.dirname(os.path.abspath(__file__))
    conf = server._configure(_dir)
    assert conf
    assert conf['logging']['level'] == 'DEBUG'
    assert conf['sources']['front_door_camera']['uri'] == 'no_secret_uri'


def test_no_pipelines():
    config_manager.CONFIG_FILE = 'test-config-no-pipelines.yaml'
    _dir = os.path.dirname(os.path.abspath(__file__))
    conf = server._configure(_dir)
    assert not conf


def test_reload():

    config_manager.CONFIG_FILE = 'test-config.1.yaml'
    _dir = os.path.dirname(os.path.abspath(__file__))
    config = {"logging": {"level": "INFO"}}
    config_file = os.path.join(_dir, config_manager.CONFIG_FILE)

    write_config(config_file, config)

    config1 = config_manager.load(_dir)

    assert config["logging"]["level"] == config1["logging"]["level"]

    watcher = Watch()

    config_manager.register_handler(lambda cfg: watcher.on_change())

    config["logging"]["level"] = "WARN"
    write_config(config_file, config)

    # wait for polling to happen
    while not watcher.changed:
        sleep(.25)

    config3 = config_manager.get()
    assert config["logging"]["level"] == config3["logging"]["level"]


def test_callback():

    config_manager.CONFIG_FILE = 'test-config.2.yaml'
    _dir = os.path.dirname(os.path.abspath(__file__))
    config = {"test": True}
    config_file = os.path.join(_dir, config_manager.CONFIG_FILE)

    write_config(config_file, config)
    config_manager.load(_dir)

    watcher = Watch()

    config_manager.register_handler(lambda cfg: watcher.on_change())
    write_config(config_file, config)

    # wait for polling to happen
    while not watcher.changed:
        sleep(.25)

    assert watcher.changed

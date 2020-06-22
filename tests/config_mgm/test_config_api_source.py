import os
from ambianic.webapp.server import config_sources
from ambianic import config_manager
from werkzeug.exceptions import NotFound, BadRequest


def get_test_config():
    config_manager.stop()
    config_manager.CONFIG_FILE = 'test-sources.yaml'
    _dir = os.path.dirname(os.path.abspath(__file__))
    config = config_manager.load(_dir)
    assert config is not None
    return config


def teardown_module(module):
    """ teardown any state that was previously setup with a setup_module
     method."""
    config_manager.stop()


def test_save():

    config = get_test_config()

    source_id = "test_add"
    result = config_sources.save(source_id, {
        "uri": source_id,
        "type": "video",
        "live": True,
    })

    assert result["id"] == source_id
    source1 = config_manager.get()["sources"][source_id]
    assert config_manager.get()["sources"][source_id]
    assert source1["uri"] == source_id


def test_save_bad_args():

    args = [
        {
            "uri": {},  # bad
            "type": "video",
            "live": False
        },
        {
            "uri": "hello",
            "type": "boom",  # bad
            "live": False
        },
        {
            "uri": "test",
            "type": "video",
            "live": None  # bad
        },
        {
            "id": 3.14,
            "uri": "test",
            "type": "video",
            "live": True  # bad
        },
    ]
    for arg in args:
        try:
            if "id" not in arg.keys():
                arg["id"] = "test"
            config_sources.save(arg["id"], arg)
            assert False
        except BadRequest:
            pass


def test_remove_bad_id():
    for arg in [None, {}, 100]:
        try:
            config_sources.remove(arg)
            assert False
        except BadRequest:
            pass


def test_remove():

    config = get_test_config()

    config.sync({
        "sources": {
            "a": {
                "uri": "a"
            },
            "b": {
                "uri": "b"
            }
        }
    })

    config_sources.remove("a")

    assert "a" not in list(config["sources"].keys())
    assert len(config["sources"]) == 2

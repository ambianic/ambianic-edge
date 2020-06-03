import os
from ambianic.webapp.server.config_api import sources
from ambianic import config_manager


def teardown_module(module):
    """ teardown any state that was previously setup with a setup_module
     method."""
    config_manager.stop()


def test_save():

    config_manager.stop()
    config_manager.CONFIG_FILE = 'test-sources.yaml'
    _dir = os.path.dirname(os.path.abspath(__file__))
    config = config_manager.load(_dir)
    assert config is not None

    source_id = "test_add"
    result = sources.save(source_id, {
        "uri": source_id,
        "type": "video",
        "live": True,
    })

    assert result["id"] == source_id
    source1 = config_manager.get()["sources"][source_id]
    assert config_manager.get()["sources"][source_id]
    assert source1["uri"] == source_id


def test_remove():

    config_manager.stop()
    config_manager.CONFIG_FILE = 'test-sources.yaml'
    _dir = os.path.dirname(os.path.abspath(__file__))
    config = config_manager.load(_dir)
    assert config is not None

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

    sources.remove("a")

    assert "a" not in list(config["sources"].keys())
    assert len(config["sources"]) == 2

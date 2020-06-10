import logging
from time import sleep
from ambianic.config_mgm import config_diff

log = logging.getLogger(__name__)


class CallbackWatcher:
    def __init__(self):
        self.event: config_diff.ConfigChangedEvent = None

    def on_callback(self, event: config_diff.ConfigChangedEvent):
        self.event = event


def test_accessors():

    test1 = {
        "version": "1.2.3",
        "logging": {
            "level": "string"
        },
        "ai_models": {
            "image_detection": {
                "model": {
                    "tflite": "string",
                    "edgetpu": "string"
                },
                "labels": "string",
                "top_k": 2,
                "precision": 0.8
            }
        },
        "pipelines": {
            "front_door_watch": [
                {"source": "src_recorded_cam_feed"}
            ]
        }
    }

    cfg = config_diff.Config(test1)

    assert cfg.get("version") == test1["version"]
    assert cfg["ai_models"]["image_detection"]["model"]["edgetpu"] == test1[
        "ai_models"]["image_detection"]["model"]["edgetpu"]
    assert len(cfg["pipelines"]["front_door_watch"]) == 1

    version1 = "1.2.3.4"
    cfg.set("version", version1)
    assert cfg.get("version") == version1
    assert cfg.get("non_existant", "ok") == "ok"


def test_callbacks():

    test1 = {
        "version": "1.2.3",
        "logging": {
            "level": "WARN",
            "options": ["a", "b", "c"]
        }
    }

    cfg = config_diff.Config(test1)

    assert cfg.get("version") == test1["version"]
    assert cfg["logging"]["level"] == test1["logging"]["level"]

    def test1_cb(event: config_diff.ConfigChangedEvent):
        # print("***** event", event)
        if event.get_name() == "level":
            assert event.new_value == "DEBUG" or event.new_value == "INFO"
    cfg.add_callback(test1_cb)

    test1["logging"]["level"] = "DEBUG"
    cfg.update(test1)
    cfg["logging"]["level"] = "INFO"

    def test2_cb(event: config_diff.ConfigChangedEvent):
        assert len(cfg["logging"]["options"]) >= 3
    cfg.add_callback(test2_cb)

    test1["logging"]["options"].append('d')
    cfg.update(test1)

    cfg["logging"]["options"][0] = 'y'

    assert cfg["logging"]["options"][0] == 'y'

    def test3_cb(event: config_diff.ConfigChangedEvent):
        raise Exception("ouch!")
    cfg.add_callback(test3_cb)

    cfg["logging"]["options"].append("z")

    assert len(cfg["logging"]["options"]) == 5


def test_list_eq():

    test1 = [
        {"v": ["a", "b"]},
        {"v": ["c", "d"]},
    ]
    test2 = [
        {"v": ["a", "b"]},
    ]
    test3 = [
        {"v": ["c", "d"]},
        {"v": ["a", "b"]},
    ]
    cfg = config_diff.Config(test1)

    assert isinstance(cfg, config_diff.ConfigList)
    assert cfg[1] == test1[1]
    assert cfg == test1
    assert cfg != test2
    assert cfg != test3


def test_embed_list_diff():

    test1 = {
        "list": [
            {"v": ["a", "b"]},
            {"v": ["c", "d"]},
        ]
    }

    cfg = config_diff.Config(test1)

    assert isinstance(cfg["list"][0]["v"], config_diff.ConfigList)
    assert cfg["list"][1] == test1["list"][1]

    test1["list"].clear()
    cfg.sync(test1)

    assert len(test1["list"]) == 0

    cfg["list"].insert(0, {"v": ["e", "f"]})
    assert len(cfg["list"]) == 1

    cfg["list"] += [{"v": ["g", "h"]}]
    assert len(cfg["list"]) == 2

    cfg["list"].extend([{"v": ["i", "l"]}])
    assert len(cfg["list"]) == 3

    cfg["list"][0] = {"v": []}
    assert len(cfg["list"]) == 3
    assert len(cfg["list"][0]["v"]) == 0


def test_list_diff():

    el3 = {"name": "el3"}

    test1 = {
        "pipelines": {
            "foo1": [
                {"name": "el1"},
                {"name": "el2"},
                el3
            ]
        }
    }

    cfg = config_diff.Config(test1)

    assert len(cfg["pipelines"]["foo1"]) == 3

    watcher = CallbackWatcher()
    cfg.add_callback(watcher.on_callback)

    # test equality
    assert cfg["pipelines"]["foo1"] == test1["pipelines"]["foo1"]

    del cfg["pipelines"]["foo1"][0]
    cfg["pipelines"]["foo1"].remove(el3)
    assert len(cfg["pipelines"]["foo1"]) == 1

    log.info("Config %s", cfg)

    tries = 5
    while watcher.event is None:
        sleep(0.1)
        tries -= 1
        if tries == 0:
            raise Exception("Callback not triggered")

    cfg["pipelines"]["foo1"][0]["name"] = "hello"

    assert len(watcher.event.get_paths()) == 3
    assert watcher.event.get_root() is not None

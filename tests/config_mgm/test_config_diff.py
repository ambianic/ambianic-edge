from ambianic.config_mgm import config_diff


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
    assert cfg["ai_models"]["image_detection"]["model"]["edgetpu"] == test1["ai_models"]["image_detection"]["model"]["edgetpu"]
    assert len(cfg["pipelines"]["front_door_watch"]) == 1


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
    cfg.set_callback(test1_cb)

    test1["logging"]["level"] = "DEBUG"
    cfg.update(test1)
    cfg["logging"]["level"] = "INFO"

    def test2_cb(event: config_diff.ConfigChangedEvent):
        assert len(cfg["logging"]["options"]) >= 3
    cfg.set_callback(test2_cb)

    test1["logging"]["options"].append('d')
    cfg.update(test1)

    cfg["logging"]["options"][0] = 'y'

    assert cfg["logging"]["options"][0] == 'y'


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

    def test1_cb(event: config_diff.ConfigChangedEvent):
        # print("***** event", event)
        assert len(cfg["pipelines"]["foo1"]) <= 3
    cfg.set_callback(test1_cb)

    del cfg["pipelines"]["foo1"][0]
    cfg["pipelines"]["foo1"].remove(el3)
    assert len(cfg["pipelines"]["foo1"]) == 1

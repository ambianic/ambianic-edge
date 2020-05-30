from ambianic.config_mgm import config_diff


def test_diff():

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

    def change_callback(event: config_diff.ConfigChangedEvent):
        print("Got change", event)

    cfg = config_diff.Config(test1)
    cfg.set_callback(change_callback)

    print(cfg)

    assert cfg.get("version") == test1["version"]
    assert cfg["ai_models"]["image_detection"]["model"]["edgetpu"] == test1["ai_models"]["image_detection"]["model"]["edgetpu"]
    assert len(cfg["pipelines"]["front_door_watch"]) == 1

    test1["version"] = "3.2.1"
    test1["ai_models"]["image_detection"]["model"]["edgetpu"] = "foo"
    test1["pipelines"]["front_door_watch"].append(
        {"source": "test2"}
    )

    cfg.update(test1)

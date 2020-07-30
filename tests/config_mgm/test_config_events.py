import logging
from time import sleep
from ambianic.config_mgm import config_diff

log = logging.getLogger(__name__)


class CallbackWatcher:
    def __init__(self):
        self.event: config_diff.ConfigChangedEvent = None
        
    def reset(self):
        self.event = None

    def on_callback(self, event: config_diff.ConfigChangedEvent):

        assert event.get_name()
        assert event.get_operation()
        assert event.get_value()
        assert isinstance(event.get_tree(), list)

        self.event = event


def test_callbacks():

    watcher = CallbackWatcher()

    test1 = {
        "version": "1.2.3"
    }

    cfg = config_diff.Config(test1)

    cfg.add_callback(watcher.on_callback)

    cfg.set("version", "3.2.1")

    assert cfg.get("version") == "3.2.1"
    assert watcher.event is not None

    cfg.remove_callback(watcher.on_callback)
    cfg.remove_callback(lambda ev: print(ev))

    assert len(cfg.get_callbacks()) == 0

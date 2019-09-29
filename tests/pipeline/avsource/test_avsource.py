"""Test audio/video source pipeline element."""
import pytest
from ambianic.pipeline.avsource.av_element \
    import AVSourceElement, MIN_HEALING_INTERVAL
import threading


def test_no_config():
    with pytest.raises(AssertionError):
        AVSourceElement()


class _TestAVSourceElement(AVSourceElement):

    def __init__(self, **source_conf):
        super().__init__(**source_conf)
        self._run_gst_service_called = False
        self._stop_gst_service_called = False

    def _run_gst_service(self):
        self._run_gst_service_called = True
        pass

    def _stop_gst_service(self):
        self._stop_gst_service_called = True
        pass


def test_no_config():
    with pytest.raises(AssertionError):
        AVSourceElement()


def test_start_stop():
    avsource = _TestAVSourceElement(uri='rstp://blah', type='video')
    t = threading.Thread(
        name="Test AVSourceElement",
        target=avsource.start, daemon=True
        )
    t.start()
    t.join(timeout=1)
    assert avsource._run_gst_service_called
    assert t.is_alive()
    avsource.stop()
    t.join(timeout=1)
    assert avsource._stop_gst_service_called
    assert not t.is_alive()


def test_heal():
    avsource = _TestAVSourceElement(uri='rstp://blah', type='video')
    t = threading.Thread(
        name="Test AVSourceElement",
        target=avsource.start, daemon=True
        )
    t.start()
    t.join(timeout=1)
    # simulate the pipe element has been unhealthy for long enough
    avsource._latest_healing = \
        avsource._latest_healing - 2*MIN_HEALING_INTERVAL
    avsource.heal()
    # heal should have done its job and stopped the gst service for repair
    assert avsource._stop_gst_service_called
    latest = avsource._latest_healing
    avsource.heal()
    # heal should ignore back to back requests
    # latest healing timestamp should be unchanged
    assert latest == avsource._latest_healing
    # set the latest healing clock back by more than the min interval
    avsource._latest_healing = \
        avsource._latest_healing - 2*MIN_HEALING_INTERVAL
    avsource.heal()
    # now the healing process should have ran and
    # set the latest timestamp to a more recent time than the last healing run
    assert latest < avsource._latest_healing
    assert t.is_alive()
    # reset the gst stop flag to test if
    # the method will be called again by stop()
    avsource._stop_gst_service_called = False
    avsource.stop()
    t.join(timeout=1)
    assert avsource._stop_gst_service_called
    assert not t.is_alive()

import pytest
import threading
import smokesignal
import logging
from . import light


@pytest.fixture(autouse=True)
def clear_smokesignal():
    smokesignal.clear_all()


@pytest.fixture(autouse=True)
def all_logging(caplog):
    caplog.set_level(logging.DEBUG)


class Factory:
    def __init__(self):
        self.lights = []

    def get_light(self, id=None):
        newlight = light.Light(id)
        self.lights.append(newlight)
        return newlight

    def stop_all(self):
        for mylight in self.lights:
            mylight.stop()
            mylight.join()


@pytest.fixture
def factory():
    f = Factory()
    yield f
    f.stop_all()


class TestLight:
    def test_master(self, factory):
        mylight = factory.get_light("master")
        mylight.start()
        # first cycle includes arbiter delay, allow for it
        self.assert_event_within(mylight, 0.6, True)
        self.assert_event_within(mylight, 0.51, False)
        self.assert_event_within(mylight, 0.51, True)
        self.assert_event_within(mylight, 0.51, False)

    def test_slave(self, factory):
        mylight = factory.get_light("slave")
        mylight.start()

        sync_recvcnt = 0

        def _on_sync():
            nonlocal sync_recvcnt
            sync_recvcnt += 1
        smokesignal.on("sync", _on_sync)

        sync_emitcnt = 3
        for _ in range(sync_emitcnt):
            smokesignal.emit("sync")
            # allow small delay for thread to run
            self.assert_event_within(mylight, 0.001, True)
            self.assert_event_within(mylight, 0.51, False)

        assert sync_recvcnt == sync_emitcnt, "more syncs received than expected, " \
            "means that light might have turned into a master"

    def assert_event_within(self, light: light.Light, timeout, new_state=None):
        event = threading.Event()
        state = None

        def _on_change(new_state):
            nonlocal state
            state = new_state
            event.set()

        smokesignal.once(light.signal_name, _on_change)
        assert event.wait(timeout)
        if new_state is not None:
            assert state == new_state

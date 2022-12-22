import threading
import smokesignal
from . import light


class TestLight:
    def test_master(self):
        mylight = light.Light()
        mylight.start()
        # first cycle includes arbiter delay, allow for it
        self.assert_event_within(mylight, 0.6, True)
        self.assert_event_within(mylight, 0.51, False)
        self.assert_event_within(mylight, 0.51, True)
        self.assert_event_within(mylight, 0.51, False)
        mylight.stop()

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

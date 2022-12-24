import threading
import random
import time
import logging
import smokesignal


class Light(threading.Thread):
    PERIOD = 1.0
    _next_id = 0

    def __init__(self, id=None):
        super().__init__()
        self.daemon = True
        self._sync = threading.Event()
        self._stop_flag = threading.Event()
        self._lock = threading.Lock()
        self._is_enabled = True
        self._was_enabled = True
        if not id:
            id = self._generate_id()
        self._id = id

        self._is_master = False
        self._is_on = False

        self._logger = logging.getLogger(f"light {self._id}")

        smokesignal.on("sync", self._on_sync)

    def enable(self):
        with self._lock:
            self._is_enabled = True

    def disable(self):
        with self._lock:
            self._is_enabled = False

    @property
    def is_enabled(self):
        with self._lock:
            return self._is_enabled

    @classmethod
    def _generate_id(cls):
        new_id = cls._next_id
        cls._next_id += 1
        return new_id

    def _on_sync(self):
        self._sync.set()

    def run(self):
        while not self._stop_flag.is_set():
            with self._lock:
                disable_now = first_cycle = False
                enabled = self._is_enabled
                if enabled != self._was_enabled:
                    smokesignal.emit(f"{self.signal_name}-toggled")
                    if enabled:
                        self._logger.info("enabling")
                        first_cycle = True
                        self._sync.clear()
                    else:
                        self._logger.info("disabling")
                        disable_now = True
                self._was_enabled = enabled
            if enabled:
                self._cycle(first_cycle)
            else:
                if disable_now:
                    self._is_master = False
                    self.is_on = False
                time.sleep(0.1)

    def _cycle(self, first_cycle):
        if self._is_master:
            # check for collision
            # also, use this for timing the sync
            if self._sync.wait(self.PERIOD / 2):
                self._logger.warn("collision detected, degrading to slave")
                smokesignal.emit("master-collision-detected",
                                 self._id)
                self._is_master = False
            else:
                smokesignal.emit("sync")
            self._blink()
        else:
            arbitration_timeout = random.random() / 100 + 0.005
            if first_cycle:
                # allow to get back in phase
                timeout = self.PERIOD + 0.1
                self._logger.debug("first cycle, waiting period to get in phase...")
            else:
                timeout = self.PERIOD / 2 + arbitration_timeout
            if self._sync.wait(timeout):
                self._blink()
            else:
                self._logger.debug("timed out waiting for sync")
                if not self._sync.is_set():
                    self._logger.info("electing itself")
                    self._is_master = True
                    smokesignal.emit("sync")
                else:
                    self._logger.info("was about to elect itself, "
                                      "but another light did in the meantime "
                                      "(collision avoidance)")
                # compensate for extra delay, to stay in phase
                self._blink(self.PERIOD / 2 - arbitration_timeout)
        self._sync.clear()

    def _blink(self, shine_time=None):
        if not shine_time:
            shine_time = self.PERIOD / 2

        self.is_on = True
        time.sleep(shine_time)
        self.is_on = False

    @property
    def is_on(self) -> bool:
        return self._is_on

    @is_on.setter
    def is_on(self, state):
        self._is_on = state
        smokesignal.emit(self.signal_name, state)

    @property
    def is_master(self) -> bool:
        return self._is_master

    @property
    def signal_name(self):
        return f"light-{self._id}"

    def stop(self):
        self._stop_flag.set()

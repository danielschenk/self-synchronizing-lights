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
        self._sync = threading.Event()
        self._stop_flag = threading.Event()
        if not id:
            id = self._generate_id()
        self._id = id

        self._master = False
        self._is_on = False

        self._logger = logging.getLogger(f"light {self._id}")

        smokesignal.on("sync", self._on_sync)

    @classmethod
    def _generate_id(cls):
        new_id = cls._next_id
        cls._next_id += 1
        return new_id

    def _on_sync(self):
        self._sync.set()

    def run(self):
        while not self._stop_flag.is_set():
            if self._master:
                # signal shouldn't be set by anyone else - check anyway
                # also, use this for timing the sync
                if self._sync.wait(self.PERIOD / 2):
                    self._logger.error("collision detected, degrading to slave")
                    smokesignal.emit("master-collision-detected",
                                     self._id)
                    self._master = False
                else:
                    self._logger.debug("emitting sync")
                    smokesignal.emit("sync")
                self._blink()
            else:
                arbiting_timeout = random.random() / 100
                if self._sync.wait(self.PERIOD / 2 + arbiting_timeout):
                    self._logger.debug("received sync")
                    self._blink()
                else:
                    self._logger.debug("timed out waiting for sync")
                    if not self._sync.is_set():
                        self._logger.info("electing itself")
                        self._master = True
                        smokesignal.emit("sync")
                    else:
                        self._logger.info("was about to elect itself, "
                                          "but another light did in the meantime "
                                          "(collision avoidance)")
                    # compensate for extra delay, to stay in phase
                    self._blink(self.PERIOD / 2 - arbiting_timeout)
            self._sync.clear()

    def _blink(self, shine_time=None):
        self._logger.info("blinking")
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
    def signal_name(self):
        return f"light-{self._id}"

    def stop(self):
        self._stop_flag.set()

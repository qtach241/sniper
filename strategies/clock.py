import datetime as dt

DEFAULT_EPOCH = 3
DEFAULT_TIME_END = 9999999999

class Clock():
    def __init__(self, start, end=9999999999, epoch=DEFAULT_EPOCH):
        self._epoch = epoch*24*60*60 # Convert days to seconds.
        self._epoch_start = 0

        self._current_time = 0
        self._end_time = end
        self.set_time(start)

    def reset_epoch(self) -> None:
        self._epoch_start = 0

    def set_time(self, time) -> None:
        if self._epoch_start == 0:
            self._epoch_start = time
        self._current_time = time

    def get_time(self):
        return self._current_time

    def time_til_epoch(self):
        return self._epoch_start + self._epoch - self._current_time

    def time_til_end(self):
        return self._end_time - self._current_time

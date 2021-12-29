import datetime as dt

class Clock():
    def __init__(self, time):
        self._start_time = 0
        self._current_time = 0
        self.set_time(time)

    def set_time(self, time) -> None:
        if self._start_time == 0:
            self._start_time = time
        self.current_time = time

    def reset(self) -> None:
        self._start_time = 0
        self._current_time = 0

    def get_elapsed_time(self) -> dt.timedelta:
        return self._current_time - self._start_time

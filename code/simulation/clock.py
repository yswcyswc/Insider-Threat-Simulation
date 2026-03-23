"""
simulation/clock.py
Discrete-time clock. 1 tick = 1 hour.
"""

from config import settings


class SimulationClock:

    def __init__(self):
        self._tick           = 0
        self._ticks_per_hour = settings.TICKS_PER_HOUR
        self._total_ticks    = settings.SIMULATION_DAYS * 24 * self._ticks_per_hour

    @property
    def tick(self) -> int:
        return self._tick

    @property
    def day(self) -> int:
        return (self._tick // (24 * self._ticks_per_hour)) + 1

    @property
    def hour(self) -> int:
        return (self._tick % (24 * self._ticks_per_hour)) // self._ticks_per_hour

    @property
    def is_work_hours(self) -> bool:
        return settings.WORK_HOURS_START <= self.hour < settings.WORK_HOURS_END

    @property
    def finished(self) -> bool:
        return self._tick >= self._total_ticks

    @property
    def time_label(self) -> str:
        return f"Day {self.day:02d}  {self.hour:02d}:00"

    def advance(self) -> None:
        self._tick += 1

    def snapshot(self) -> dict:
        return {
            "tick":          self._tick,
            "day":           self.day,
            "hour":          self.hour,
            "time_label":    self.time_label,
            "is_work_hours": self.is_work_hours,
        }

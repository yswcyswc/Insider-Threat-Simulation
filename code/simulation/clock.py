"""
simulation/clock.py — discrete-time clock. 1 tick = 1 second.
"""

from config import settings


class SimulationClock:

    def __init__(self):
        self.tick  = 0 
        self.total = settings.SIMULATION_DAYS * settings.SECONDS_PER_DAY

    @property
    def day(self) -> int:
        return self.tick // settings.SECONDS_PER_DAY + 1

    @property
    def hour(self) -> int:
        return (self.tick % settings.SECONDS_PER_DAY) // settings.SECONDS_PER_HOUR

    @property
    def minute(self) -> int:  
        return (self.tick % settings.SECONDS_PER_HOUR) // 60

    @property
    def second(self) -> int:    
        return self.tick % 60

    @property
    def is_work_hours(self) -> bool:
        return settings.WORK_HOURS_START <= self.hour < settings.WORK_HOURS_END

    @property
    def finished(self) -> bool:
        return self.tick >= self.total

    @property
    def label(self) -> str:
        return f"Day {self.day:02d}  {self.hour:02d}:00"

    def advance(self, step=1):
        self.tick += step

"""
simulation/engine.py — the main simulation loop.

Each tick (= 1 hour):
  1. Every agent gains risk.
  2. If work hours → run email sessions and log each state.
  3. If off hours  → log IDLE.
"""

from config import settings
from simulation.clock import SimulationClock
from simulation.logger import EventLogger
from agent import EmployeeAgent


class SimulationEngine:

    def __init__(self, agents: list[EmployeeAgent]):
        self.agents = agents
        self.clock = SimulationClock()
        self.logger = EventLogger()

    def run(self) -> EventLogger:
        total_hours = settings.SIMULATION_DAYS * 24
        for _ in range(total_hours):
            is_work = self.clock.is_work_hours
            for agent in self.agents:
                agent.increment_risk()
                if is_work:
                    self._run_work_hour(agent)
                else:
                    self.logger.log(
                        self.clock, agent,
                        session=0,
                        behavior="IDLE",
                        duration_seconds=settings.SECONDS_PER_HOUR,
                    )

            self.clock.advance(step=settings.SECONDS_PER_HOUR)

        return self.logger

    def _run_work_hour(self, agent: EmployeeAgent):
        for session_num in range(1, agent.sessions_this_hour() + 1):
            for behavior, email, duration in agent.run_email_session():
                self.logger.log(
                    self.clock, agent,
                    session=session_num,
                    behavior=behavior,
                    duration_seconds=duration,
                    email=email,
                )
                self.clock.advance(step=duration)

            # one new email drips into the inbox between sessions
            agent.emailbox.receive_new_emails(count=1)
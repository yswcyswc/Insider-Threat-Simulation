"""
simulation/engine.py — the main simulation loop.

Each tick (= 1 hour):
  1. Every agent gains risk.
  2. If work hours → run email sessions and log each state.
  3. If off hours  → log IDLE.
"""

from simulation.clock import SimulationClock
from simulation.logger import EventLogger
from agent import EmployeeAgent


class SimulationEngine:

    def __init__(self, agents: list[EmployeeAgent]):
        self.agents = agents
        self.clock = SimulationClock()
        self.logger = EventLogger()

    def run(self) -> EventLogger:
        while not self.clock.finished:
            for agent in self.agents:
                agent.increment_risk()

                if self.clock.is_work_hours:
                    for session_num in range(1, agent.sessions_this_hour() + 1):
                        for state in agent.run_email_session():
                            self.logger.log(self.clock, agent, session_num, state)
                else:
                    self.logger.log(self.clock, agent, 0, "IDLE")

            self.clock.advance()

        return self.logger

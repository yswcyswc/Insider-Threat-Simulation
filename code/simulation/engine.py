"""
simulation/engine.py — the main simulation loop.

Each tick (= 1 second):
  1. The engine invokes every agent once at the current clock tick.
  2. Agents manage their own behavior queues and timers.
  3. The shared clock advances by one second after all agents have stepped.
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
                agent.step(self.clock, self.logger)

            self.clock.advance()

        return self.logger

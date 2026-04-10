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
        self.agent_lookup = {agent.agent_id: agent for agent in agents}
        self.clock = SimulationClock()
        self.logger = EventLogger()

    def _recipient_agent_id(self, artifact):
        if getattr(artifact, "channel", "") == "email":
            recipient = getattr(artifact, "recipient", "")
            if recipient.endswith("@company.com"):
                return recipient.removesuffix("@company.com")
            return None
        if getattr(artifact, "channel", "") == "messenger":
            return getattr(artifact, "recipient", "") or None
        return None

    def _deliver_artifact(self, artifact):
        recipient_id = self._recipient_agent_id(artifact)
        if not recipient_id:
            return

        recipient = self.agent_lookup.get(recipient_id)
        if recipient is None:
            return

        recipient.receive_artifact(artifact)

    def run(self) -> EventLogger:
        while not self.clock.finished:
            outgoing = []
            for agent in self.agents:
                artifact = agent.step(self.clock, self.logger)
                if artifact is not None:
                    outgoing.append(artifact)

            for artifact in outgoing:
                self._deliver_artifact(artifact)

            self.clock.advance()

        return self.logger

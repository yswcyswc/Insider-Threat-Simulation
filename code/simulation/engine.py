"""
simulation/engine.py
Main simulation loop.

Each tick:
  1. For every agent: increment risk score (regardless of work/off hours).
  2. If work hours: run email sessions and log each step.
  3. If off hours: log INACTIVE_OFF_HOURS (no email activity).

Suspicious branches in the email chain are silently locked when
agent.threshold_crossed is False — no special handling needed here,
the agent itself manages that via _get_transitions().
"""

from simulation.clock  import SimulationClock
from simulation.logger import EventLogger
from agent.employee    import EmployeeAgent
from config            import settings


class SimulationEngine:

    def __init__(self, agents: list[EmployeeAgent]):
        self.agents = agents
        self.clock  = SimulationClock()
        self.logger = EventLogger()

    def run(self) -> EventLogger:
        print(f"Simulation started  |  agents={len(self.agents)}  "
              f"days={settings.SIMULATION_DAYS}  "
              f"threshold={settings.SUSPICIOUS_THRESHOLD}")

        while not self.clock.finished:
            snap = self.clock.snapshot()
            for agent in self.agents:
                agent.increment_risk()
                if snap["is_work_hours"]:
                    self._work_tick(agent, snap)
                else:
                    self.logger.log(snap, agent,
                                    session_id=0, chain_step=0,
                                    behavior="INACTIVE_OFF_HOURS",
                                    suspicious=False)
            self.clock.advance()

        print("Simulation complete.")
        return self.logger

    def _work_tick(self, agent: EmployeeAgent, snap: dict) -> None:
        n = agent.sessions_this_hour()
        if n == 0:
            self.logger.log(snap, agent,
                            session_id=0, chain_step=0,
                            behavior="IDLE", suspicious=False)
            return
        for s in range(1, n + 1):
            for step_idx, step in enumerate(agent.run_email_chain()):
                self.logger.log(snap, agent,
                                session_id=s,
                                chain_step=step_idx,
                                behavior=step["state"],
                                suspicious=step["suspicious"])

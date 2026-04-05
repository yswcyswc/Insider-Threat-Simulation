"""
simulation/engine.py — the main simulation loop.

Each tick (= 1 second):
  1. At the top of each hour, every agent gains risk and gets a fresh plan.
  2. Each agent counts down their current activity timer independently.
  3. When a timer reaches zero, that agent switches to the next activity.
"""

from collections import deque

from config import settings
from simulation.clock import SimulationClock
from simulation.logger import EventLogger
from agent import EmployeeAgent


class SimulationEngine:

    def __init__(self, agents: list[EmployeeAgent]):
        self.agents = agents
        self.clock = SimulationClock()
        self.logger = EventLogger()
        self.agent_states = {
            agent.agent_id: {"queue": deque(), "remaining": 0}
            for agent in agents
        }

    def run(self) -> EventLogger:
        while not self.clock.finished:
            if self.clock.minute == 0 and self.clock.second == 0:
                self._plan_current_hour()

            for agent in self.agents:
                self._run_tick(agent)

            self.clock.advance()

        return self.logger

    def _plan_current_hour(self):
        is_work = self.clock.is_work_hours
        for agent in self.agents:
            agent.increment_risk()
            hour_plan = self._build_work_hour_plan(agent) if is_work else [
                (0, "IDLE", settings.SECONDS_PER_HOUR, None)
            ]
            self.agent_states[agent.agent_id] = {
                "queue": deque(hour_plan),
                "remaining": 0,
            }

    def _build_work_hour_plan(self, agent: EmployeeAgent):
        hour_plan = []
        remaining = settings.SECONDS_PER_HOUR
        session_num = 1

        while remaining > 0:
            session_events = agent.run_email_session()
            for behavior, email, duration in session_events:
                if remaining <= 0:
                    break

                actual_duration = min(duration, remaining)
                hour_plan.append((session_num, behavior, actual_duration, email))
                remaining -= actual_duration

            agent.emailbox.receive_new_emails(count=1)
            session_num += 1

        return hour_plan

    def _run_tick(self, agent: EmployeeAgent):
        state = self.agent_states[agent.agent_id]

        while state["remaining"] == 0 and state["queue"]:
            session_num, behavior, duration, email = state["queue"].popleft()
            if duration <= 0:
                continue

            self.logger.log(
                self.clock, agent,
                session=session_num,
                behavior=behavior,
                duration_seconds=duration,
                email=email,
            )
            state["remaining"] = duration

        if state["remaining"] > 0:
            state["remaining"] -= 1

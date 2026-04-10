import csv
import random
from config import settings
from agent import EmployeeAgent
from simulation import SimulationEngine

def load_employees(path=settings.EMPLOYEE_CSV) -> list[tuple[str, str]]:
    rows = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            rows.append((row["name"].strip(), row["profile"].strip()))
    return rows

def build_agents(master_rng: random.Random) -> list[EmployeeAgent]:
    agents = []
    for name, profile in load_employees():
        rng = random.Random(master_rng.randint(0, 2**31))
        agents.append(EmployeeAgent(name, profile, rng))
    return agents


def main():
    master_rng = random.Random(settings.RANDOM_SEED)
    agents = build_agents(master_rng)
    engine = SimulationEngine(agents)
    logger = engine.run()
    csv_path = logger.to_csv()
    summary = logger.summary()

    print(f"\n{'Agent':<14} {'Profile':<12} {'Final Risk':>10}  {'Inbox':>6}  {'Suspicious?':>12}")
    print("-" * 62)
    for a in agents:
        flag = "YES" if a.is_suspicious else "no"
        print(f"  {a.agent_id:<12} {a.profile:<12} {a.risk_score:>10.1f}"
              f"  {a.emailbox.inbox_size:>6}  {flag:>12}")
    print(f"\nTotal events logged : {summary['total_events']:,}")
    print(f"Flagged events      : {summary['flagged_events']:,}")
    print(f"CSV saved to        : {csv_path}")


if __name__ == "__main__":
    main()

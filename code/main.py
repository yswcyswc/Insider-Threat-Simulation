import csv
import random
from config import settings
from agent import EmployeeAgent
from simulation import SimulationEngine

def load_relationships(path) -> dict[str, set[str]]:
    graph: dict[str, set[str]] = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            source = row["source"].strip()
            target = row["target"].strip()
            if not source or not target:
                continue
            graph.setdefault(source, set()).add(target)
            graph.setdefault(target, set()).add(source)
    return graph

def load_employees(path=settings.EMPLOYEE_CSV) -> list[dict]:
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(
                {
                    "name": row["name"].strip(),
                    "profile": row["profile"].strip(),
                    "email_weight": float(row["email_weight"]),
                    "messenger_weight": float(row["messenger_weight"]),
                }
            )
    return rows

def build_agents(master_rng: random.Random) -> list[EmployeeAgent]:
    agents = []
    formal_graph = load_relationships(settings.FORMAL_RELATIONSHIPS_CSV)
    informal_graph = load_relationships(settings.INFORMAL_RELATIONSHIPS_CSV)

    for row in load_employees():
        rng = random.Random(master_rng.randint(0, 2**31))
        agents.append(
            EmployeeAgent(
                row["name"],
                row["profile"],
                rng,
                row["email_weight"],
                row["messenger_weight"],
                formal_graph.get(row["name"], set()),
                informal_graph.get(row["name"], set()),
            )
        )
    return agents


def main():
    master_rng = random.Random(settings.RANDOM_SEED)
    agents = build_agents(master_rng)
    engine = SimulationEngine(agents)
    logger = engine.run()
    csv_path = logger.to_csv()
    summary = logger.summary()

    print(
        f"\n{'Agent':<14} {'Profile':<12} {'Final Risk':>10}  "
        f"{'Email':>6}  {'Msgs':>6}  {'Suspicious?':>12}"
    )
    print("-" * 76)
    for a in agents:
        flag = "YES" if a.is_suspicious else "no"
        print(
            f"  {a.agent_id:<12} {a.profile:<12} {a.risk_score:>10.1f}"
            f"  {a.emailbox.inbox_size:>6}  {a.messengerbox.inbox_size:>6}  {flag:>12}"
        )
    print(f"\nTotal events logged : {summary['total_events']:,}")
    print(f"Flagged events      : {summary['flagged_events']:,}")
    print(f"CSV saved to        : {csv_path}")


if __name__ == "__main__":
    main()

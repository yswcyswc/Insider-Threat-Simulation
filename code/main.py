"""
main.py — run with: python main.py
"""
import csv
import random
from config import settings
from agent import EmployeeAgent
from simulation import SimulationEngine


# __ Population ___________________________________________
# (name, profile)
# profiles: "normal" | "stressed" | "malicious"

def load_employees(path=settings.EMPLOYEE_CSV) -> list[tuple[str, str]]:
    """
    Read employees.csv → list of (name, profile) tuples.

    CSV format (header required):
        name,profile
        Snoopy,normal
        Jake,malicious
    """
    rows = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            rows.append((row["name"].strip(), row["profile"].strip()))
    return rows

# POPULATION = [
#     ("Snoopy", "normal"),
#     ("Woodstock", "normal"),
#     ("Charlie", "normal"),
#     ("Lucy", "normal"),
#     ("Linus", "stressed"),
#     ("Cathy", "stressed"),
#     ("Jake", "malicious"),
#     ("Freya", "malicious"),
#     ("Schroeder", "normal"),
#     ("PigMarciepen", "normal"),
# ]


# POPULATION = [
#         ("Snoopy", "low", "low", "novice", "low", 2),
#         ("Woodstock", "low", "low", "novice", "low", 2),
#         ("Charlie",  "low", "low", "advanced", "medium", 2),
#         ("Lucy", "low", "low", "advanced", "medium", 2),
#         ("Linus", "medium", "high", "advanced", "medium", 2),
#         ("Cathy", "medium", "high", "novice", "low", 2),
#         ("Jake", "high", "high", "advanced", "high", 3),
#         ("Freya", "high", "high", "administrator", "high", 3),
#         ("Schroeder", "high", "medium", "advanced", "high", 3),
#         ("Pigpen", "low", "low", "novice", "low", 2),
#     ]

def build_agents(master_rng: random.Random) -> list[EmployeeAgent]:
    agents = []
    for name, profile in load_employees():
        rng = random.Random(master_rng.randint(0, 2**31))
        agents.append(EmployeeAgent(name, profile, rng))
    return agents


def main():
    master_rng = random.Random(settings.RANDOM_SEED)
    agents = build_agents(master_rng)

    # __ Run ______________________________________________
    engine = SimulationEngine(agents)
    logger = engine.run()

    # __ Results __________________________________________
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

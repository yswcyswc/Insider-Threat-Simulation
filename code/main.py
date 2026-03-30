"""
main.py — run with: python main.py
"""

import random
from config import settings
from agent import EmployeeAgent
from simulation import SimulationEngine


# __ Population ___________________________________________
# (name, profile)
# profiles: "normal" | "stressed" | "malicious"


POPULATION = [
    ("Snoopy", "normal"),
    ("Woodstock", "normal"),
    ("Charlie", "normal"),
    ("Lucy", "normal"),
    ("Linus", "stressed"),
    ("Cathy", "stressed"),
    ("Jake", "malicious"),
    ("Freya", "malicious"),
    ("Schroeder", "normal"),
    ("PigMarciepen", "normal"),
]

'''
POPULATION = [
        ("Snoopy", "low", "low", "novice", "low", 2),
        ("Woodstock", "low", "low", "novice", "low", 2),
        ("Charlie",  "low", "low", "advanced", "medium", 2),
        ("Lucy", "low", "low", "advanced", "medium", 2),
        ("Linus", "medium", "high", "advanced", "medium", 2),
        ("Cathy", "medium", "high", "novice", "low", 2),
        ("Jake", "high", "high", "advanced", "high", 3),
        ("Freya", "high", "high", "administrator", "high", 3),
        ("Schroeder", "high", "medium", "advanced", "high", 3),
        ("Pigpen", "low", "low", "novice", "low", 2),
    ]
'''
def build_agents(master_rng: random.Random) -> list[EmployeeAgent]:
    agents = []
    for name, profile in POPULATION:
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

    print(f"\n{'Agent':<12} {'Profile':<12} {'Final Risk':>10}  {'Suspicious?':>12}")
    print("-" * 52)
    for a in agents:
        flag = "YES" if a.is_suspicious else "no"
        print(f"  {a.agent_id:<10} {a.profile:<12} {a.risk_score:>10.1f}  {flag:>12}")
        '''
        print(f"\n{'Agent':<12} {'Predisposition':<16} {'Stress':<8} {'Role':<15} {'Sophistication':<16} {'Risk':>6}  {'Suspicious?':>12}")
        print("-" * 90)
        for a in agents:
            flag = "YES" if a.is_suspicious else "no"
            print(f"  {a.name:<10} {a.predisposition:<16} {a.stress:<8} {a.role:<15} {a.sophistication:<16} {a.risk:>6}  {flag:>12}")
        '''
    print(f"\nTotal events logged : {summary['total_events']:,}")
    print(f"Flagged events      : {summary['flagged_events']:,}")
    print(f"CSV saved to        : {csv_path}")


if __name__ == "__main__":
    main()

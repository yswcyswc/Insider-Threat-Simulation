"""
main.py — run with: python main.py
"""

import random
from config import settings
from agent import EmployeeAgent
from simulation import SimulationEngine


# ── Population ───────────────────────────────────────────
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


def build_agents(master_rng: random.Random) -> list[EmployeeAgent]:
    agents = []
    for name, profile in POPULATION:
        rng = random.Random(master_rng.randint(0, 2**31))
        agents.append(EmployeeAgent(name, profile, rng))
    return agents


def main():
    master_rng = random.Random(settings.RANDOM_SEED)
    agents = build_agents(master_rng)

    # ── Run ──────────────────────────────────────────────
    engine = SimulationEngine(agents)
    logger = engine.run()

    # ── Results ──────────────────────────────────────────
    csv_path = logger.to_csv()
    summary = logger.summary()

    print(f"\n{'Agent':<12} {'Profile':<12} {'Final Risk':>10}  {'Suspicious?':>12}")
    print("-" * 52)
    for a in agents:
        flag = "YES" if a.is_suspicious else "no"
        print(f"  {a.agent_id:<10} {a.profile:<12} {a.risk_score:>10.1f}  {flag:>12}")

    print(f"\nTotal events logged : {summary['total_events']:,}")
    print(f"Flagged events      : {summary['flagged_events']:,}")
    print(f"CSV saved to        : {csv_path}")


if __name__ == "__main__":
    main()

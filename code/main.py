"""
main.py
Run with: python main.py
Output:   output/simulation_log.csv
"""

import random
import pprint
from config     import settings
from agent      import EmployeeAgent
from simulation import SimulationEngine


# 10 employees: name → profile
POPULATION = [
    ("alice",   "normal_employee"),
    ("bob",     "normal_employee"),
    ("carol",   "normal_employee"),
    ("dave",    "developer"),
    ("eve",     "developer"),
    ("frank",   "normal_employee"),
    ("grace",   "stressed_employee"),
    ("henry",   "stressed_employee"),
    ("ivan",    "malicious_insider"),
    ("julia",   "malicious_insider"),
]


def build_agents(master_rng: random.Random) -> list[EmployeeAgent]:
    agents = []
    for agent_id, profile in POPULATION:
        rng = random.Random(master_rng.randint(0, 2**31))
        agents.append(EmployeeAgent(agent_id, profile, rng))
    return agents


def main():
    master_rng = random.Random(settings.RANDOM_SEED)
    agents     = build_agents(master_rng)

    print(f"\n{'Agent':<10} {'Profile':<22} {'Threshold':>10}")
    print("-" * 46)
    for a in agents:
        print(f"{a.agent_id:<10} {a.profile_name:<22} "
              f"{settings.SUSPICIOUS_THRESHOLD:>10}")

    print(f"\nWork hours : {settings.WORK_HOURS_START:02d}:00 – "
          f"{settings.WORK_HOURS_END:02d}:00")
    print(f"Risk unlocks suspicious pathway at score >= "
          f"{settings.SUSPICIOUS_THRESHOLD}\n")

    engine = SimulationEngine(agents)
    logger = engine.run()

    csv_path = logger.to_csv()
    print(f"\nDataset  →  {csv_path}")
    print(f"Rows     :  {len(logger.rows):,}")

    summary = logger.summary()
    print(f"\nSuspicious events : "
          f"{summary['suspicious_events']} / {summary['total_events']}")

    print(f"\n{'Profile':<22} {'Total':>8} {'Suspicious':>11} {'%':>6}")
    print("-" * 50)
    for profile, s in summary["by_profile"].items():
        pct = s["suspicious"] / s["total"] * 100 if s["total"] else 0
        print(f"{profile:<22} {s['total']:>8,} {s['suspicious']:>11,} "
              f"{pct:>5.1f}%")

    print("\nAgent final risk scores:")
    for a in agents:
        status = "UNLOCKED" if a.threshold_crossed else "locked  "
        print(f"  {a.agent_id:<10} risk={a.risk_score:>5.1f}  [{status}]")

    print(f"\nFirst 10 work-hours rows:")
    work = [r for r in logger.rows
            if r["period"] == "work_hours" and r["behavior"] != "IDLE"][:10]
    for r in work:
        flag = " <-- SUSPICIOUS" if r["suspicious"] else ""
        print(f"  tick={r['tick']:>3}  {r['time_label']}  "
              f"{r['agent_id']:<10} risk={r['risk_score']:>5.1f}  "
              f"unlocked={str(r['threshold_crossed']):<5}  "
              f"{r['behavior']}{flag}")


if __name__ == "__main__":
    main()

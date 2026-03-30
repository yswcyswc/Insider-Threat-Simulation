# Email ABM — Insider Threat Simulation

Models employee email behaviour as a discrete-time agent-based simulation
based on Kandias et al. (2010). Each agent accumulates a risk score every
tick. Suspicious email actions are locked until the score crosses a threshold.

## Structure

```
InsiderThreatSim/
├── main.py                    entry point, defines the population
├── config/settings.py         all parameters and probabilities
├── agent/employee.py          EmployeeAgent — email chain + risk score
├── simulation/
│   ├── clock.py               tick / work-hours logic
│   ├── engine.py              main loop
│   └── logger.py              event collection + CSV writer
└── output/simulation_log.csv
```

## Run

```bash
python main.py
```

Pure Python 3.10+, no dependencies.

## Output columns

| Column            | Description                                     |
|-------------------|-------------------------------------------------|
| tick              | Global tick (1 tick = 1 hour)                   |
| day               | Simulation day                                  |
| hour              | Hour of day (0–23)                              |
| time_label        | Human readable e.g. Day 01  09:00               |
| period            | work or off                                     |
| agent_id          | Agent name                                      |
| profile           | normal / stressed / malicious                   |
| risk_score        | Accumulated risk at time of event               |
| is_suspicious     | True once risk >= SUSPICIOUS_THRESHOLD          |
| session           | Email session index within the tick             |
| behavior          | State name e.g. READ_EMAIL, FWD_EXTERNAL        |
| flagged           | True if this state is a suspicious action       |

## How risk and the threshold work

Every tick, each agent's risk score increases by a fixed amount set per
profile in settings.py. While risk is below SUSPICIOUS_THRESHOLD the
agent follows NORMAL_TRANSITIONS only — suspicious states are unreachable.
Once the threshold is crossed, SUSPICIOUS_TRANSITIONS activates and states
like FWD_EXTERNAL and LEAK_ATTACH become possible.

## How the email chain works

Each work-hour session is a random walk through email states starting at
OPEN_CLIENT and ending at DONE. At each step the agent picks the next state
by sampling from the current transition row. If the agent has crossed the
threshold, the SUSPICIOUS_TRANSITIONS table overrides the normal one for
certain states. States listed in SUSPICIOUS_STATES are flagged in the output.

## Profiles

| Profile   | Risk per tick | Sessions per hour |
|-----------|--------------|-------------------|
| normal    | 0.5          | 2                 |
| stressed  | 1.5          | 2                 |
| malicious | 2.5          | 3                 |

Normal agents never cross the threshold over a 5-day run. Stressed agents
cross it around day 3. Malicious agents cross it earliest and generate the
most flagged events.

## Tuning

All parameters are in config/settings.py: work hours, simulation days,
threshold, risk increments per profile, transition probabilities, and the
set of flagged states. The population is defined in main.py.
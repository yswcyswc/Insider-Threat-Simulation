# Email ABM — Insider Threat Simulation

Models employee email behaviour as a discrete-time agent-based simulation.
Each agent accumulates a risk score every tick. Suspicious email actions are
locked until the score crosses a threshold.

## Structure

```
email_abm/
├── main.py                  entry point
├── config/settings.py       all parameters and probabilities
├── agent/employee.py        EmployeeAgent — state machine + risk score
├── simulation/
│   ├── clock.py             tick / work-hours logic
│   ├── engine.py            main loop
│   └── logger.py            event collection + CSV writer
└── output/simulation_log.csv
```

## Run

```bash
python main.py
```

Pure Python 3.10+, no dependencies.

## Output columns

| Column            | Description                                      |
|-------------------|--------------------------------------------------|
| tick              | Global tick (1 tick = 1 hour)                    |
| day               | Simulation day                                   |
| hour              | Hour of day (0-23)                               |
| time_label        | Human readable e.g. Day 01  09:00                |
| period            | work_hours or off_hours                          |
| agent_id          | Agent name                                       |
| profile           | normal_employee / developer / etc.               |
| risk_score        | Accumulated risk at time of event                |
| threshold_crossed | True once risk >= SUSPICIOUS_THRESHOLD           |
| session_id        | Email session index within the tick              |
| chain_step        | Step within the session                          |
| behavior          | State name e.g. READ_EMAIL, FWD_EXTERNAL         |
| suspicious        | True if this is a flagged action                 |

## How the threshold works

Every tick, each agent's risk score increases by RISK_INCREMENT (set per
profile in settings.py). While risk_score < SUSPICIOUS_THRESHOLD the
suspicious transitions in SUSPICIOUS_TRANSITIONS are simply not available
— the agent follows NORMAL_TRANSITIONS only. Once the threshold is crossed,
the override rows activate and suspicious behaviours become possible.

## Tuning

All knobs are in config/settings.py: work hours, simulation days, threshold
value, risk increments, transition probabilities, and session frequency.

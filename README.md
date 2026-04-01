# Email ABM — Insider Threat Simulation

Models employee email behaviour as a **second-based, action-driven agent-based simulation**.
Each agent owns an inbox (`EmailBox`), processes emails over time, and accumulates risk.
Suspicious actions emerge probabilistically once risk crosses a threshold.


## Structure

```
InsiderThreatSim/
├── main.py                      entry point, loads employees from CSV
├── config/settings.py           all parameters (timing, risk, probabilities)
├── data/
│   ├── employees.csv            agent definitions
│   ├── email_senders.csv        sender pools by category
│   └── email_subjects.csv       subject pools by category
├── agent/
│   └── employee.py              EmployeeAgent — risk + action selection
├── environment/
│   ├── email.py                 Email object definition
│   └── emailbox.py              EmailBox — inbox + email actions
├── simulation/
│   ├── clock.py                 second-based clock
│   ├── engine.py                main loop (duration-driven)
│   └── logger.py                event collection + CSV writer
└── output/simulation_log.csv
```


## Run

```
python main.py
```


## Core Model Changes

- 1 tick = 1 second
- Simulation advances by action duration
- Email behavior is action-based, not session-based
- Inbox is an explicit entity (EmailBox)
- All data comes from CSV files


## Output columns

| Column            | Description                                      |
|-------------------|--------------------------------------------------|
| tick              | Global time (seconds)                            |
| day               | Simulation day                                   |
| hour              | Hour of day                                      |
| minute            | Minute of hour                                   |
| second            | Second of minute                                 |
| period            | work or off                                      |
| agent_id          | Agent name                                       |
| profile           | normal / stressed / malicious                    |
| risk_score        | Accumulated risk at time of event                |
| is_suspicious     | True once risk >= SUSPICIOUS_THRESHOLD           |
| behavior          | Action taken                                     |
| duration_seconds  | Time consumed by this action                     |
| email_id          | Email involved                                   |
| email_category    | normal / phishing / malicious                    |
| flagged           | True if action is suspicious                     |


## How time works

- Simulation runs in seconds
- Each action consumes a fixed duration
- Clock advances by that duration
- Work hours are enforced based on time-of-day


## How email behavior works

- read_email() pops from inbox
- write_email(), reply_email(), forward_email() create emails
- delete_email() removes emails
- receive_new_emails() injects new emails

Email content is generated from CSV pools by category.

---

## How risk works

- Risk increases continuously over time
- Below threshold → normal behavior
- Above threshold → higher probability of suspicious actions

Suspicious actions:
- CLICK_LINK
- FWD_EXTERNAL
- LEAK_ATTACH
- SEARCH_SENSITIVE


## Profiles

| Profile   | Risk rate | Behavior tendency            |
|-----------|----------|------------------------------|
| normal    | low      | mostly safe actions          |
| stressed  | medium   | more risky actions           |
| malicious | high     | frequent attacks             |


## Tuning

All parameters in config/settings.py:
- simulation duration
- work hours
- risk rates
- action durations
- email category weights
- inbox sizes

Data-driven:
- employees.csv
- email_senders.csv
- email_subjects.csv

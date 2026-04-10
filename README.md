# Email + Messenger ABM - Insider Threat Simulation

Models employee communication behavior as a second-based, action-driven agent-based simulation.
Each agent owns an email inbox (`EmailBox`) and a chat queue (`MessengerBox`), processes communications over time, and accumulates risk.
Each employee also has a per-person email vs. messenger distribution, and communication is constrained by formal and informal relationship networks.
Suspicious actions emerge probabilistically once risk crosses a threshold.

## Structure

```text
InsiderThreatSim/
+-- code/
|   +-- main.py                      entry point
|   +-- visualize_log.py             HTML viewer for simulation_log.csv
|   +-- config/settings.py           loads runtime configuration
|   +-- data/
|   |   +-- employees.csv            agent definitions
|   |   +-- action_definitions.csv   action durations and flags by profile
|   |   +-- formal_relationships.csv formal email network
|   |   +-- informal_relationships.csv informal messenger network
|   |   +-- email_senders.csv        sender pools by category
|   |   +-- email_subjects.csv       subject pools by category
|   |   +-- message_senders.csv      messenger sender pools by category
|   |   +-- message_bodies.csv       messenger body pools by category
|   +-- agent/
|   |   +-- employee.py              EmployeeAgent logic
|   +-- environment/
|   |   +-- email.py                 Email object definition
|   |   +-- emailbox.py              inbox and email actions
|   |   +-- messenger.py             Messenger object definition
|   |   +-- messengerbox.py          chat queue and messenger actions
|   +-- simulation/
|   |   +-- clock.py                 second-based clock
|   |   +-- engine.py                main loop
|   |   +-- logger.py                event collection and CSV writer
|   +-- output/
|       +-- simulation_log.csv
|       +-- simulation_timeline.html
+-- README.md
```

## Run

```powershell
python code/main.py
python code/visualize_log.py
```

The first command regenerates `simulation_log.csv`.
The second command turns that CSV into an easier-to-read HTML timeline.

## Core Model

- 1 tick = 1 second
- Simulation advances by action duration
- Email behavior is action-based, not session-based
- Inbox is an explicit entity (`EmailBox`)
- Employee and action settings come from CSV files

## Output Columns

| Column | Description |
|---|---|
| tick | Global time in seconds |
| day | Simulation day |
| hour | Hour of day |
| minute | Minute of hour |
| second | Second of minute |
| period | `work` or `off` |
| agent_id | Agent name |
| profile | `normal`, `stressed`, or `malicious` |
| risk_score | Accumulated risk at time of event |
| is_suspicious | `True` once risk is above the threshold |
| session | Session number within the current work period |
| behavior | Action taken |
| duration_seconds | Time consumed by this action |
| channel | `email` or `messenger` when an artifact is involved |
| artifact_kind | `email` or `message` |
| artifact_id | Communication artifact involved, if any |
| artifact_category | Artifact type, if the action touched one |
| flagged | `True` if the action is suspicious |

## How Time Works

- Simulation runs in seconds
- Each action consumes a random duration sampled from a CSV-defined range
- The clock advances by that action duration
- Work hours are enforced based on time of day

## How Communication Behavior Works

- `read_email()` pops one email from the inbox
- `write_email()`, `reply_email()`, and `forward_email()` create new outgoing emails
- `delete_email()` removes one email
- `receive_new_emails()` injects new emails into the inbox
- `read_message()` pops one chat message from the queue
- `send_message()` and `reply_message()` create outgoing chat messages
- `delete_message()` removes one chat message
- `receive_new_messages()` injects new chat messages into the queue

Email and messenger content are generated from CSV pools by category.

<!-- ## Why Some Rows Have `,,,`

Some actions are not tied to one specific email object.

Examples:
- `OPEN_CLIENT`
- `VIEW_INBOX`
- `SEARCH`
- `IDLE`

Those actions still get logged, but there is no single communication object to store in the artifact columns.
That is why rows like these are normal:

```csv
129284,2,11,54,44,work,Schroeder,normal,5.6,False,2,OPEN_CLIENT,35,,,False
129319,2,11,55,19,work,Schroeder,normal,5.6,False,2,VIEW_INBOX,96,,,False
```

By contrast, actions like `READ_EMAIL`, `DELETE`, `REPLY`, `FORWARD`, `READ_MESSAGE`, and `SEND_MESSAGE` usually do involve a communication object, so those rows usually contain values for the artifact columns. -->

## How Risk Works

- Risk increases continuously over time and decreases during off-work hours
- Below threshold -> normal behavior
- Above threshold -> higher probability of suspicious actions

Suspicious actions:
- `CLICK_LINK`
- `FWD_EXTERNAL`
- `LEAK_ATTACH`
- `SEARCH_SENSITIVE`

## Profiles

| Profile | Risk rate | Behavior tendency |
|---|---|---|
| normal | low | mostly safe actions |
| stressed | medium | more risky actions |
| malicious | high | frequent attacks |

## Tuning

Code-level settings in `code/config/settings.py` include:
- simulation duration
- work hours
- risk rates
- session counts per hour
- email category weights
- inbox sizes

Data-driven files in `code/data/` include:
- `employees.csv`
- `action_definitions.csv`
- `formal_relationships.csv`
- `informal_relationships.csv`
- `email_senders.csv`
- `email_subjects.csv`
- `message_senders.csv`
- `message_bodies.csv`

`action_definitions.csv` controls:
- which actions exist for each profile
- minimum and maximum duration for each action
- which actions are suspicious
- which actions should scale with email category 

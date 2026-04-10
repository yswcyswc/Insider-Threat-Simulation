Some thoughts in case i forget

Structure

- main.py creates employees from CSV data and runs the simulation  
- The simulation loop lives in engine.py  
- Each employee is an EmployeeAgent in employee.py  
- Each employee owns an EmailBox in emailbox.py, which creates and manipulates Email objects from email.py  
- Every logged event is written by logger.py to code/output/simulation_log.csv  
- visualize_log.py turns that CSV into simulation_timeline.html  


Bugs

Original problem

The engine directly controlled employee behavior  
It would process one employee’s actions, then another’s  
Time advanced while processing those actions  
Then, at the end of the loop, an extra hour was added again  

Caused 2 problems

- Employees were not truly acting at the same time  
- If employee A spent several minutes doing things, employee B had to wait for A to finish before acting  
- Time was being advanced twice  
  - Once through action durations  
  - Then again through a fixed hourly jump  


The exact buggy code

```python
def _run_work_hour(self, agent: EmployeeAgent):
    for session_num in range(1, agent.sessions_this_hour() + 1):
        for behavior, email, duration in agent.run_email_session():
            self.logger.log(...)
            self.clock.advance(step=duration)
```

After this, I added another full hour, time was also being incremented in a fixed chunk after those actions, which made the clock jump abnormally


- Now the engine is small  
- Every loop iteration is one second  
- Every agent gets a step(...) call  
- Then the shared clock advances by one second  


Employee agent

- Each employee agent maintains its own local state:
  - current communication state
  - current action countdown
  - active communication object
  - risk / stress state
  - formal and informal relationship neighborhoods
  - email vs messenger preference weights
- The agent is updated once per simulation tick (1 second).
- When the countdown for the current action reaches zero, the agent samples its next action based on:
  - current communication channel context
  - unread inbox / chat state
  - stochastic transition rules
  - profile-dependent action durations
  - current risk state

Per-tick action logic

- If the agent is currently busy, decrement the action countdown by one second.
- If the countdown reaches zero:
  - determine the next communication context (email or messenger)
  - evaluate the current state transition rule
  - sample the next action stochastically
  - sample the action duration
  - assign the sampled duration as the new countdown
  - log the action start

Communication workflow

- Communication behavior is modeled as a stochastic state machine.
- At each decision point, the next state is sampled from a transition table conditioned on:
  - current state
  - employee risk condition
  - communication channel
- Once an action is selected, its duration is sampled from a profile-specific range.
- The selected action remains active until its countdown expires.


Risks

- increment_risk() during work hours  
- recover_risk() during non-work hours  


buggy parts: 

- DONE: maybe it would be a good idea to remove preplanned hour-long behaviour queues entirely and move everything into per-tick inside `EmployeeAgent.step()`
- NO LONGER ISSUE: right now agents often follow a sampled plan for a while, which makes them less reactive than they should be
- a newly received item should be able to change near-future behavior right away:
    - open messenger because a message arrived
    - reply soon after reading
    - switch from email to messenger because the inbox/chat state changed
    - prioritize unread real interpersonal communication over ambient/generated traffic
- current communication is only partially interpersonal:
    - an employee can send a real message/email to another employee
    - but the recipient does not strongly react to that event yet

some ideas:

- use relationship weights?
    - not just whether an edge exists, but how likely one employee is to contact another
    - stronger ties should produce more frequent communication
- add a small “just received item” bias
    - if an employee just received a message, increase chance of opening messenger soon
    - if they just read a message from a close contact, increase chance of reply
- add a urgency / attention model
    - unread interpersonal communication should temporarily raise the probability of checking that channel
Some thoughts in case i forget

Structure

- main.py creates employees from CSV data and runs the simulation  
- The simulation loop lives in engine.py  
- Each employee is an EmployeeAgent in employee.py  
- Each employee owns an EmailBox in emailbox.py, which creates and manipulates Email objects from email.py  
- Every logged event is written by logger.py to code/output/simulation_log.csv  
- visualize_log.py turns that CSV into simulation_timeline.html  


Update 4/9

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

After this, I added another full hour  


Changes for 4/10 Meeting

- Now the engine is intentionally very small  
- Every loop iteration is one second  
- Every agent gets a step(...) call  
- Then the shared clock advances by one second  


Employee agent

- Plan entire hour: only triggered at the start of each hour  
- Store plan in a queue  
- Execute it second-by-second  


Every hour

- while remaining time in hour:  
  - generate one email session  
  - break it into actions  
  - append to plan  
  - reduce remaining time  
  - inject new emails  

run_email_session()  # state machine, state transition chain + durations  

- while state != "DONE":  
  - behavior, email = perform(state)  
  - duration = sample_duration(...)  
  - next state = stochastic transition from the table  


Risks

- increment_risk() during work hours  
- recover_risk() during non-work hours  


buggy parts: 

- maybe it would be a good idea to remove preplanned hour-long behaviour queues entirely and move everything into per-tick inside `EmployeeAgent.step()`
- right now agents often follow a sampled plan for a while, which makes them less reactive than they should be
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
- reduce planning horizon
    - instead of planning a whole hour, maybe plan one action at a time or a few actions ahead
    - this keeps duration-based actions but allows better responsiveness
# Simple task deliverer

Simple python script delivering tasks to many machines.

# Preparation


- For the main machine, it can **login to all other working machines with**
   **ssh key**.

- **The main machine has enough memory to handle many ssh connections.** i.e. 
   the number of running tasks and number of threads to check working machine 
   availability.

- **The codes and datas are placed to all working machines, and the sent**
   **command can run properly on any working machine.** It is recommended to 
   use NAS to handle all codes and datas. Make some tests before sending real 
   tasks. 

- **When the task has many output, make sure it won't exceed the maximum** 
   **reading or writing speed of the hardware.** e.g., if your task writes logs
   10MB/s, when 20 tasks simultaneously writes to a same disk, all of them will
   spend many time waiting for write datas. This happens commonly when all
   tasks write datas to one NAS. 

- **When workers are new machines,** e.g. deploy many workers on cloud
   services, `ssh` may show warning about unknown key fingerprints. In this
   situation, please change TODO to true in config to add
   `StrictHostKeyChecking=no` when using `ssh`. **When IPs may re-use,** `ssh`
   will show `REMOTE HOST IDENTIFICATION HAS CHANGED` warning, please softlink 
   `/dev/null` to `~/.ssh/known_hosts` to replace it.

# Designed pipeline

- Use `ping` `ssh` `ps aux` and `nvidia-smi` to search running tasks, as well 
  as the availabitity of working machines.
- Use user-defined task generation class to get tasks.
- Based on availability, send tasks to working machines with `ssh`, and save 
  outputs to result folder. For every sent task, a prefix like `SENDTASK1_1=`
  will be added.
- Check availability and send tasks recursively, until all tasks are sent. 
- Maybe a tool to maintianance running tasks and re-run failed tasks.

# TODOs

1. [X] For every task, add prefix to identify it. 
2. [X] Support run several tasks on one machine.
3. [X] For GPU tasks, use `nvidia-smi` to check GPU status with current 
       running status to determine availability.
4. [X] Easy way to specify IPs of working machines.  
       *improve it, set different work threads on different hardware.*
5. [ ] A simple way to kill all/specified working tasks.
6. [ ] Avoid override existing logs, show important informarion before 
       running.
7. [ ] Pause running.
8. [ ] Check failed tasks, skip exist tasks.

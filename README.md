# Simple task deliverer

Simple python script delivering tasks to many machines. May only support linux.

# Preparation

1．For the main machine, it can login to all other working machines with ssh
   key.
2. The main machine has enough memory to handle many ssh connections, i.e. the 
   number of running tasks and number of threads to check working machine 
   availability.
3. The codes and datas are placed to all working machines, and the sent command
   can run properly on any working machine. It is recommended to use NAS to 
   handle all codes and datas. Make some tests before sending a lot of tasks. 
4. When the task has many output, make sure it won't exceed the maximum reading
   or writing speed of the hardware. e.g., if your task writes logs 10MB/s,
   when 20 tasks simultaneously writes to a same disk, all of them will spend
   lots of time waiting for write datas. This happens commonly when all tasks
   write datas to one NAS. 
5. NEW MACHINE

# Expected pipeline

- Use `ssh` and `ps aux` and search prefixes to identify running tasks and 
  availabitity of working machines.
- Parse task configuration file to get tasks.
- Based on availability, send tasks to working machines with ssh, and save 
  outputs to result folder. For every sent task, a prefix like `SENDTASK1_1=`
  will be added.
- Check availability recursively, until all task are sent. 

# TODOs

1. [ ] For every task, add prefix to identify it. 
2. [ ] Support run several tasks on one machine.
3. [ ] For GPU tasks, use `nvidia-smi` to check GPU status with current 
       running status to determine availability.
4. [ ] Easy way to specify IPs of working machines.
5. [ ] A simple way to kill all/specified working tasks.
6. [ ] Avoid override existing logs, show important informarion before 
       running.

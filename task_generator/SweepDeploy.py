import time
import os

from .TaskGeneratorBase import TaskGeneratorBase
from utils import get_real_path

class SweepDeploy(TaskGeneratorBase):
    def __init__(self, sweep_name: str, prepare_command: str,
                 **kwargs):
        """
        Deploy wandb sweep task. When it is started, infinite task number is
        generated, and log file name is 
        `sweep_{timestamp}_{host}-{gpuid}-{thread}.log`.

        sweep_name: sweep full name of wandb
        prepare_command:  commands that run before running sweep, e.g., go 
            to specified folder, acticvate venv. You can input multiple 
            commands and split them with `;`, like bash.
            DO NOT SET CUDA_VISIBLE_DEVICES here, it will be controlled by 
            the code.
        **kwargs: not-used arguments.
        """
        self.sweep = sweep_name
        self.p_cmd = prepare_command.strip()
        # remove semicolon
        while self.p_cmd[-1] == ';':
            self.p_cmd = self.p_cmd[:-1]

    def make_command(self, IP, device, threadnumber):
        """
        return command to run on slave. %GPUID will be replaced with GPU 
        number in get_next_command. (if CPU-only, it will be ',')
        """
        cmd = (
            self.p_cmd
            + '; export CUDA_VISIBLE_DEVICES=%GPUID; '
            + f' export TASK_DELIVER_HINT={IP}_{device}_{threadnumber}; '
            + 'wandb agent ' + self.sweep
        )
        return cmd

    def make_logname(self):
        """
        log file name, %SLAVE will be replaced by machine hostname or IP in 
        get_next_command.
        """
        return f'sweep_{int(time.time())}_%SLAVE.log'

    def __len__(self):
        return 99999999

    def get_next_command(self, prefix, IP, device, threadnumber):
        """
        generate full command to run in slave. In this function, final command
        and logname is generated based on metadatas.

        prefix: prefix added to SSH command that is used to distinguish whether
            a worker is working.
        IP: hostname or IP of slave.
        device: device string to run the command of slave.
        threadnumber: thread number of commands that run on the save slave
            and device.
        """
        while True:
            cmd = self.make_command(IP, device, threadnumber)
            logname = self.make_logname()
            logname = logname.replace(
                '%SLAVE', '-'.join((str(IP), str(device), str(threadnumber))))
            if device == 'X':
                device = ','
            cmd = cmd.replace('%GPUID', str(device))
            return cmd, logname
        raise StopIteration


import os

from .TaskGeneratorBase import TaskGeneratorBase
from utils import get_real_path

class KDD24Train(TaskGeneratorBase):
    def __init__(self, config_list, train_number,
                 code_folder, log_folder, config_folder,
                 **kwargs):
        """
        config_list: txt file that contains config yaml names, one per line.
        train_number: how many number for one config need to train
        code_folder:
        log_folder: absolute folder name to save logs that printed to terminal
            during ssh. 
        config_folder: absolute folder name where the config.yml for task
            generator is saved.
        pytorch_thread_num: if is 0, set pytorch thread automatically. 
            Otherwise, set pytorch thread with specified number. Mainly
            used in full-CPU machines, as sometimes it will not fully use all
            threads automatically. (TODO: currently not available)
        **kwargs: not-used arguments.
        """
        self.config_folder = config_folder
        self.c = self.read_config(self.get_real_path(config_list))
        self.tn = train_number
        self.codef = self.get_real_path(code_folder)
        # self.pytorch_thread_num = pytorch_thread_num
        self.existing_logs = self.update_existing_logs(
            self.get_real_path(log_folder))
        # print(self.existing_logs)
        self.check_exist()
        self.tasks = []
        self.now = 0
        for i in range(train_number):
            for c in self.c:
                tx = self.make_tx(c, i)
                if tx in self.existing_logs:
                    continue
                print(f'{tx} not found, pending.')
                cmd = self.make_command(c, tx)
                logname = self.make_logname(tx)
                self.tasks.append([cmd, logname])

    def get_real_path(self, unk_path):
        return get_real_path(unk_path, self.config_folder)

    @staticmethod
    def update_existing_logs(log_folder):
        if not os.path.exists(log_folder):
            return set()
        files = os.listdir(log_folder)
        return set(['_'.join(x.split('_')[:-1])
                    for x in files if x[-4:] == '.log'])

    def read_config(self, fname):
        """
        read config_list, and remove appending .yml
        """
        res = [x.replace('.yml', '')
               for x in open(fname).read().strip().split('\n')]
        # filename should not be same
        res_filename = set(map(lambda x: x.split('/')[-1], res))
        assert len(res_filename) == len(res), 'some files have same name!'
        # res = [x for x in res if 'ppr200' not in x]  # filter ppr200 for now
        return res

    def check_exist(self):
        """
        check if config is exist
        """
        cf_path = os.path.join(self.codef, 'config')
        for c in self.c:
            assert isinstance(c, str)
            if not os.path.exists(os.path.join(cf_path, c) + '.yml'):
                print('config %s not exist' % c)
                raise ValueError

    def make_tx(self, config, index):
        """
        make tensorboard-name for this config
        """
        config = config.split('/')[-1]
        return f'{config}_{index}'

    def make_command(self, config, tx):
        """
        return command to run on slave. %GPUID will be replaced with GPU 
        number in get_next_command. (if CPU-only, it will be ',')
        """
        cmd = (
            '. ~/.bash_profile; '
            '. ~/environment/KDD24/bin/activate; '
            f'cd {self.codef}; '
            # 'CUDA_LAUNCH_BLOCKING=1 '
            'WANDB_MODE=offline '
            f'python -u main.py '
            f'--config=config/{config}.yml '
            '-g=%GPUID '
            '-- '
            f'name=\\"{tx}\\" '
        )
        return cmd

    def make_logname(self, tx):
        """
        log file name, %SLAVE will be replaced by machine hostname or IP in 
        get_next_command.
        """
        return tx + '_%SLAVE.log'

    def __len__(self):
        return len(self.tasks)

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
        while len(self.tasks) > self.now:
            cmd, logname = self.tasks[self.now]
            logname = logname.replace(
                '%SLAVE', '-'.join((str(IP), str(device), str(threadnumber))))
            if device == 'X':
                device = ','
            cmd = cmd.replace('%GPUID', str(device))
            self.now += 1
            return cmd, logname
        raise StopIteration


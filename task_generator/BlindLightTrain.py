import os

from .TaskGeneratorBase import TaskGeneratorBase
from utils import get_real_path

class BlindLightTrain(TaskGeneratorBase):
    def __init__(self, cityflow_config_list, config_list, train_number,
                 code_folder, log_folder, config_folder,
                 pytorch_thread_num = 0, **kwargs):
        self.config_folder = config_folder
        self.cc = self.read_config(self.get_real_path(cityflow_config_list))
        self.c = self.read_config(self.get_real_path(config_list))
        self.tn = train_number
        self.codef = self.get_real_path(code_folder)
        self.pytorch_thread_num = pytorch_thread_num
        self.existing_logs = self.update_existing_logs(
            self.get_real_path(log_folder))
        # print(self.existing_logs)
        self.check_exist()
        self.tasks = []
        self.now = 0
        for i in range(train_number):
            for c1 in self.c:
                for c2 in self.cc:
                    blind = ''
                    if not isinstance(c1, str):
                        blind = c1[1]
                        c1 = c1[0]
                    if not isinstance(c2, str):
                        blind = c2[1]
                        c2 = c2[0]
                    tx = self.make_tx(c1, c2, blind, i)
                    if tx in self.existing_logs:
                        # print(f'{tx} exist, skip!')
                        continue
                    print(f'{tx} not found, pending.')
                    cmd = self.make_command(c1, c2, blind, tx)
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
        res = [x.replace('.yml', '')
               for x in open(fname).read().strip().split('\n')]
        for i in res:
            assert (' ' in res[0]) == (' ' in i)
        if ' ' in res[0]:
            res = [x.split(' ') for x in res]
            assert set(map(len, res)) == set([2])
        return res

    def check_exist(self):
        cf = os.listdir(os.path.join(self.codef, 'configs/main'))
        ccf = os.listdir(os.path.join(self.codef, 'configs/cityflow'))
        flag = False
        for c in self.c:
            if not isinstance(c, str):
                c = c[0]  # has blind param, get config name
            if c + '.yml' not in cf:
                print('config %s not exist' % c)
                flag = True
        for c in self.cc:
            if not isinstance(c, str):
                c = c[0]  # has blind param, get config name
            if c + '.yml' not in ccf:
                print('cityflow-config %s not exist' % c)
                flag = True
        if flag:
            raise ValueError

    def make_tx(self, config, cfconfig, blind, index):
        if blind != '':
            return f'{config}_{cfconfig}_{blind}_{index}'
        return f'{config}_{cfconfig}_{index}'

    def make_command(self, config, cfconfig, blind, tx):
        cmd = (
            # download code from cos
            'coscli cp cos://tits/BL.7z /BL.7z; '
            # extract and copy to codef
            'cd /; '
            '7z x BL.7z; '
            f'rm -r {self.codef}; '
            f'mv BlindLight {self.codef}; '
            # go to codef
            f'cd {self.codef}; '
            # 'CUDA_LAUNCH_BLOCKING=1 '
            'SUMO_HOME=/usr/share/sumo '
            f'python -u main.py '
            f'--config configs/main/{config}.yml '
            f'--cityflow-config configs/cityflow/{cfconfig}.yml '
            f'-tx \\"{tx}\\" '
            '-g %s '
            # '--cityflow-config-modify SAVEREPLAY=False '
            '--cityflow-config-modify REPLAY_ONLY_KEEP_LAST=True '
            # '--cityflow-replay-only-evaluate '
            f'--enable-wandb '
            f'--note \\"{config}_{cfconfig}_{blind}\\" '
            f'--note2 \\"{config}\\" '
            f'--note3 \\"{cfconfig}\\" '
            f'--note4 \\"{blind}\\" '
            f'--note5 \\"{tx[-1]}\\" '  # run idx
            # test configs
            '--dqn-replay-size 80 --n-frames 360 --evaluate-round 1 '
            # '-rmf '
            '; '
            # after run, zip results
            f'7z a -m0=lzma2 "{config}_{cfconfig}_{blind}_{tx[-1]}.7z" logs results wandb; '
            f'coscli cp "{config}_{cfconfig}_{blind}_{tx[-1]}.7z" cos://tits/results/ '
        )
        if self.pytorch_thread_num > 0:
            cmd += f'--pytorch-threads {self.pytorch_thread_num} '
        if blind != '':
            cmd += f'--cityflow-config-modify \\"BLIND={blind}\\" '
        return cmd

    def make_logname(self, tx):
        return tx + '_%s.log'

    def __len__(self):
        return len(self.tasks)

    def get_next_command(self, prefix, IP, device, threadnumber):
        while len(self.tasks) > self.now:
            res = self.tasks[self.now]
            res[1] = res[1] % '-'.join((str(IP), str(device), str(threadnumber)))
            # res[1] = res[1] % prefix.replace('_', '')
            if device == 'X':
                device = ','
            res[0] = res[0] % device
            self.now += 1
            return res
        raise StopIteration


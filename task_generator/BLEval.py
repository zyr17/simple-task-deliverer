import os

from .TaskGeneratorBase import TaskGeneratorBase
from utils import get_real_path

class BLEval(TaskGeneratorBase):
    def __init__(self, exist_log_folder,
                 code_folder, log_folder, config_folder, **kwargs):
        self.config_folder = config_folder
        self.codef = self.get_real_path(code_folder)
        self.tasks = []
        self.now = 0
        self.exist_log_folder = exist_log_folder
        self.existing_logs = self.update_existing_logs(
            self.get_real_path(log_folder))
        elogs = [x for x in os.listdir(exist_log_folder) if x[-4:] == '.log']
        for i in elogs:
            pref = '_'.join(i.split('_')[:-1])
            if pref in self.existing_logs:
                # print(f'{tx} exist, skip!')
                continue
            print(f'{pref} not found, pending.')
            cmd = self.make_command(exist_log_folder, i)
            logname = self.make_logname(pref)
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

#     def read_config(self, fname):
#         res = [x.replace('.yml', '')
#                for x in open(fname).read().strip().split('\n')]
#         for i in res:
#             assert (' ' in res[0]) == (' ' in i)
#         if ' ' in res[0]:
#             res = [x.split(' ') for x in res]
#             assert set(map(len, res)) == set([2])
#         return res
# 
#     def check_exist(self):
#         cf = os.listdir(os.path.join(self.codef, 'configs/main'))
#         ccf = os.listdir(os.path.join(self.codef, 'configs/cityflow'))
#         flag = False
#         for c in self.c:
#             if not isinstance(c, str):
#                 c = c[0]  # has blind param, get config name
#             if c + '.yml' not in cf:
#                 print('config %s not exist' % c)
#                 flag = True
#         for c in self.cc:
#             if not isinstance(c, str):
#                 c = c[0]  # has blind param, get config name
#             if c + '.yml' not in ccf:
#                 print('cityflow-config %s not exist' % c)
#                 flag = True
#         if flag:
#             raise ValueError
# 
#     def make_tx(self, config, cfconfig, blind, index):
#         if blind != '':
#             return f'{config}_{cfconfig}_{blind}_{index}'
#         return f'{config}_{cfconfig}_{index}'

    def make_command(self, elfolder, i):
        cmd = (
            '. ~/environment/cityflow/bin/activate; '
            f'cd {self.codef}; '
            # 'CUDA_LAUNCH_BLOCKING=1 '
            'SUMO_HOME=/usr/share/sumo '
            f'python -u eval.py '
            f'{elfolder}/{i} '
            '-g %s '
        )
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


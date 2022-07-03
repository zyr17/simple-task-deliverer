import os

from .TaskGeneratorBase import TaskGeneratorBase

class BlindLightTrain(TaskGeneratorBase):
    def __init__(self, cityflow_config_list, config_list, train_number, 
                 code_folder, log_folder, **kwargs):
        self.cc = self.read_config(cityflow_config_list)
        self.c = self.read_config(config_list)
        self.tn = train_number
        self.codef = code_folder
        self.existing_logs = self.update_existing_logs(log_folder)
        print(self.existing_logs)
        self.check_exist()
        self.tasks = []
        self.now = 0
        for c1 in self.c:
            for c2 in self.cc:
                blind = ''
                if not isinstance(c1, str):
                    blind = c1[1]
                    c1 = c1[0]
                if not isinstance(c2, str):
                    blind = c2[1]
                    c2 = c2[0]
                for i in range(train_number):
                    tx = self.make_tx(c1, c2, blind, i)
                    if tx in self.existing_logs:
                        print(f'{tx} exist, skip!')
                        continue
                    cmd = self.make_command(c1, c2, blind, tx)
                    logname = self.make_logname(tx)
                    self.tasks.append([cmd, logname])
    
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
        return f'{config}_{cfconfig}_{blind}_{index}'

    def make_command(self, config, cfconfig, blind, tx):
        return (
                '. ~/environment/cityflow/bin/activate; '
                f'cd {self.codef}; '
                # 'CUDA_LAUNCH_BLOCKING=1 '
                f'python -u main.py '
                f'--config configs/main/{config}.yml '
                f'--cityflow-config configs/cityflow/{cfconfig}.yml '
                f'-tx \\"{tx}\\" '
                '-g %s '
                '--cityflow-config-modify SAVEREPLAY=False '
                f'--cityflow-config-modify \\"BLIND={blind}\\" '
                f'--enable-wandb '
                # '--dqn-replay-size 80 '
                # '-rmf '
        )

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

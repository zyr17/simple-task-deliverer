import os

from .TaskGeneratorBase import TaskGeneratorBase

class MultiTSCTest(TaskGeneratorBase):
    def __init__(self, test_log_folder, test_log_file_folder, code_folder, 
                 log_folder, **kwargs):
        raise NotImplementedError("some path should relative to config file, not check compability!")
        self.codef = code_folder
        self.test_logs = self.update_test_logs(test_log_folder, 
                                               test_log_file_folder)
        self.existing_logs = self.update_existing_logs(log_folder)
        # print(self.existing_logs)
        self.tasks = []
        self.now = 0
        for log in self.test_logs:
            tx = self.make_tx(log)
            if tx in self.existing_logs:
                print(f'{tx} exist, skip!')
                continue
            cmd = self.make_command(log)
            logname = self.make_logname(tx)
            self.tasks.append([cmd, logname])

    @staticmethod
    def update_config_path(logfolder, command):
        # return command
        for num in range(len(command)):
            if command[num] == '--config':
                command[num + 1] = command[num + 1].replace(
                    'configs/main/',
                    f'{logfolder}/input_files/configs/'
                )
                return command
        assert 0, '--config not found'

    def update_test_logs(self, test_log_folder, test_log_file_folder):
        logfolders = os.listdir(test_log_folder) 
        # print(logfolders)
        if not os.path.exists(test_log_file_folder):
            return set()
        logfiles = [x for x in os.listdir(test_log_file_folder)
                    if x[-4:] == '.log']
        logfiles.sort()
        res = []
        for logfile in logfiles:
            lines = open(test_log_file_folder + '/' + logfile).readlines(10000)
            logline = [x for x in lines if 'log folder' in x]
            assert len(logline) == 1, (logfile, logline)
            logfolder = logline[0].strip().split('/')[-2]
            command = [x for x in lines if 'command:' in x]
            assert len(command) == 1, command
            command = eval(command[0][16:])
            if logfolder not in logfolders:
                print(f'{logfolder} not found in test_log_folder!')
                continue
            logfolder = test_log_folder + '/' + logfolder
            command = self.update_config_path(logfolder, command)
            res.append([logfolder, command])
        return res
    
    @staticmethod
    def update_existing_logs(log_folder):
        if not os.path.exists(log_folder):
            return set()
        files = os.listdir(log_folder)
        return set(['_'.join(x.split('_')[:-1]) 
                    for x in files if x[-4:] == '.log'])

    def make_tx(self, log):
        for cmd, cmd1 in zip(log[1][:-1], log[1][1:]):
            if cmd == '-tx':
                return cmd1
        assert 0, log

    def make_command(self, log):
        return (
                # f'. ~/environment/cityflow/bin/activate; '
                f'cd {self.codef}; '
                # f'CUDA_LAUNCH_BLOCKING=1 '
                f'python -u {" ".join(log[1])} '
                f'--test-round 10 '
                f'--preload-model-file {log[0]}/models/best.pt '
                # f'-rmf '
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
            # res[0] = res[0] % device  # now no need to use gpu
            self.now += 1
            return res
        raise StopIteration

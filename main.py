#!/usr/bin/env python3

import os
import sys
import time
import re
import yaml

from get_worker_status import get_worker_status, output_status
from task_generator import *
from utils import get_configs, gen_cmd_prefix

default_config = 'config.yml'
if os.path.exists(default_config):
    default_config = get_configs(default_config)
else:
    default_config = {}
    raise ValueError('default config file config.yml not exist!')

config_path = 'config.yml'
if len(sys.argv) > 1:
    config_path = sys.argv[1]
    if config_path[0] != '/':
        config_path = './' + config_path  # not start with /, a relative path
    if os.path.isdir(config_path):
        # input folder, use config.yml in folder as config
        config_path = f'{config_path}/config.yml'
config_folder = os.path.abspath(os.path.dirname(config_path))
configs = default_config.copy()
configs.update(get_configs(config_path))

def main():
    taskgen = globals()[configs['task_generator']](
        config_folder = config_folder, **configs
    )
    print('Task number:', len(taskgen))
    logf = configs['log_folder']
    if logf[0] != '/':
        # if not start with /, treat as relative folder to config path
        logf = f'{config_folder}/{logf}'
        configs['log_folder'] = logf
    if not os.path.exists(logf):
        print('log folder not exist, create it.')
        os.system(f'mkdir "{logf}" -p')
    # if len(os.listdir(logf)) > 0:
    #     print('log folder not empty! press enter to continue '
    #           'or ctrl-c to exit.')
    #     try:
    #         input()
    #     except KeyboardInterrupt:
    #         exit()
    status_list = []
    total_number = len(taskgen)
    time_wait = 1
    for i in range(total_number):
        while len(status_list) == 0:
            print(f'available worker not found, will get status in {time_wait}s')
            time.sleep(time_wait)  # sleep 15s to wait command sent successfuly
            time_wait = 15
            status_list = get_status()
            if len(status_list) > 0:
                IP_maxlen = max([len(x[0]) for x in status_list])
            else:
                time.sleep(configs['sleep_after_status'])
        prefix = gen_cmd_prefix(configs['command_prefix'], *status_list[0][1:])
        cmd, logf = taskgen.get_next_command(prefix, *status_list[0])
        logf = os.path.join(configs['log_folder'], logf)
        send_task(prefix, *status_list[0], cmd, logf)
        print(task_send_notify(i, total_number, *status_list[0], IP_maxlen))
        status_list = status_list[1:]
        # sleep after send one task to avoid reach rate limit
        time.sleep(configs['sleep_after_task'])

def task_send_notify(now, total_number, IP, device, thread, IP_maxlen = 0):
    res = (f'Task {"%3d" % now}/{total_number} sent to '
           f'{"%%-%ds" % IP_maxlen % IP} '
           f'{"CPU  " if device == "X" else "GPU " + str(device)} '
           f'thread {thread}'
          )
    return res

"""get thread status by get_worker_status, keep available worker threads.
    Return: [[IP, device, thread_number], ... ]
"""
def get_status():
    print('try to get worker status ...')
    R = get_worker_status(**configs)
    if configs['verbose']:
        output_status(R)
    res = []
    for ip in R:
        for device in R[ip]:
            for thread, status in enumerate(R[ip][device]):
                if status == 'A':
                    res.append([ip, device, thread])
    if len(res) == 0 and configs['testmode']:
        print('now in test mode, create not exist machines to send tasks')
        res = [['0.0.0.0', 'X', 0]] * 1000
    print(f'available worker thread(s): {len(res)}')
    return res

def send_task(prefix, IP, device, thread_number, cmd, logfile):
    username = configs['ssh_username']
    port = configs['ssh_port']
    final_cmd = (f'ssh {username}{"@" if username else ""}{IP} -p {port} '
                 # add sleep and colon to avoid cmd disappear before cmd done running,
                 # and make sure last data has written to the log file.
                 f'"{prefix}=; {cmd}; sleep 10s; :;" '
                 f' > "{logfile}" 2>&1 &'
                )
    if configs['remote_save_log']:
        final_cmd = (
            f'ssh {username}{"@" if username else ""}{IP} -p {port} '
            f''' " nohup bash -c ' {prefix}=; {cmd} ' > '{logfile}' 2>&1 < /dev/null & "'''
        )
    if configs['verbose'] or configs['testmode']:
        print(final_cmd)
    if not configs['testmode']:
            os.system(final_cmd)

"""

# train args
cityflow_config_list = 'cityflow_config_list.txt'
config_list = 'config_list.txt'
log_folder = 'LCLogs/'
train_number = 4

# test args
test_list_file = 'test_log_list.txt'
# test_log_folder = code_folder + '/results/SYN_test/'
test_log_folder = code_folder + '/results/early_retest/tested/shanghai_vol'
test_target_folder = ''

# common setting
run_and_shutdown = False # deprecated, now spare machines will be shutdown
shutdown_suffix = ' && shutdown now' if run_and_shutdown else ''

def count_status(status):
    r = {'A': 0, 'B': 0, 'S': 0, 'D': 0}
    for ip, s in status:
        r[s] += 1
    print(' --- Now status: Avaliable=%d, Busy=%d, Self=%d, Dead=%d --- '
          % (r['A'], r['B'], r['S'], r['D']))

last_available = []
def get_next_available():
    global last_available
    while len(last_available) == 0:
        time.sleep(5) # sleep a while to make sure sended tasks has started
        status = get_status()
        count_status(status)
        for ip, s in status:
            if s == 'A':
                last_available.append(ip)
    choose = last_available[0]
    last_available = last_available[1:]
    return choose

def make_command_train(config, cityflow_config, tx):
    return ('cd ' + code_folder + '; '
            'python -u main.py --config configs/main/%s.yml '
                              '--cityflow-config configs/cityflow/%s.yml '
                              '-tx %s'
            '%s') % (config, cityflow_config, tx, shutdown_suffix)

def make_command_test(logname):
    logs = open(logname).readlines()
    logfolder = ''
    for l in logs:
        if 'log folder:' in l:
            logfolder = re.search(r'log folder: (.+)$', l).group(1)
            break
    if logfolder == '':
        print('ERROR! cant find log folder in', logname)
        return 'echo ERROR'
    return ('cd ' + code_folder + '; '
            'python -u main.py --config %s/input_files/configs/*.yml '
                '--cityflow-config %s/input_files/cityflow-config.yml '
                '--preload-model-file %s/models/best.pt '
                #'--dqn-hidden-size 256 '
                "-tx '' -rmf --test-round 10"
            '%s') % (logfolder, logfolder, logfolder, shutdown_suffix)

def make_tx(config, cityflow_config, index):
    return config + '_' + cityflow_config + '_' + str(index)

def check_exist(configs, cityflow_configs):
    cf = os.listdir(code_folder + '/configs/main')
    ccf = os.listdir(code_folder + '/configs/cityflow')
    flag = False
    for c in configs:
        if c + '.yml' not in cf:
            print('config %s not exist' % c)
            flag = True
    for c in cityflow_configs:
        if c + '.yml' not in ccf:
            print('cityflow-config %s not exist' % c)
            flag = True
    if flag:
        raise ValueError

def read_config(cfile, ccfile):
    return [open(cfile).read().strip().split('\n'),
            open(ccfile).read().strip().split('\n')]

def train_main(argv):
    cf, ccf = read_config(config_list, cityflow_config_list)
    check_exist(cf, ccf)
    task_number = len(cf) * len(ccf) * train_number
    print('estimated number', task_number)
    now_number = 0
    if not os.path.exists(log_folder):
        os.mkdir(log_folder)
    for c1 in cf:
        for c2 in ccf:
            for i in range(train_number):
                tx = make_tx(c1, c2, i)
                cmd = make_command_train(c1, c2, tx)
                print(cmd)
                IP = get_next_available()
                logfile = '%s/%s_%s.log' % (log_folder, tx, IP.split('.')[-1])
                send_task(IP, cmd, logfile)
                now_number += 1

def test_main(argv):
    log_folder = test_log_folder
    global test_target_folder
    if os.path.exists(test_list_file):
        test_list = open(test_list_file)
    else:
        test_list = [x for x in os.listdir(log_folder) if x[-4:] == '.log'
                                                       and 'test' not in x]
    print('test number:', len(test_list))
    is_move = False
    if test_target_folder == '':
        test_target_folder = log_folder + '/tested'
        is_move = True
    if not os.path.exists(test_target_folder):
        os.mkdir(test_target_folder)
    now_number = 0
    for log in test_list:
        ori_log = log
        log = '_'.join(log.split('_')[:-1])
        cmd = make_command_test(log_folder + '/' + ori_log)
        print(cmd)
        IP = get_next_available()
        if is_move:
            logfile = '%s/%s_test%s.log' % (log_folder, log, IP.split('.')[-1])
            send_task(IP, cmd, logfile)
            os.system('mv %s/%s %s' % (log_folder, ori_log,
                                       test_target_folder))
        else:
            logfile = '%s/%s_test%s.log' % (test_target_folder,
                                            log, IP.split('.')[-1])
            send_task(IP, cmd, logfile)
        now_number += 1
"""

if __name__ == '__main__':
    #print(get_status())
    #send_task('192.168.1.251', 'cd ' + code_folder + '; ls', 'running_log/1.log')
    main()


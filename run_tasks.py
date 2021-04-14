#!/usr/bin/python3

import os 
import sys
import maintain_status
import time
import re
from IP import available_ip_pool, ip_prefix, self_ip, parallel_num

TASK_IS = 'train'
code_folder = '/app/MultiTSC/'
# code_folder = '/app/MM/MultiTSC/'

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

def main():
    if TASK_IS.lower() == 'test':
        test_main(sys.argv)
    elif TASK_IS.lower() == 'train':
        train_main(sys.argv)

def get_status():
    R = maintain_status.main(ip_prefix, available_ip_pool, self_ip, 
                             parallel_num)
    st, ed = available_ip_pool
    res = []
    for ip in ip_prefix:
        r = R[:ed - st + 1]
        R = R[ed - st + 1:]
        for i, c in zip(range(st, ed + 1), r):
            res.append([ip + str(i), c])
    return res

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

def send_task(target_ip, cmd, logfile):
    final_cmd = 'ssh %s "RUN_TASK=1; %s" > %s 2>&1 &' % (target_ip, cmd, logfile)
    print(final_cmd)
    #final_cmd = 'ssh %s "sleep 15s && echo python main.py" > %s 2>&1 &' % (target_ip, logfile)
    os.system(final_cmd)

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

if __name__ == '__main__':
    #print(get_status())
    #send_task('192.168.1.251', 'cd ' + code_folder + '; ls', 'running_log/1.log')
    main()

#!/usr/bin/python3

import os
import sys
import re
import multiprocessing
import subprocess
import io
from collections import OrderedDict
import re

def get_ip(ip):
    res = []
    if '[' in ip and ']' in ip:
        r = re.match(r'(.*?)\[(\d+)-(\d+)\](.*)', ip)
        if not r:
            raise ValueError(ip + ' illegal')
        left = r.group(1)
        x = int(r.group(2))
        y = int(r.group(3))
        right = r.group(4)
        for i in range(x, y + 1):
            res += get_ip(left + str(i) + right)
    else:
        res = [ip]
    return res

def gen_lists(inc, exc, tasknum):
    incIP = []
    excIP = []
    for i in inc:
        incIP += get_ip(i)
    for i in exc:
        excIP += get_ip(i)
    IPs = []
    for i in incIP:
        if i not in excIP:
            IPs.append(i)

class Worker(multiprocessing.Process):
    def __init__(self, target_ip, self_ip, pipe):
        super().__init__(daemon = True)
        self.ip = target_ip
        self.self_ip = self_ip
        self.pipe = pipe

    def run(self):
        self.pipe.send(test_one_ip(self.ip, self.self_ip))
        self.pipe.close()

def top_check_usage(target_ip):
    print('warning: no timeout')
    lines = subprocess.Popen('ssh -o ConnectTimeout=1 %s '
                             'top -b -w 512 -d 1 -n 5' % target_ip, 
                             shell = True, 
                             stdout = subprocess.PIPE,
                             stderr = subprocess.DEVNULL,
                             bufsize = -1)
    lines.wait()
    lines = io.TextIOWrapper(lines.stdout)
    lines = str(lines.read()).split('\n')
    cpu_loads = [float(x[8:14].strip()) for x in lines 
                                        if x[:4] == '%Cpu'][1:]
    mem_loads = [float(re.search(r'(\d+\.\d) used', x).group(1)) 
                    for x in lines if x[:7] == 'MiB Mem'][1:]
    if len(cpu_loads) == 0:
        return 'D' # dead
    if sum(cpu_loads) / len(cpu_loads) > 10:
        return 'B' # busy
    else:
        return 'A' # available

def grep_check_usage(target_ip):
    lines = subprocess.Popen('ssh -o ConnectTimeout=1 %s '
                             'ps aux --cols 999' % target_ip, 
                             shell = True, 
                             stdout = subprocess.PIPE,
                             stderr = subprocess.DEVNULL,
                             bufsize = -1)
    try:
        lines.wait(timeout = 10)
        lines = io.TextIOWrapper(lines.stdout)
        lines = str(lines.read()).split('\n')
        python_main = [x for x in lines if 'RUN_TASK' in x or 'main.py' in x]
        if len(''.join(lines)) == 0:
            return 'D' # dead
        if len(python_main):
            return 'B' # busy
        return 'A' # available
    except subprocess.TimeoutExpired:
        return 'D' # dead

def test_one_ip(target_ip, self_ip):
    if target_ip == self_ip:
        return 'S' # self
    else:
        ping_res = os.popen('ping -c 5 -i 0.2 -w 1 -q ' + target_ip).read()
        ping_res = re.search(r'(\d) received', ping_res)
        if not ping_res or int(ping_res.group(1)) == 0:
            return 'D' # dead
        else:
            return grep_check_usage(target_ip)

"""generate worker IP lists. 
    Args:
        inc: lists of IP strings, for the meaning, please refer to sample 
             config file.
            to describe multiple IPs, use `[a-b]`. for
             example, '192.168.[1-2].[3-8]' contains 12 IPs. if set in ssh 
             file, host names also works, such as 'node[26-29]'.
        dec: lists of IP strings
        tasknum: number of tasks running on one device on one worker.

    Return: OrderedDict{IP: OrderedDict{'-': ['A', 'D'], '0': ['A', 'B']}}
                                        v      v
                                        1      2
            1: '-' means CPU thread availability, others means GPU card 
               availability.
            2: list length equals to tasknum.
               'A' means available, 'D' means dead, 'B' means busy.
"""
def main(ip_prefix, available_ip_pool, self_ip, parallel_num = 128, 
            lock = False):

    if not isinstance(ip_prefix, str):
        allres = []
        for ip in ip_prefix:
            res = main(ip, available_ip_pool, self_ip, parallel_num, lock)
            allres += res
        return allres

    res = []
    
    if lock:
        os.system('touch /app/.status.lock')

    st, ed = available_ip_pool

    workers, send, recv = [], [], []
    for i in range(st, ed + 1):
        target_ip = ip_prefix + str(i)
        s, r = multiprocessing.Pipe()
        worker = Worker(target_ip, self_ip, s)
        send.append(s)
        recv.append(r)
        workers.append(worker)

    while len(workers) > 0:
        w_now = workers[:parallel_num]
        w_s = send[:parallel_num]
        w_r = recv[:parallel_num]
        for w in w_now:
            w.start()
        for w in w_now:
            w.join()
        for r in w_r:
            res.append(r.recv())
        workers = workers[parallel_num:]
        send = send[parallel_num:]
        recv = recv[parallel_num:]

    if lock:
        os.system('rm /app/.status.lock')

    return res

if __name__ == '__main__':
    from IP import available_ip_pool, ip_prefix, self_ip, parallel_num
    # available_ip_pool = [1, 252] # for [x, y], include x and y
    # ip_prefix = ['192.168.0.', '192.168.1.']
    # self_ip = '192.168.0.158'
    # parallel_num = 128
    res = main(ip_prefix, available_ip_pool, self_ip, parallel_num)
    for i, r in enumerate(res):
        print(i + available_ip_pool[0], r)

#!/usr/bin/env python3

"""generate worker IP lists and get their availability. 
    Args used in config.yml:
        ip_include: lists of IP strings, for the meaning, please refer to sample 
             config file.
            to describe multiple IPs, use `[a-b]`. for
             example, '192.168.[1-2].[3-8]' contains 12 IPs. if set in ssh 
             file, host names also works, such as 'node[26-29]'.
        ip_exclude: lists of IP strings
        parallel_num: thread number when checking availability
        cpu_thread, gpu_thread: how many tasks will run on CPU or GPU
        cmd_prefix: prefix to identify running tasks
        ssh_strict_host_key_checking: for newly deployed machines, ignore the 
            warning thrown by ssh
        ssh_username: when not empty, connect to specified user
        ssh_port: when not empty, connect with specified port
        expected_gpu_memory_usage: check memory usage availability to avoid
            MLE in public machines. 

    Return: OrderedDict{IP: OrderedDict{'X': ['A', 'D'], '0': ['A', 'B100']}}
                                         v     v
                                         1     2
            1: 'X' means CPU thread availability, others means GPU card 
               availability.
            2: list length equals to use_cpu or use_gpu.
               'A' means available, 'D' means dead, 'B100' means busy, and
               task PID is 100. if only 'B', means task PID cannot be
               determined. 
    TODO: some can ping but cannot ssh, may treat as available?
"""
import os
import getpass
import sys
import re
import multiprocessing
import subprocess
import io
from collections import OrderedDict
import re
import yaml
from utils import gen_cmd_prefix, get_configs

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

def gen_ip_lists(inc, exc):
    incIP = []
    excIP = []
    for i in inc:
        incIP += get_ip(i)
    if exc:
        for i in exc:
            excIP += get_ip(i)
    IPs = []
    for i in incIP:
        if i not in excIP:
            IPs.append(i)
    return IPs

class Worker(multiprocessing.Process):
    def __init__(self, ip, pipe, cpu_thread, gpu_thread, command_prefix, 
                 ssh_strict_host_key_checking, ssh_username, ssh_port, 
                 expected_gpu_memory_usage, gpu_check_ignore_users, **kwargs):
        super().__init__(daemon = True)
        self.ip = ip
        self.cpu = cpu_thread
        self.gpu = gpu_thread
        self.prefix = command_prefix
        self.strict = ssh_strict_host_key_checking
        self.username = ssh_username
        self.port = ssh_port
        self.gpumem = expected_gpu_memory_usage
        self.ignoreuser = gpu_check_ignore_users
        self.kwargs = kwargs
        if self.gpumem <= 0:
            self.gpumem = 1
        self.pipe = pipe

    def gen_cmd_prefix(self, device, number):
        return gen_cmd_prefix(self.prefix, device, number)
        return self.prefix + str(device) + '_' + str(number)

    def get_flag(self, is_all_dead, device, number, texts):
        if is_all_dead:
            return 'D' # dead
        prefix = self.gen_cmd_prefix(device, number)
        if prefix + '=' in texts:
            lines = [x for x in texts.split('\n') if prefix + '=' in x]
            for line in lines:
                if not re.search(f'ssh [^=;]*{prefix}=', line):
                    return 'B' # busy
                    # TODO get PID. now can't get PID by ps results.
            return 'A' # all match has ssh before, means it is a host task, 
                       # not a worker task.
        else:
            return 'A' # available

    def ssh_cmd(self, innercmd):
        res = 'ssh -p %d -o ConnectTimeout=1 -o %s %s%s %s' % (
            self.port,
            '' if self.strict else 'StrictHostKeyChecking=no',
            self.username + '@' if len(self.username) else '',
            self.ip, 
            innercmd
        )
        if 'verbose' in self.kwargs and self.kwargs['verbose']:
            print('ssh_cmd', res)
        return res

    def get_gpu_status(self, ps_lines):
        lines = subprocess.Popen(self.ssh_cmd('nvidia-smi'),
                                 shell = True, 
                                 stdout = subprocess.PIPE,
                                 stderr = subprocess.DEVNULL,
                                 bufsize = -1)
        try:
            lines.wait(timeout = 10)
            lines = io.TextIOWrapper(lines.stdout)
            lines = str(lines.read()).split('\n')
        except subprocess.TimeoutExpired:
            return []
        if 'failed' in lines[0]:
            return []
        result = []
        while len(lines) > 0 and '========' not in lines[0]:
            lines = lines[1:]
        if len(lines) == 0:
            return []
        while True:
            line1 = lines[1]
            line2 = lines[2]
            if line1.strip() == '':
                break
            gid = int(line1[1:5].strip())
            muse, mall = [x.strip() for x in line2.split('|')[2].split('/')]
            assert muse[-3:] == mall[-3:] and muse[-3:] == 'MiB'
            result.append([gid, int(mall[:-3]) - int(muse[:-3])])
            lines = lines[1:]
            while '-----' not in lines[0]:
                lines = lines[1:]
        GPUpos = -1
        PIDpos = -1
        while '======' not in lines[0]:
            if '|' in lines[0]:
                line = lines[0].split('|')[1]
                if 'GPU  ' in line:
                    GPUpos = line.index('GPU  ')
                if 'PID' in line:
                    PIDpos = line.index('PID') - 4
            lines = lines[1:]
        assert PIDpos >= 0 and GPUpos >= 0
        ps_lines = [x.strip().split()[:2] for x in ps_lines[1:]]
        ps_lines = {int(x[1]): x[0] for x in ps_lines if len(x) == 2}
        working_name = self.username
        if self.username == '':
            # get current username
            working_name = getpass.getuser()
        for line in lines[1:]:
            if len(line) == 0 or line[0] != '|':
                continue
            if 'No running process' in line:
                continue
            line = line.split('|')[1]
            gid = int(line[GPUpos:GPUpos + 3].strip())
            pid = int(line[PIDpos:PIDpos + 7].strip())
            # print(gid, pid, ps_lines[pid])
            if pid in ps_lines \
                and ps_lines[pid] not in [*self.ignoreuser, working_name]:
                    # other accounts using this card, change mem to 0
                    if 'verbose' in self.kwargs and self.kwargs['verbose']:
                        print(f'PID {"%7d" % pid}, {ps_lines[pid]} is '
                              f'using GPU {gid} on {self.ip}, skip this GPU.')
                    for i in result:
                        if int(i[0]) == gid:
                            i[1] = 0
        return result

    def grep_check_usage(self, is_all_dead):
        lines = subprocess.Popen(self.ssh_cmd('ps aux --cols 999'),
                                 shell = True, 
                                 stdout = subprocess.PIPE,
                                 stderr = subprocess.DEVNULL,
                                 bufsize = -1)
        try:
            out, _ = lines.communicate(timeout = 10)
            lines = out.decode('utf8').split('\n')
        except subprocess.TimeoutExpired:
            print('timeout', self.ip)
            print(io.TextIOWrapper(lines.stdout).read())
            is_all_dead = True
            lines = []
        useful = '\n'.join([x for x in lines if self.prefix in x])
        result = OrderedDict()
        if self.cpu > 0:
            result['X'] = []
        for i in range(self.cpu):
            result['X'].append(self.get_flag(is_all_dead, 'X', i, useful))
        for g, gmem in self.get_gpu_status(lines):
            result[g] = []
            for i in range(min(self.gpu, int(gmem / self.gpumem))):
                result[g].append(self.get_flag(is_all_dead, g, i, useful))
        return result

    def ping_test_one_ip(self):
        ping_res = os.popen('ping -c 5 -i 0.2 -w 1 -q ' + self.ip).read()
        ping_res = re.search(r'(\d) received', ping_res)
        is_all_dead = False
        if not ping_res or int(ping_res.group(1)) == 0:
            is_all_dead = True
        return self.grep_check_usage(is_all_dead)

    def run(self):
        self.pipe.send(self.ping_test_one_ip())
        self.pipe.close()

def get_worker_status(ip_include, ip_exclude, parallel_num, **kwargs):
    
    IPs = gen_ip_lists(ip_include, ip_exclude)

    workers, send, recv = [], [], []
    for ip in IPs:
        s, r = multiprocessing.Pipe()
        worker = Worker(ip, s, **kwargs)
        send.append(s)
        recv.append(r)
        workers.append(worker)

    res = {}

    while len(workers) > 0:
        w_now = workers[:parallel_num]
        w_s = send[:parallel_num]
        w_r = recv[:parallel_num]
        for w in w_now:
            w.start()
        for w in w_now:
            w.join()
        for w, r in zip(w_now, w_r):
            res[w.ip] = r.recv()
        workers = workers[parallel_num:]
        send = send[parallel_num:]
        recv = recv[parallel_num:]

    return res

def output_status(status):
    for k in status:
        print(k + ':')
        for kk in status[k]:
            print('    ' + str(kk) + ': ' + str(status[k][kk]))

if __name__ == '__main__':
    conf = get_configs('config.yml')
    res = get_worker_status(**conf)
    output_status(res)

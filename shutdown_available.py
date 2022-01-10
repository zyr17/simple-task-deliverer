#!/usr/bin/env python3

import os 
import sys
import time

from get_worker_status import get_worker_status
from utils import get_configs

check_times = 5
sleep_time = 20

def get_available():
    res = []
    status = get_worker_status(**get_configs('config.yml'))
    for ip in status:
        flag = True
        for dev in status[ip]:
            for i in status[ip][dev]:
                flag = flag and i == 'A'
        if flag:
            res.append(ip)
    return res

def send_shutdown(ip):
    cmd = 'ssh %s "shutdown now"' % ip
    os.system(cmd)

def shutdown_available():
    os.system("date | tr '\n' ' '")
    print('check round: %d, check interval: %d' % (check_times, sleep_time))
    a = get_available()
    for i in range(1, check_times):
        print('round %d: %d instances always available' % (i, len(a)))
        time.sleep(sleep_time)
        b = get_available()
        c = []
        for ip in a:
            if ip in b:
                c.append(ip)
        a = c
    print('shutdown %d instances' % len(a))
    for ip in a:
        send_shutdown(ip)

if __name__ == '__main__':
    while True:
        shutdown_available()

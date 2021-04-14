#!/usr/bin/python3

import os 
import sys
import maintain_status
import time
from IP import available_ip_pool, ip_prefix, self_ip, parallel_num

check_times = 5
sleep_time = 20

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

def get_available():
    res = []
    status = get_status()
    for ip, s in status:
        if s == 'A':
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
    #print(get_status())
    #send_task('192.168.1.251', 'cd /app/MultiTSC; ls', 'running_log/1.log')
    while True:
        shutdown_available()

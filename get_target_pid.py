#!/usr/bin/env python3

import sys
import yaml
import os


def kill_one(filename):
    assert filename[-4:] == '.log'
    filename = filename[:-4].split('_')[-1].split('-')
    server, gid, thread = filename
    config = yaml.safe_load(open('config.yml'))
    prefix = config['command_prefix']
    port = config.get('ssh_port', 22)
    full_prefix = f'{prefix}{gid}_{thread}'
    ps_res = os.popen(
        f'''ssh {server} -p {port} '''
        f''' 'ps aux | grep "{full_prefix}" | grep -v grep' '''
    ).read().strip()
    pid = ps_res.split()[1]
    cps_res = os.popen(
        f'''ssh {server} -p {port} 'pgrep -P {pid}' ''').read().strip()
    cpid = cps_res
    print(pid, cpid)
    print('sure to kill? (if not, Ctrl+C; otherwise enter)')
    try:
        input()
    except KeyboardInterrupt:
        return
    os.system(
        f'''ssh {server} -p {port} '''
        f''' 'kill -s SIGINT {cpid}' '''
    )
    assert len(sys.argv) > 1

if __name__ == '__main__':
    assert len(sys.argv) > 1
    for filename in sys.argv[1:]:
        print(f'processing file {filename}')
        kill_one(filename)

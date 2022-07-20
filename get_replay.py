#!/usr/bin/env python3

# used for MultiTSC/BlindLight to get wandb, replay and logs of one exp folder

import os
import sys
import yaml

DEBUG = False

if __name__ == '__main__':
    target = sys.argv[1]
    log_save_folder = f'{target}/logs'
    replay_save_folder = f'{target}/replays'
    wandb_save_folder = f'{target}/wandb'
    for i in [log_save_folder, replay_save_folder, wandb_save_folder]:
        if not os.path.exists(i):
            os.mkdir(i)
    logs = os.listdir(target)
    configs = [x for x in logs if '.yml' == x[-4:]]
    assert len(configs) == 1
    configs = configs[0]
    logs = [x for x in logs if x[-4:] == '.log']
    logsf = [
        [y.strip().split(' ')[4] 
         for y in open(f'{target}/{x}').readlines() 
         if 'log folder:' in y][0]
        for x in logs]
    wandbf = [
        [y.strip().split(' ')[-1]
         for y in open(f'{target}/{x}').readlines() 
         if 'wandb id:' in y][0]
        for x in logs]
    # print('\n'.join(logs))
    # print(configs)
    cfolder = yaml.load(open(f'{target}/{configs}'), Loader = yaml.SafeLoader)['code_folder']
    wandb_root = f'{cfolder}/wandb'
    all_wandb = [x for x in os.listdir(wandb_root) if 'offline-' in x]
    wandbf = [[y for y in all_wandb if x in y][0] for x in wandbf]
    failed = []
    for num, [log, logf, wandb] in enumerate(zip(logs, logsf, wandbf)):
        try:
            print(f'{num}/{len(logs)}\r', end = '')
            logroot = f'{cfolder}/{logf}'
            logf = f'{logroot}/test_env'
            for i in range(2):
                # env may crash and have multiple env instance, get maximum id one
                sub = max([int(x) for x in os.listdir(logf)])
                logf = f'{logf}/{sub}'
            replayf = [x for x in os.listdir(logf) if x[:10] == 'replay.txt']
            replayf.sort()
            replayf = f'{logf}/{replayf[-1]}'
            prefix = 'echo ' if DEBUG else ''
            os.system(f'{prefix} cp "{replayf}" "{replay_save_folder}/{log[:-4]}.txt"')
            os.system(f'{prefix} mv "{logroot}" "{log_save_folder}/"')
            os.system(f'{prefix} mv "{wandb_root}/{wandb}" "{wandb_save_folder}/"')
        except Exception as e:
            if DEBUG:
                raise e
            failed.append(log)
    print(f'{len(failed)} failed. {" ".join(failed)}')

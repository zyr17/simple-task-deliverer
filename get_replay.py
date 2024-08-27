#!/usr/bin/env python3


import os
import sys
import yaml

DEBUG = False
COMMAND_MV = 'mv -f'
COMMAND_LN = 'ln -s'
COMMAND = COMMAND_LN

def blindlight(target):
    # used for MultiTSC/BlindLight to get wandb, replay and logs of one exp folder
    log_save_folder = f'{target}/logs'
    replay_save_folder = f'{target}/replays'
    wandb_save_folder = f'{target}/wandb'
    for i in [log_save_folder, replay_save_folder, wandb_save_folder]:
        if not os.path.exists(i):
            try:  # when run on multiple servers, may raise exception
                os.mkdir(i)
            except:
                pass
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
    wandbf = [[y for y in all_wandb if x in y] for x in wandbf]
    failed = []
    for num, [log, logf, wandb] in enumerate(zip(logs, logsf, wandbf)):
        try:
            prefix = 'echo ' if DEBUG else ''
            print(f'{num}/{len(logs)}\r', end = '')
            logroot = f'{cfolder}/{logf}'
            try:
                logf = f'{logroot}/test_env'
                for i in range(2):
                    # env may crash and have multiple env instance, get maximum id one
                    sub = max([int(x) for x in os.listdir(logf)])
                    logf = f'{logf}/{sub}'
                replayf = [x for x in os.listdir(logf) if x[:10] == 'replay.txt']
                replayf.sort()
                replayf = f'{logf}/{replayf[-1]}'
                os.system(f'{prefix} {COMMAND} "{replayf}" "{replay_save_folder}/{log[:-4]}.txt"')
            except FileNotFoundError as e:
                print(f'{log} have no replay file')
                print(e)
            while logroot[-1] == '/':
                logroot = logroot[:-1]
            # os.system(f'{prefix} rm -r "{log_save_folder}/{logroot.split("/")[-1]}"')
            os.system(f'{prefix} {COMMAND} "{logroot}" "{log_save_folder}/"')
            # os.system(f'{prefix} rm -r "{wandb_save_folder}/{wandb[0]}"')
            os.system(f'{prefix} {COMMAND} "{wandb_root}/{wandb[0]}" "{wandb_save_folder}/"')
        except Exception as e:
            if DEBUG:
                raise e
            print('error:', e)
            failed.append(log)
    print(f'{len(failed)} failed. {" ".join(failed)}')


def KDD24(target):
    # used for KDD24 to get wandb and logs of one exp folder
    log_save_folder = f'{target}/logs'
    wandb_save_folder = f'{target}/wandb'
    for i in [log_save_folder, wandb_save_folder]:
        if not os.path.exists(i):
            try:  # when run on multiple servers, may raise exception
                os.mkdir(i)
            except:
                pass
    logs = os.listdir(target)
    configs = [x for x in logs if '.yml' == x[-4:]]
    assert len(configs) == 1
    configs = configs[0]
    logs = [x for x in logs if x[-4:] == '.log']
    logsf = [
        [y.strip().split(' ')[-1] 
         for y in open(f'{target}/{x}').readlines() 
         if 'log folder:' in y][0]
        for x in logs]
    try:
        wandbf = [
            [y.strip().split(' ')[-1]
             for y in open(f'{target}/{x}').readlines() 
             if 'wandb run:' in y][0]
            for x in logs]
    except:
        wandbf = ['UNEXIST_WANDB' for x in logs]
    # print('\n'.join(logs))
    # print(configs)
    cfolder = yaml.load(open(f'{target}/{configs}'), Loader = yaml.SafeLoader)['code_folder']
    wandb_root = f'{cfolder}/wandb'
    all_wandb = [x for x in os.listdir(wandb_root) if 'offline-' in x or 'run' in x]
    wandbf = [[y for y in all_wandb if x in y] for x in wandbf]
    failed = []
    for num, [log, logf, wandb] in enumerate(zip(logs, logsf, wandbf)):
        try:
            prefix = 'echo ' if DEBUG else ''
            print(f'{num}/{len(logs)}\r', end = '')
            logroot = f'{cfolder}/{logf}'
            while logroot[-1] == '/':
                logroot = logroot[:-1]
            # os.system(f'{prefix} rm -r "{log_save_folder}/{logroot.split("/")[-1]}"')
            os.system(f'{prefix} {COMMAND} "{logroot}" "{log_save_folder}/"')
            # os.system(f'{prefix} rm -r "{wandb_save_folder}/{wandb[0]}"')
            if len(wandb):
                os.system(f'{prefix} {COMMAND} "{wandb_root}/{wandb[0]}" "{wandb_save_folder}/"')
            else:
                print(f'wandb of `{logf}` not found')
        except Exception as e:
            if DEBUG:
                raise e
            print('error:', e)
            failed.append(log)
    print(f'{len(failed)} failed. {" ".join(failed)}')


def KDD24_sweep(target):
    # used for KDD24 to get wandb and logs of one exp folder
    log_save_folder = f'{target}/logs'
    wandb_save_folder = f'{target}/wandb'
    for i in [log_save_folder, wandb_save_folder]:
        if not os.path.exists(i):
            try:  # when run on multiple servers, may raise exception
                os.mkdir(i)
            except:
                pass
    logs = os.listdir(target)
    configs = [x for x in logs if '.yml' == x[-4:]]
    assert len(configs) == 1
    configs = configs[0]
    logs = [x for x in logs if x[-4:] == '.log']
    logsf = [
        [y.strip().split(' ')[-1] 
         for y in open(f'{target}/{x}').readlines() 
         if 'log folder:' in y]
        for x in logs]
    wandbf = [
        [y.strip().split(' ')[-1]
         for y in open(f'{target}/{x}').readlines() 
         if 'wandb run:' in y]
        for x in logs]
    # logsf = sum(logsf, [])
    # wandbf = sum(wandbf, [])
    # logsf = list(set(logsf))
    # wandbf = list(set(wandbf))
    # print('\n'.join(logs))
    # print(configs)
    cfolder = yaml.load(open(f'{target}/{configs}'), Loader = yaml.SafeLoader)['code_folder']
    wandb_root = f'{cfolder}/wandb'
    all_wandb = [x for x in os.listdir(wandb_root) if 'offline-' in x or 'run' in x]
    wandb_flat = sum(wandbf, [])
    wandb_flat = [[y for y in all_wandb if x in y] for x in wandb_flat]
    wandb_flat = set(sum(wandb_flat, []))
    failed = []
    for num, wandb in enumerate(wandb_flat):
        try:
            prefix = 'echo ' if DEBUG else ''
            print(f'{num}/{len(wandb_flat)}\r', end = '')
            # os.system(f'{prefix} rm -r "{wandb_save_folder}/{wandb[0]}"')
            os.system(f'{prefix} {COMMAND} "{wandb_root}/{wandb}" "{wandb_save_folder}/"')
        except Exception as e:
            if DEBUG:
                raise e
            print('error:', e)
            failed.append(log)
    print(f'{len(failed)} failed. {" ".join(failed)}')


if __name__ == '__main__':
    method = sys.argv[1]
    if method == 'ln':
        COMMAND = COMMAND_LN
    elif method == 'mv':
        COMMAND = COMMAND_MV
    else:
        raise NotImplementedError(method)
    func = sys.argv[2]
    if func == 'bl':
        blindlight(sys.argv[3])
    elif func == 'kdd':
        KDD24(sys.argv[3])
    elif func == 'sweep':
        KDD24_sweep(sys.argv[3])
    else:
        raise NotImplementedError(func)

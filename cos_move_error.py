#!/usr/bin/env python
import os

logs = [x for x in os.listdir('.') if x[-4:] == '.log']
logs = [x.split('_')[:-1] for x in logs]
logs = ['_'.join(x[:-1]) + '__' + x[-1] + '.7z' for x in logs]

for i in logs:
    print(i)
    source = f'"cos://tits/results/{i}"'
    dest = f'"cos://tits/errors/{i}"'
    os.system(f'coscli mv {source} {dest}')


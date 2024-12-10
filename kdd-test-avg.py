import os
import numpy as np
import sys

if __name__ == '__main__':
    folder = sys.argv[1] + '/logs/'
    subfolders = os.listdir(folder)
    for sf in subfolders:
        path = folder + sf + '/testinfo.txt'
        data = eval(open(path).read())
        history_reward = [eval(x) for x in data['history_reward']]
        hw = history_reward[-300:]
        hw = [max(x) for x in hw]
        hw = np.array(hw)
        hw[hw > 1] = 1
        hw.sort()
        print(f'{sf}\nmean:{hw.mean():.5f} median:{hw[len(hw)//2]:.5f}')

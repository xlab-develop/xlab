import argparse
import os
import json
import numpy as np
import matplotlib.pyplot as plt


### Get arguments
parser = argparse.ArgumentParser()

parser.add_argument('functions', type=str, nargs='+')

args = parser.parse_args()



### Load data
save_dir = 'data'

data = []
for f in args.functions:
    filename = os.path.join(save_dir, 'results_{}.json'.format(f))

    with open(filename, 'r') as in_file:
        data.append(json.load(in_file)['y'])
    
data = np.array(data)



### Make plots
x = np.arange(data.shape[1])
y = data

fig = plt.figure(figsize=(13, 8))
plt.title('Function benchmark')
plt.ylabel('y')
plt.xlabel('x')
for i, f in enumerate(args.functions):
    plt.plot(x, y[i], label=f)
plt.legend()
plt.savefig('benchmark.png')
plt.close(fig)
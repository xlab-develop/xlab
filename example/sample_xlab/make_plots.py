import argparse
import os
import json
import numpy as np
import matplotlib.pyplot as plt

import xlab.experiment as exp


### Get arguments
parser = argparse.ArgumentParser()

parser.add_argument('functions', type=str, nargs='+')

args = parser.parse_args()


### Create base experiment
executable = 'generate_data.py'
req_args = {
    'function': 'linear'
}
command = 'python {executable} {function}'

e = exp.Experiment(executable, req_args, command=command)


### Load data
data = []
for f in args.functions:
    e.args['function'] = f
    exp_dir = e.get_dir()

    if e.is_complete():
        print("*** Using cached version from {}".format(exp_dir))
    else:
        e.run(use_cached=True, wait=True)

    filename = os.path.join(exp_dir, 'results.json')
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

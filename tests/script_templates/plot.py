from argparse import ArgumentParser
import os
import json
import numpy as np
import matplotlib.pyplot as plt

import xlab.experiment as exp


### Get parser
parser = ArgumentParser()

parser.add_argument('ops', type=str, nargs='+')
parser.add_argument('--start', type=int, default=0)
parser.add_argument('--samples', type=int, default=10)

args = parser.parse_args()


### Create base experiment
executable = 'sampler.py'
req_args = {
    'op': 'linear',
    'value': 0,
}
command = 'python {executable} {op} {value}'

e = exp.Experiment(executable, req_args, command=command)


### Load data
ops = args.ops
values = [i + args.start for i in range(args.samples)]

metrics = {}
for op in ops:
    metrics[op] = []

    for value in values:
        e.args['op'] = op
        e.args['value'] = value

        exp_dir = e.get_dir()

        filename = os.path.join(exp_dir, 'metrics.json')
        with open(filename, 'r') as in_file:
            data = json.load(in_file)
    
        metrics[op].append(np.mean(data))


### Make plots
indices = np.arange(len(list(metrics.values())[0]))

fig = plt.figure(figsize=(13, 8))
plt.title('Function benchmark')
plt.ylabel('y')
plt.xlabel('x')
for i, op in enumerate(args.ops):
    plt.plot(indices, metrics[op], label=op)
plt.legend()
plt.savefig('benchmark.png')
plt.close(fig)

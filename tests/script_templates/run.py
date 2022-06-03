from argparse import ArgumentParser

import xlab.experiment as exp
from xlab.filesys import dirs


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


### Run experiments
ops = args.ops
values = [i + args.start for i in range(args.samples)]

for op in ops:
    for value in values:
        e.args['op'] = op
        e.args['value'] = value

        e.run()
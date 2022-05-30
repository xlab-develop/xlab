from argparse import ArgumentParser
import os
import time

import json

import xlab.experiment as exp
from xlab.filesys import dirs


### Get parser
parser = ArgumentParser()

parser.add_argument('op', type=str)
parser.add_argument('value', type=int)
parser.add_argument('--repetitions', type=int, default=10)
parser.add_argument('--delay', type=int, default=0)

ignores = ['delay']


### Setup experiment
with exp.setup(parser, hash_ignore=ignores) as setup:
    args = setup.args
    dir = setup.dir

    time.sleep(args.delay)

    ### Generate toy data
    if args.op == 'linear':
        data = [args.value for _ in range(args.repetitions)]
    elif args.op == 'quadratic':
        data = [args.value ** 2 for _ in range(args.repetitions)]
    elif args.op == 'sqrt':
        data = [args.value ** (1/2) for _ in range(args.repetitions)]
    else:
        raise Exception('Invalid operation. Choose one of "linear", "quadratic", or "sqrt".')

    ### Save data
    filepath = os.path.join(dir, 'metrics.json')
    with open(filepath, 'w') as out_file:
        json.dump(data, out_file, indent=4)



    ### THESE LINES WERE EXCLUSIVELY ADDED FOR TESTING PURPOSES
    root = dirs.root()
    test_data_path = os.path.join(root, 'test_data.json')

    if os.path.exists(test_data_path):
        with open(test_data_path, 'r') as in_file:
            results = json.load(in_file)
    else:
        results = {}
    
    if 'sampler_calls' not in results:
        results['sampler_calls'] = 0
    if 'sampler_data' not in results:
        results['sampler_data'] = []
    
    results['sampler_calls'] += 1
    results['sampler_data'].append({
        'root': root,
        'dir': dir,
        'args': dict(vars(args)),
        'data': data,
    })

    with open(test_data_path, 'w') as out_file:
        json.dump(results, out_file, indent=4)
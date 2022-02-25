import argparse
import numpy as np
import os
import json
import time

import experimental as exp


### Get arguments
parser = argparse.ArgumentParser()

parser.add_argument('function', type=str)
parser.add_argument('--samples', type=int, default=20)
parser.add_argument('--cpus', type=int, default=1)

ignores = ['cpus']

with exp.setup(parser, hash_ignore=ignores) as setup:
    args = setup.args
    save_dir = setup.dir


    ### Get data
    time.sleep(3)
    x = np.arange(args.samples)
    if args.function == 'linear':
        y = x
    elif args.function == 'quadratic':
        y = x ** 2
    elif args.function == 'sqrt':
        y = np.sqrt(x)
    else:
        print("error: Invalid function '{}'".format(args.function))

    data = {
        'y': y.tolist()
    }


    ### Save data
    filename = os.path.join(save_dir, 'results.json')

    with open(filename, 'w') as out_json:
        json.dump(data, out_json)
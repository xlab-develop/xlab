import argparse
import numpy as np
import os
import json

import experimental as exp


### Get arguments
parser = argparse.ArgumentParser()

parser.add_argument('function', type=str)
parser.add_argument('--samples', type=int, default=20)


with exp.setup(parser) as setup:
    args = setup.args
    save_dir = setup.dir


    ### Get data
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
    filename = os.path.join(save_dir, 'result.json')

    with open(filename, 'w') as out_json:
        json.dump(data, out_json)
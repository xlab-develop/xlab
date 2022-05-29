import os
from argparse import ArgumentParser

import xlab.experiment as exp

parser = ArgumentParser()

parser.add_argument('op', type=str)
parser.add_argument('--size', type=int, default=10)

with exp.setup(parser) as setup:
    args = setup.args
    dir = setup.dir

    data = args.op + ':' + str(args.size)

    with open(os.path.join(dir, 'result.txt'), 'w') as out_file:
        out_file.write(data)
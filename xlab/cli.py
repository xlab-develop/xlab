import sys
import os

from . import filesys

MAIN_USAGE_MESSAGE = """
usage: xlab command ...

Options:

positional arguments:
  command
    project
"""

def project(args):
    if len(args) != 1:
        print("error: Invalid arguments.")
        exit()
    
    if args[0] == 'init':
        root = os.getcwd()
        
        dirs = filesys.Directories()
        dirs.set_root(root)


def main():
    if len(sys.argv) <= 1:
        print(MAIN_USAGE_MESSAGE)
        exit()
    
    command = sys.argv[1]
    args = sys.argv[2:]

    if command == 'project':
        exe = project
    else:
        print("error: No command 'xlab {}'.".format(command))
        exit()
    
    exe(args)
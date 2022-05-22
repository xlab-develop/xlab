import sys
import os

from xlab import filesys

MAIN_USAGE_MESSAGE = """
usage: xlab command ...

Options:

positional arguments:
  command
    project
"""


def project(args):
    """Project-related CLI sub-command.
    
    Args:
        args: dictionary of CLI arguments.
    """

    # Validate arguments
    if len(args) != 1:
        print('error: Invalid arguments.')
        exit()
    
    if args[0] == 'init':
        # Subcommand that sets up a project from a directory

        root = os.getcwd()
        
        dirs = filesys.Directories()
        dirs.set_root(root)


def main():
    """Main call to CLI command."""

    # Validate arguments
    if len(sys.argv) <= 1:
        print(MAIN_USAGE_MESSAGE)
        exit()
    
    command = sys.argv[1]
    args = sys.argv[2:]

    # Assign matching subcommands
    if command == 'project':
        exe = project
    else:
        print("error: No command 'xlab {}'.".format(command))
        exit()
    
    exe(args)
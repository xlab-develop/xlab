from subprocess import Popen, PIPE
from argparse import Namespace
import json
import sys
import os
import traceback
import fasteners
from datetime import datetime

from xlab import cache, filesys
from xlab.cache import Cache
from xlab.utils import merge_dicts, substract_dict_keys

DEFAULT_INDEX_KEYS = [
    'executable',
]
DEFAULT_ARGS_KEYS = [
    'exp_config',
    'exp_dir',
    'exp_is_complete',
    'exp_force',
    'exp_no_wait',
    'exp_hash',
]
DEFAULT_CONFIG_KEYS = [
    'exp_time',
]


def init_args(executable):
    """Returns a dict filled with basic default run data.

    Args:
        executable: path to executable for the run.
    """

    args = {
        'executable': executable,
        'exp_time': datetime.now().strftime('%Y-%m-%d_%H-%M-%S'),
    }
    return args


def setup(*args, **kwargs):
    """Returns an instance of a Setup class."""

    return Setup(*args, **kwargs)


class Setup:
    def __init__(self, parser, hash_ignore=[]):
        """Initializes the experiment retrieval setup.

        The experiment setup is defined as a function of a parser
        because it automatically parses the input on a call to
        __enter__. For this reason, we expect the parser to be already
        initialized prior to the instantiation of this class.

        Args:
            parser: already initialized argpase parser.
            hash_ignore: keys not to be considered while hashing.
        """

        parser.add_argument(
            '--exp-config', default='{}',
            type=json.loads)
        parser.add_argument(
            '--exp-dir', default=False,
            action='store_const', const=True)
        parser.add_argument(
            '--exp-is-complete', default=False,
            action='store_const', const=True)
        parser.add_argument(
            '--exp-force', default=False,
            action='store_const', const=True)
        parser.add_argument(
            '--exp-no-wait', default=False,
            action='store_const', const=True)
        parser.add_argument(
            '--exp-hash', default=False,
            action='store_const', const=True)

        self.parser = parser

        self._cache = Cache()
        self._hash_ignore = hash_ignore
        self._run_lock = None
    
    def __enter__(self):
        """Opens the context of a run within a 'with' statement.
        
        This call automatically parses the input arguments, and
        assigns a new directory to the run for results to be saved.
        """

        executable = filesys.relative_root_path(sys.argv[0])

        default_args = init_args(executable)
        parser_args = dict(vars(self.parser.parse_args()))
        input_config_args = parser_args['exp_config']

        args = merge_dicts(default_args, parser_args)
        args = merge_dicts(args, input_config_args)

        self._all_args = args

        user_args = substract_dict_keys(
            args, 
            DEFAULT_ARGS_KEYS + DEFAULT_CONFIG_KEYS + DEFAULT_INDEX_KEYS)
        config_args = substract_dict_keys(
            args,
            DEFAULT_ARGS_KEYS)
        hash_args = substract_dict_keys(
            args,
            DEFAULT_ARGS_KEYS + DEFAULT_CONFIG_KEYS + self._hash_ignore)
        
        self.args = Namespace(**user_args)
        

        exists = self._cache.exists(hash_args)
        if exists:
            self.dir = self._cache.get_dir(hash_args)
        else:
            self.dir = self._cache.assign_dir(hash_args)
        
        input_hash_args = substract_dict_keys(
            input_config_args, DEFAULT_CONFIG_KEYS + self._hash_ignore)
        input_hash = cache.get_hash(input_hash_args)
        if not self._cache.exists(input_hash):
            self._cache.merge_hashes(input_hash, cache.get_hash(hash_args))

        os.makedirs(self.dir, exist_ok=True)

        path = os.path.join(self.dir, 'config.json')
        if not os.path.exists(path) or args['exp_force']:
            with open(path, 'w') as out_file:
                json.dump(config_args, out_file, indent=4)

        if args['exp_hash']:
            print(cache.get_hash(hash_args))
            exit(0)

        if args['exp_dir']:
            print(self.dir)
            exit(0)
        
        if args['exp_is_complete']:
            print(self._cache.is_complete(hash_args))
            exit(0)

        self._run_lock = fasteners.InterProcessLock(
            os.path.join(self.dir, '.run.lock'))
        self._run_lock.acquire()

        err_filename = os.path.join(self.dir, 'error.log')
        if os.path.exists(err_filename):
            os.remove(err_filename)
        
        if self._cache.is_complete(hash_args) and not args['exp_force']:
            print('*** Using cached data on {}'.format(self.dir))
            self._run_lock.release()
            exit(0)
        
        return self
    
    def __exit__(self, exc_type, exc_value, tb):
        """Closes run context and catches errors.
        
        If the run of an experiment is completed successfully, the
        results are cached. If not, the error is catched and thrown.
        """

        if exc_type is not None:
            tb_message = ''.join(
                traceback.format_exception(exc_type, exc_value, tb))
            err_filename = os.path.join(self.dir, 'error.log')
            with open(err_filename, 'w') as err_file:
                err_file.write(tb_message)
                
            self._run_lock.release()
            return False
        
        hash_args = substract_dict_keys(
            self._all_args,
            DEFAULT_CONFIG_KEYS + DEFAULT_ARGS_KEYS + self._hash_ignore)

        self._cache.set_complete(hash_args)

        self._run_lock.release()

        return True



class Experiment:
    def __init__(self, executable, req_args, command):
        """Initializes the experiment run setup.

        The experiment arguments are set from initialization to have
        it ready to be run later, with few updates to the arguments.

        Args:
            executable: string of experiment executable path.
            req_args: dict of required arguments on command call.
            command: template string of the command to be executed for
                the experiment to run. As it is a template, keys
                within the string are replaced by its values from the
                experiment arguments. Note that the executable name
                is also replaced in the string.
                
                Example:

                command='python {executable} {arg1} {arg2}'

                One can run an instance of the experiment by providing
                arguments, such as:
                    * executable='main.py'
                    * req_args={
                        'arg1': 10,
                        'arg2': 'a'
                    }
        """

        self.executable = filesys.relative_root_path(executable)
        self.command = command
        self.args = req_args
        
        self._cache = Cache()
        self._last_full_hash = None
        self._last_local_hash = cache.get_hash(self.args)

        dir = self.get_dir()
        
        path = os.path.join(dir, 'config.json')
        with open(path, 'r') as in_file:
            self.args = json.load(in_file)

    def run(
            self, custom_command=None,
            use_cached=True, wait=True):
        """Runs an experiment for the current argument setup.

        The dictionary self.args can be modified by the user freely,
        as an interface for creating a series of experiments. Whenever
        this method is called, the current state of self.args is used
        to run an execution instance for the experiment.
        
        Args:
            custom_command: string representing a command to run the
                the experiment. Used when the default command given
                at experiment initialization does not fit the desired
                usage of the run.
            use_cached: boolean that allows the experiment results to
                be retrieved in case they are cached if set to true.
            wait: boolean that enables experiments to wait for
                previous experiments to finish running before starting
                its execution.
        """

        tmp_args = init_args(self.executable)
        tmp_args = merge_dicts(tmp_args, self.args)

        command = custom_command if custom_command != None else self.command
        command = command.format(**tmp_args)
        command_parts = command.split(' ')
        if not use_cached:
            command_parts.append('--exp-force')
        if not wait:
            command_parts.append('--exp-no-wait')
        command_parts += ['--exp-config', '{}'.format(json.dumps(self.args))]
        
        exe = Popen(command_parts, stdout=PIPE, stderr=PIPE)
        out, err = exe.communicate()

    def get_hash(self):
        """Returns the hash identifier of a run."""

        curr_local_hash = cache.get_hash(self.args)
        if (curr_local_hash == self._last_local_hash and
                self._last_full_hash is not None):
            return self._last_full_hash
        self._last_local_hash = curr_local_hash

        if self._cache.exists(self.args):
            return curr_local_hash
        
        tmp_args = init_args(self.executable)
        tmp_args = merge_dicts(tmp_args, self.args)

        command = self.command.format(**tmp_args)
        command_parts = command.split(' ')
        command_parts.append('--exp-hash')
        command_parts += ['--exp-config', '{}'.format(json.dumps(self.args))]

        exe = Popen(command_parts, stdout=PIPE, stderr=PIPE)
        out, err = exe.communicate()

        lines = out.decode(sys.stdin.encoding).split('\n')
        err_msg = err.decode(sys.stdin.encoding)

        if len(lines) < 2:
            if len(err) > 0:
                raise Exception(err_msg)
            else:
                raise Exception('error: Command did not print an output.')

        hash = lines[-2]

        if not self._cache.exists(hash):
            if len(err) > 0:
                raise Exception(err_msg)
            else:
                raise Exception('error: Command returned invalid hash.')

        self._last_full_hash = hash
        self._cache.merge_hashes(curr_local_hash, hash)

        return hash

    def get_dir(self):
        """Returns the directory assigned to a run."""

        return self._cache.get_dir(self.get_hash())

    def is_complete(self):
        """Returns true if the run has been completed."""

        return self._cache.is_complete(self.get_hash())

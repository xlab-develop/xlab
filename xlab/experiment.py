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

    # So far, it's used like an interface
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

        # Adds default xlab option for automated functions to work
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

        # Incrementaly merge args together to have a dictionary
        # with keys from all types of args 
        args = merge_dicts(default_args, parser_args)
        args = merge_dicts(args, input_config_args)

        self._all_args = args


        # Filter arguments to meet specific purposes

        # Arguments that can be observed and modified by the user from
        # the Python interface: self.args
        user_args = substract_dict_keys(
            args, 
            DEFAULT_ARGS_KEYS + DEFAULT_CONFIG_KEYS + DEFAULT_INDEX_KEYS)

        # Arguments that will be saved on the run's config.json
        config_args = substract_dict_keys(
            args,
            DEFAULT_ARGS_KEYS)

        # Arguments used as a run's unique identifier
        hash_args = substract_dict_keys(
            args,
            DEFAULT_ARGS_KEYS + DEFAULT_CONFIG_KEYS + self._hash_ignore)


        # Get user args
        self.args = Namespace(**user_args)

        # Get unique dir for current run
        exists = self._cache.exists(hash_args)
        if exists:
            self.dir = self._cache.get_dir(hash_args)
        else:
            self.dir = self._cache.assign_dir(hash_args)

        os.makedirs(self.dir, exist_ok=True)
        
        # Associate the dir and run status from an incomplete input
        # args dict to its filled-out output args dict if cached
        input_hash_args = substract_dict_keys(
            input_config_args, DEFAULT_CONFIG_KEYS + self._hash_ignore)
        input_hash = cache.get_hash(input_hash_args)
        if not self._cache.exists(input_hash):
            self._cache.merge_hashes(input_hash, cache.get_hash(hash_args))

        # Create config.json on run's dir if forced or not present
        path = os.path.join(self.dir, 'config.json')
        if not os.path.exists(path) or args['exp_force']:
            with open(path, 'w') as out_file:
                json.dump(config_args, out_file, indent=4)


        ### Print requested information from run
        if args['exp_hash']:
            print(cache.get_hash(hash_args))
            exit(0)

        if args['exp_dir']:
            print(self.dir)
            exit(0)
        
        if args['exp_is_complete']:
            print(self._cache.is_complete(hash_args))
            exit(0)


        # Assign lock to organize concurrent exection
        self._run_lock = fasteners.InterProcessLock(
            os.path.join(self.dir, '.run.lock'))
        self._run_lock.acquire()
        ### Start of critical region

        # Remove any error.log file from previous cached runs
        err_filename = os.path.join(self.dir, 'error.log')
        if os.path.exists(err_filename):
            os.remove(err_filename)
        
        # If a previous run was successful, use cached data and
        # release lock
        if self._cache.is_complete(hash_args) and not args['exp_force']:
            print('*** Using cached data on {}'.format(self.dir))

            ### End of critical region
            self._run_lock.release()
            exit(0)
        
        # Note that up to this line of code, the critical region is
        # open. The idea is to keep it open throughout the scope of
        # the with block, which contains code provided by the user.
        # In case any exception is raised, the critical region
        # is closed on the with exit method that catches the exception
        return self
    
    def __exit__(self, exc_type, exc_value, tb):
        """Closes run context and catches errors.
        
        If the run of an experiment is completed successfully, the
        results are cached. If not, the error is catched and thrown.
        """

        # Makes sure to record exception on error.log and release lock
        # if any exception occurs on the user side within the with
        # block
        if exc_type is not None:
            tb_message = ''.join(
                traceback.format_exception(exc_type, exc_value, tb))
            err_filename = os.path.join(self.dir, 'error.log')
            with open(err_filename, 'w') as err_file:
                err_file.write(tb_message)
                
            ### End of critical region
            self._run_lock.release()
            return False
        
        # If there was no exception, the run is marked as complete
        hash_args = substract_dict_keys(
            self._all_args,
            DEFAULT_CONFIG_KEYS + DEFAULT_ARGS_KEYS + self._hash_ignore)
        self._cache.set_complete(hash_args)

        ### End of critical region
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

        # These params refer to the hashes of the incomplete, local
        # dict of arguments provided from the caller executable or
        # CLI, and the complete dict of arguments obtained from the
        # executable after the parser and processor has filled out
        # default parameters
        self._last_full_hash = None
        self._last_local_hash = cache.get_hash(self.args)

        # Makes a call to the executable to retrieve the directory
        # location assigned to the minimal required run arguments
        # of this executable
        dir = self.get_dir()
        
        # Loads the run config from this directory, as it has the
        # argument structure autocompleted by the parser and processor
        # on the executable. This makes it easier for the user of
        # self.args to manipulate arguments from this experiment
        # (there is no need to remember the structure of the args dict
        # if it is already provided by the executable)
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

        # Prepare run arguments
        tmp_args = init_args(self.executable)
        tmp_args = merge_dicts(tmp_args, self.args)

        # Prepare run command to be called
        command = custom_command if custom_command != None else self.command
        command = command.format(**tmp_args)
        command_parts = command.split(' ')
        if not use_cached:
            command_parts.append('--exp-force')
        if not wait:
            command_parts.append('--exp-no-wait')
        command_parts += ['--exp-config', '{}'.format(json.dumps(self.args))]
        
        # Call command and get outputs and errors
        exe = Popen(command_parts, stdout=PIPE, stderr=PIPE)
        out, err = exe.communicate()

    def get_hash(self):
        """Returns the hash identifier of a run."""

        ### Get results from cached hash whenever possible

        # If the current hash from args provided by the user is equal
        # to the hash from its previous set of args, we can return the
        # hash of the complete version of the args dict filled by the
        # executable, obtained from the previous call to this function
        curr_local_hash = cache.get_hash(self.args)
        if (curr_local_hash == self._last_local_hash and
                self._last_full_hash is not None):
            return self._last_full_hash
        self._last_local_hash = curr_local_hash

        # If the hash of the incomplete set of args provided by the
        # user is already associated to the complete set of args
        # filled out by the executable, we can use the former to
        # retrieve the results saved from the latter
        if self._cache.exists(self.args):
            return curr_local_hash
        

        # Prepare run arguments
        tmp_args = init_args(self.executable)
        tmp_args = merge_dicts(tmp_args, self.args)

        # Prepare run command to be called
        command = self.command.format(**tmp_args)
        command_parts = command.split(' ')
        command_parts.append('--exp-hash')
        command_parts += ['--exp-config', '{}'.format(json.dumps(self.args))]

        # Call command and get outputs and errors
        exe = Popen(command_parts, stdout=PIPE, stderr=PIPE)
        out, err = exe.communicate()

        lines = out.decode(sys.stdin.encoding).split('\n')
        err_msg = err.decode(sys.stdin.encoding)

        if len(lines) < 2:
            if len(err) > 0:
                raise Exception(err_msg)
            else:
                raise Exception('error: Command did not print an output.')

        # If there were no error messages, then the last printed
        # output before the end of execution should be the run's hash
        hash = lines[-2]

        # Validate if the output is, in fact, a hash
        if not self._cache.exists(hash):
            if len(err) > 0:
                raise Exception(err_msg)
            else:
                raise Exception('error: Command returned invalid hash.')

        # Associate incomplete args provided by the user to the
        # complete args obtained from the executable to enable caching
        self._last_full_hash = hash
        self._cache.merge_hashes(curr_local_hash, hash)

        return hash

    def get_dir(self):
        """Returns the directory assigned to a run."""

        return self._cache.get_dir(self.get_hash())

    def is_complete(self):
        """Returns true if the run has been completed."""

        return self._cache.is_complete(self.get_hash())

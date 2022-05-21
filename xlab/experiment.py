from subprocess import Popen, PIPE, STDOUT
from argparse import Namespace
import copy
import json
import sys
import os
import traceback
import fasteners
from datetime import datetime

from . import cache, filesys
from .cache import Cache
from .utils import merge_dicts, substract_dict_keys

DEFAULT_INDEX_KEYS = ['executable']
DEFAULT_ARGS_KEYS = ['exp_config', 'exp_dir', 'exp_is_complete', 'exp_force', 'exp_no_wait', 'exp_hash']
DEFAULT_CONFIG_KEYS = ['exp_time']

def init_args(executable):
    args = {
        'executable': executable,
        'exp_time': datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    }
    return args

def setup(*args, **kwargs):
    return Setup(*args, **kwargs)

class Setup:
    def __init__(self, parser, hash_ignore=[]):
        parser.add_argument("--exp-config", default='{}', type=json.loads)
        parser.add_argument("--exp-dir", default=False, action="store_const", const=True)
        parser.add_argument("--exp-is-complete", default=False, action="store_const", const=True)
        parser.add_argument("--exp-force", default=False, action="store_const", const=True)
        parser.add_argument("--exp-no-wait", default=False, action="store_const", const=True)
        parser.add_argument("--exp-hash", default=False, action="store_const", const=True)

        self.parser = parser

        self._cache = Cache()
        self._hash_ignore = hash_ignore
        self._run_lock = None
    
    def __enter__(self):
        executable = filesys.relative_root_path(sys.argv[0])

        default_args = init_args(executable)
        parser_args = dict(vars(self.parser.parse_args()))
        input_config_args = parser_args['exp_config']

        args = merge_dicts(default_args, parser_args)
        args = merge_dicts(args, input_config_args)

        self._all_args = args

        user_args = substract_dict_keys(args, DEFAULT_ARGS_KEYS + DEFAULT_CONFIG_KEYS + DEFAULT_INDEX_KEYS)
        config_args = substract_dict_keys(args, DEFAULT_ARGS_KEYS)
        hash_args = substract_dict_keys(args, DEFAULT_ARGS_KEYS + DEFAULT_CONFIG_KEYS + self._hash_ignore)
        
        self.args = Namespace(**user_args)
        

        exists = self._cache.exists(hash_args)
        self.dir = self._cache.get_dir(hash_args) if exists else self._cache.assign_dir(hash_args)
        
        input_hash_args = substract_dict_keys(input_config_args, DEFAULT_CONFIG_KEYS + self._hash_ignore)
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

        self._run_lock = fasteners.InterProcessLock(os.path.join(self.dir, '.run.lock'))
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
        if exc_type is not None:
            tb_message = ''.join(traceback.format_exception(exc_type, exc_value, tb))
            err_filename = os.path.join(self.dir, 'error.log')
            with open(err_filename, 'w') as err_file:
                err_file.write(tb_message)
                
            self._run_lock.release()
            return False
        
        hash_args = substract_dict_keys(self._all_args, DEFAULT_CONFIG_KEYS + DEFAULT_ARGS_KEYS + self._hash_ignore)

        self._cache.set_complete(hash_args)

        self._run_lock.release()

        return True



class Experiment:
    def __init__(self, executable, req_args, command, hash_ignore=[]):
        self.executable = filesys.relative_root_path(executable)
        self.command = command
        self.args = req_args
        self._hash_ignore = hash_ignore
        
        self._cache = Cache()
        self._last_full_hash = None
        self._last_local_hash = cache.get_hash(substract_dict_keys(merge_dicts(init_args(self.executable), self.args), DEFAULT_CONFIG_KEYS + self._hash_ignore))

        dir = self.get_dir()
        
        path = os.path.join(dir, 'config.json')
        with open(path, 'r') as in_file:
            self.args = json.load(in_file)

    def run(self, custom_command=None, use_cached=True, wait=True):
        tmp_args = init_args(self.executable)
        tmp_args = merge_dicts(tmp_args, self.args)

        command = custom_command if custom_command != None else self.command
        command = command.format(**tmp_args)
        command_parts = command.split(' ')
        if not use_cached:
            command_parts.append('--exp-force')
        if not wait:
            command_parts.append('--exp-no-wait')
        command_parts += ["--exp-config", "{}".format(json.dumps(self.args))]
        
        exe = Popen(command_parts, stdout=PIPE, stderr=PIPE)
        out, err = exe.communicate()

    def get_hash(self):
        default_args = init_args(self.executable)
        local_hash_args = substract_dict_keys(merge_dicts(default_args, self.args), DEFAULT_CONFIG_KEYS + self._hash_ignore)

        curr_local_hash = cache.get_hash(local_hash_args)
        # if curr_local_hash == self._last_local_hash and self._last_full_hash is not None:
        #     return self._last_full_hash
        self._last_local_hash = curr_local_hash

        if self._cache.exists(local_hash_args):
            return curr_local_hash
        
        tmp_args = init_args(self.executable)
        tmp_args = merge_dicts(tmp_args, self.args)

        command = self.command.format(**tmp_args)
        command_parts = command.split(' ')
        command_parts.append("--exp-hash")
        command_parts += ["--exp-config", "{}".format(json.dumps(self.args))]

        exe = Popen(command_parts, stdout=PIPE, stderr=PIPE)
        out, err = exe.communicate()

        lines = out.decode(sys.stdin.encoding).split('\n')
        err_msg = err.decode(sys.stdin.encoding)

        if len(lines) < 2:
            if len(err) > 0:
                raise Exception(err_msg)
            else:
                raise Exception("error: Command did not print an output.")

        hash = lines[-2]

        if not self._cache.exists(hash):
            if len(err) > 0:
                raise Exception(err_msg)
            else:
                raise Exception("error: Command returned invalid hash.")

        self._last_full_hash = hash
        self._cache.merge_hashes(curr_local_hash, hash)
        
        return hash

    def get_dir(self):
        return self._cache.get_dir(self.get_hash())

    def is_complete(self):
        return self._cache.is_complete(self.get_hash())

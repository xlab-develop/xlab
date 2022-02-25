### Arguments
from argparse import Namespace
import copy
import sys
import os
import traceback

def merge_dicts(a, b, output_type=None):
    a_type = type(a)
    b_type = type(b)

    if a_type == Namespace:
        a = dict(vars(a))
    if b_type == Namespace:
        b = dict(vars(b))

    a = copy.deepcopy(a)

    for key in b:
        val = b[key]
        if type(val) == dict and key in a and type(a[key]) == dict:
            a[key] = merge_dicts(a[key], val)
        else:
            a[key] = val

    if output_type == None:
        output_type = a_type
    if output_type == Namespace:
        a = Namespace(**a)

    return a

def substract_dict_keys(a, keys):
    a = copy.deepcopy(a)
    for key in keys:
        if key in a:
            del a[key]
    
    return a



### Cache functions
from argparse import Namespace
import json
import hashlib
import copy
import pickle

exp_path = '.exp'
runs_path = 'runs'
metadata_path = os.path.join(exp_path, 'metadata.json')
hashmap_path = os.path.join(exp_path, 'hashmap.pkl')

if not os.path.exists(exp_path):
    os.makedirs(exp_path, exist_ok=True)

if not os.path.exists(runs_path):
    os.makedirs(runs_path, exist_ok=True)

if not os.path.exists(metadata_path):
    with open(metadata_path, 'w') as out_file:
        json.dump({
            'next_id': 0
        }, out_file)

if not os.path.exists(hashmap_path):
    with open(hashmap_path, 'wb') as out_file:
        pickle.dump({}, out_file)

def cache_get_hash(args):
    hash = hashlib.sha224(json.dumps(sorted(args.items()), separators=(',', ':')).encode('utf-8')).hexdigest()
    return hash

def cache_exists(args):
    hash = cache_get_hash(args)
    with open(hashmap_path, 'rb') as in_file:
        cache = pickle.load(in_file)
    return hash in cache

def cache_complete(args):
    hash = cache_get_hash(args)
    with open(hashmap_path, 'rb') as in_file:
        cache = pickle.load(in_file)
    return hash in cache and cache[hash][1]

def cache_get_dir(args):
    hash = cache_get_hash(args)
    with open(hashmap_path, 'rb') as in_file:
        cache = pickle.load(in_file)
    if hash in cache:
        return cache[hash][0]
    else:
        raise Exception('error: Hash not found in cache.')

def cache_assign_dir(args):
    with open(metadata_path, 'r') as in_file:
        metadata = json.load(in_file)
    id = metadata['next_id']
    metadata['next_id'] += 1
    with open(metadata_path, 'w') as out_file:
        json.dump(metadata, out_file)

    path = os.path.join(runs_path, str(id))
    hash = cache_get_hash(args)
    with open(hashmap_path, 'rb') as in_file:
        cache = pickle.load(in_file)
    cache[hash] = [path, False]
    with open(hashmap_path, 'wb') as out_file:
        pickle.dump(cache, out_file)
    
    return path

def cache_set_complete(args):
    hash = cache_get_hash(args)
    with open(hashmap_path, 'rb') as in_file:
        cache = pickle.load(in_file)
    cache[hash][1] = True
    with open(hashmap_path, 'wb') as out_file:
        pickle.dump(cache, out_file)



### Setup class
from subprocess import Popen, PIPE, STDOUT
import copy
import json
import os

def setup(*args, **kwargs):
    return Setup(*args, **kwargs)

class Setup:
    def __init__(self, parser, hash_ignore=[]):
        parser.add_argument("--exp-config", default='{}', type=json.loads)
        parser.add_argument("--exp-dir", default=False, action="store_const", const=True)
        parser.add_argument("--exp-force", default=False, action="store_const", const=True)
        parser.add_argument("--exp-no-wait", default=False, action="store_const", const=True)

        self.parser = parser

        self._hash_ignore = hash_ignore
    
    def __enter__(self):
        default_args_keys = ['exp_config', 'exp_dir', 'exp_force', 'exp_no_wait']
        default_config_keys = ['executable']

        args = {
            'executable': sys.argv[0]
        }
        args = merge_dicts(args, dict(vars(self.parser.parse_args())))
        args = merge_dicts(args, args['exp_config'])

        self._all_args = args

        user_args = substract_dict_keys(args, default_args_keys + default_config_keys)
        config_args = substract_dict_keys(args, default_args_keys)
        hash_args = substract_dict_keys(args, 
            substract_dict_keys(default_args_keys, ['executable']) +
            default_config_keys + self._hash_ignore
        )
        
        self.args = Namespace(**user_args)
        

        exists = cache_exists(hash_args)
        self.dir = cache_get_dir(hash_args) if exists else cache_assign_dir(hash_args)

        os.makedirs(self.dir, exist_ok=True)

        path = os.path.join(self.dir, 'config.json')
        if not os.path.exists(path) or args['exp_force']:
            with open(path, 'w') as out_file:
                json.dump(config_args, out_file, indent=4)

        if args['exp_dir']:

            print(self.dir)

            exit(0)
        
        if cache_complete(hash_args) and not args['exp_force']:
            print('*** Using cached data on {}'.format(self.dir))
            exit(0)
        
        return self
    
    
    def __exit__(self, exc_type, exc_value, tb):
        if exc_type is not None:
            traceback.print_exception(exc_type, exc_value, tb)
            return False

        default_args_keys = ['exp_config', 'exp_dir', 'exp_force', 'exp_no_wait']
        default_config_keys = ['executable']
        
        hash_args = substract_dict_keys(self._all_args, 
            substract_dict_keys(default_args_keys, ['executable']) +
            default_config_keys + self._hash_ignore
        )

        cache_set_complete(hash_args)

        return True



### Experiment class

class Experiment:
    def __init__(self, executable, req_args, command):
        self.executable = executable
        self.command = command
        
        self.args = req_args
        dir = self.get_dir()
        
        path = os.path.join(dir, 'config.json')
        with open(path, 'r') as in_file:
            self.args = json.load(in_file)

    def run(self, use_cached=True, wait=True):
        tmp_args = {
            'executable': self.executable
        }
        tmp_args = merge_dicts(tmp_args, copy.deepcopy(self.args))

        command = self.command.format(**tmp_args)
        command_parts = command.split(' ')
        if not use_cached:
            command_parts.append('--exp-force')
        if not wait:
            command_parts.append('--exp-no-wait')
        command_parts += ["--exp-config", "{}".format(json.dumps(self.args))]
        
        exe = Popen(command_parts)
        exe.communicate()
        # TODO: catch errors

    def get_dir(self):
        tmp_args = {
            'executable': self.executable
        }
        tmp_args = merge_dicts(tmp_args, copy.deepcopy(self.args))

        command = self.command.format(**tmp_args)
        command_parts = command.split(' ')
        command_parts.append("--exp-dir")
        command_parts += ["--exp-config", "{}".format(json.dumps(self.args))]

        exe = Popen(command_parts, stdout=PIPE, stderr=PIPE)
        out, err = exe.communicate()

        lines = out.decode(sys.stdin.encoding).split('\n')
        if len(lines) < 2:
            raise Exception("Command didn't return a directory")

        dir = lines[-2]

        if len(err) > 0 and not os.path.exists(dir):
            error = err.decode(sys.stdin.encoding)
            raise Exception(error)

        return dir
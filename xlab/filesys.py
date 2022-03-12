import os
import sys
import json
import pickle
import fasteners

_dirs = {}

def find_root_dir():
    try:
        filename = os.path.realpath(sys.argv[0])
        dirname = os.path.dirname(filename) if os.path.isfile(filename) else filename

        curr_dir = dirname
    except:
        curr_dir = os.getcwd()
    
    abs_root = os.path.abspath(os.sep)

    while curr_dir != abs_root and '.exp' not in os.listdir(curr_dir):
        curr_dir = os.path.dirname(curr_dir)
    
    if '.exp' not in os.listdir(curr_dir):
        curr_dir = None
    
    return curr_dir

def relative_root_path(path):
    path = os.path.realpath(path)
    root = dirs.root()

    if root[-len(os.sep):] != os.sep:
        root = root + os.sep
    
    if len(path) < len(root) or path[:len(root)] != root:
        raise Exception("error: Path does not belong to project. Received {} which was expected to be found within {}.".format(path, root))

    return path[len(root):]


class Directories:
    def __init__(self):
        root = find_root_dir()

        self._init_q = root != None
        if self._init_q:
            self.set_root(root)
    
    def set_root(self, root):
        exp_path = os.path.join(root, '.exp')
        os.makedirs(exp_path, exist_ok=True)

        _dirs['root'] = root
        _dirs['exp'] = exp_path

        self._init_q = True
    
    def root(self):
        if not self._init_q:
            print("error: Could not find '.exp' folder. Try running 'xlab project init' on your project root directory.")
            exit(1)
        return _dirs['root']

    def exp_path(self):
        if not self._init_q:
            print("error: Could not find '.exp' folder. Try running 'xlab project init' on your project root directory.")
            exit(1)
        return _dirs['exp']

    def runs_path(self):
        if 'runs' not in _dirs:
            root = self.root()

            runs_path = os.path.join(root, 'runs')
            os.makedirs(runs_path, exist_ok=True)

            _dirs['runs'] = runs_path

        return _dirs['runs']

dirs = Directories()



class MetadataLoader:
    def __init__(self, path, name):
        filename = '{}.json'.format(name)
        self.path = os.path.join(path, filename)

        lock_filename = '.{}.lock'.format(name)
        lock_path = os.path.join(path, lock_filename)
        self.lock = fasteners.InterProcessReaderWriterLock(lock_path)

        self.lock.acquire_write_lock()
        if not os.path.exists(self.path):
            with open(self.path, 'w') as out_file:
                json.dump({
                    'next_id': 0
                }, out_file)
        self.lock.release_write_lock()
    
    def next_id(self):
        self.lock.acquire_write_lock()
        with open(self.path, 'r') as in_file:
            metadata = json.load(in_file)

        id = metadata['next_id']
        metadata['next_id'] += 1

        with open(self.path, 'w') as out_file:
            json.dump(metadata, out_file)
        self.lock.release_write_lock()

        return id



class HashmapLoader:
    def __init__(self, path, name):
        filename = '{}.pkl'.format(name)
        self.path = os.path.join(path, filename)

        lock_filename = '.{}.lock'.format(name)
        lock_path = os.path.join(path, lock_filename)
        self.lock = fasteners.InterProcessReaderWriterLock(lock_path)
        self.locked_q = False

        self.lock.acquire_write_lock()
        if not os.path.exists(self.path):
            with open(self.path, 'wb') as out_file:
                pickle.dump({}, out_file)
        self.lock.release_write_lock()
    
    def load(self):
        assert not self.locked_q

        self.lock.acquire_read_lock()
        with open(self.path, 'rb') as in_file:
            hashmap = pickle.load(in_file)
        self.lock.release_read_lock()

        return hashmap
    
    def load_and_lock_acquire(self):
        assert not self.locked_q
        self.locked_q = True

        self.lock.acquire_write_lock()
        with open(self.path, 'rb') as in_file:
            hashmap = pickle.load(in_file)
        
        return hashmap
    
    def save_and_lock_release(self, hashmap):
        assert self.locked_q
        self.locked_q = False

        with open(self.path, 'wb') as out_file:
            pickle.dump(hashmap, out_file)
        self.lock.release_write_lock()

import os
import sys
import json
import pickle
import fasteners

_dirs = {}


def find_root_dir():
    """Returns the location of the project directory if found."""

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
    """Returns a path relative to the project directory."""
    
    path = os.path.realpath(path)
    root = dirs.root()

    if root[-len(os.sep):] != os.sep:
        root = root + os.sep
    
    if len(path) < len(root) or path[:len(root)] != root:
        raise Exception(
            'error: Path does not belong to project. Received {} ' \
            'which was expected to be found within {}.'.format(path, root))

    return path[len(root):]



class Directories:
    def __init__(self):
        """Initializes directory structure."""

        root = find_root_dir()

        self._init_q = root != None
        if self._init_q:
            self.set_root(root)
    
    def set_root(self, root):
        """Sets up the root project, if not set already.
        
        Args:
            root: string path where the project will be initialized.
        """

        exp_path = os.path.join(root, '.exp')
        os.makedirs(exp_path, exist_ok=True)

        _dirs['root'] = root
        _dirs['exp'] = exp_path

        self._init_q = True
    
    def root(self):
        """Returns the root directory."""

        if not self._init_q:
            print(
                "error: Could not find '.exp' folder. Try running " \
                "'xlab project init' on your project root directory.")
            exit(1)
        return _dirs['root']

    def exp_path(self):
        """Returns the metadata directory."""

        if not self._init_q:
            print(
                "error: Could not find '.exp' folder. Try running " \
                "'xlab project init' on your project root directory.")
            exit(1)
        return _dirs['exp']

    def runs_path(self):
        """Returns the path reserved for runs."""

        if 'runs' not in _dirs:
            root = self.root()

            runs_path = os.path.join(root, 'runs')
            os.makedirs(runs_path, exist_ok=True)

            _dirs['runs'] = runs_path

        return _dirs['runs']

dirs = Directories()



class MetadataLoader:
    def __init__(self, path, name):
        """Initializes files for metadata read and write operations.

        The metadata is saved as a .json file.
        
        Args:
            path: string path where metadata will be saved.
            name: string for the name of the metadata file.
        """

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
        """Provides the next available run id."""

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
        """Initializes files for hashmap read and write operations.

        A hashmap is saved as a .pkl file.
        
        Args:
            path: string path where hashmap will be saved.
            name: string for the name of the hashmap file.
        """

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
        """Read-only operation that returns the hashmap."""

        assert not self.locked_q

        self.lock.acquire_read_lock()
        with open(self.path, 'rb') as in_file:
            hashmap = pickle.load(in_file)
        self.lock.release_read_lock()

        return hashmap
    
    def load_and_lock_acquire(self):
        """Read operation that returns the hashmap.
        
        A write lock is acquired after this call, so one MUST call
        save_and_lock_release to release the lock. The updates made to
        the hashmap are saved on this last call.
        """

        assert not self.locked_q
        self.locked_q = True

        self.lock.acquire_write_lock()
        with open(self.path, 'rb') as in_file:
            hashmap = pickle.load(in_file)
        
        return hashmap
    
    def save_and_lock_release(self, hashmap):
        """Write operation that saved the hashmap.
        
        This method is designed to be used after a call to
        load_and_lock_acquire, because it releases the write lock set
        on the hashmap load operation. The updates made to the hashmap
        are saved on this call.

        Args:
            hashmap: dict that associates hashes to some data. Since
                the hashmap is saved as a .pkl file, there is no
                restriction on the data to be assigned to a key.
        """

        assert self.locked_q
        self.locked_q = False

        with open(self.path, 'wb') as out_file:
            pickle.dump(hashmap, out_file)
        self.lock.release_write_lock()

import os
import sys
import json
import pickle
import fasteners

# Dict of directories
_dirs = {}


def find_root_dir():
    """Returns the location of the project directory if found."""

    # Get the current working directory
    try:
        filename = os.path.realpath(sys.argv[0])
        dirname = os.path.dirname(filename) if os.path.isfile(filename) else filename

        curr_dir = dirname
    except:
        curr_dir = os.getcwd()
    
    abs_root = os.path.abspath(os.sep)

    # Exit directories in a bottom-up fashion until .exp dir is found
    while curr_dir != abs_root and '.exp' not in os.listdir(curr_dir):
        curr_dir = os.path.dirname(curr_dir)
    
    if '.exp' not in os.listdir(curr_dir):
        curr_dir = None
    
    return curr_dir


def relative_root_path(path):
    """Returns a path relative to the project directory."""
    
    # Take project path as a reference
    path = os.path.realpath(path)
    root = dirs.root()

    # Add trailing dir separator if not present already
    if root[-len(os.sep):] != os.sep:
        root = root + os.sep
    
    # Validate that path is found within project path
    if len(path) < len(root) or path[:len(root)] != root:
        raise Exception(
            'error: Path does not belong to project. Received {} ' \
            'which was expected to be found within {}.'.format(path, root))

    # Extract root from path to make path relative to the project path
    return path[len(root):]



class Directories:
    def __init__(self):
        """Initializes directory structure."""

        # Project path
        root = find_root_dir()

        self._init_q = root != None
        if self._init_q:
            self.set_root(root)
    
    def set_root(self, root):
        """Sets up the root project, if not set already.
        
        Args:
            root: string path where the project will be initialized.
        """

        # Create .exp dir on project path
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

        # Automatically creates runs on project path dir when called
        if 'runs' not in _dirs:
            root = self.root()

            runs_path = os.path.join(root, 'runs')
            os.makedirs(runs_path, exist_ok=True)

            _dirs['runs'] = runs_path

        return _dirs['runs']

# Initialize dirs as a global object
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
        ### Start of critical region

        # If metadata doesn't exist, it is created and filled with
        # default values. So far, the keys are
        #   * next_id: stores the next results dir id to be taken
        if not os.path.exists(self.path):
            with open(self.path, 'w') as out_file:
                json.dump({
                    'next_id': 0
                }, out_file)

        ### End of critical region
        self.lock.release_write_lock()
    
    def next_id(self):
        """Provides the next available run id."""

        self.lock.acquire_write_lock()
        ### Start of critical region

        with open(self.path, 'r') as in_file:
            metadata = json.load(in_file)

        # Get id and update on metadata for future calls to next_id
        id = metadata['next_id']
        metadata['next_id'] += 1

        with open(self.path, 'w') as out_file:
            json.dump(metadata, out_file)

        ### End of critical region
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
        ### Start of critical region

        # If hashmap doesn't exist, save it as empty
        if not os.path.exists(self.path):
            with open(self.path, 'wb') as out_file:
                pickle.dump({}, out_file)
        
        ### End of critical region
        self.lock.release_write_lock()
    
    def load(self):
        """Read-only operation that returns the hashmap."""

        assert not self.locked_q

        self.lock.acquire_read_lock()
        ### Start of critical region

        with open(self.path, 'rb') as in_file:
            hashmap = pickle.load(in_file)
        
        ### End of critical region
        self.lock.release_read_lock()

        return hashmap
    
    def load_and_lock_acquire(self):
        """Read operation that returns the hashmap.
        
        A write lock is acquired after this call, so one MUST call
        save_and_lock_release to release the lock. The updates made to
        the hashmap are saved on this last call.
        """

        # This assert makes sure we don't fall into a deadlock,
        # because one must call save_and_lock_release first (which
        # releases the lock) to make the assert pass
        assert not self.locked_q
        self.locked_q = True

        self.lock.acquire_write_lock()
        ### Start of critical region

        with open(self.path, 'rb') as in_file:
            hashmap = pickle.load(in_file)
        
        # Remember to call save_and_lock_release to close the
        # critical region, which is open up until this line
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

        # This assert makes sure we don't call this method without
        # calling load_and_lock_acquire immediately before. We cannot
        # release a lock if it hasn't been acquired first
        assert self.locked_q
        self.locked_q = False

        with open(self.path, 'wb') as out_file:
            pickle.dump(hashmap, out_file)
        
        ### End of critical region
        self.lock.release_write_lock()

import json
import hashlib
import copy
import os

from xlab import filesys


def sort_args(args):
    """Sorts keys from dicts (including nested dicts).
    
    Args:
        args: regular dictionary.
    """

    # Note dicts are sorted recursivelly within lists and dicts
    args = copy.deepcopy(args)
    if type(args) == dict:
        for key in args:
            args[key] = sort_args(args[key])
        return sorted(args.items())
    if type(args) == list:
        # Lists are not sorted, they might encode positional info
        return [sort_args(x) for x in args]

    return args



# Cache functions
def get_args_hash(args):
    """Returns a unique identifier (hash) for a dict.
    
    Args:
        args: JSON-like dictionary.
    """

    json_string = json.dumps(sort_args(args), separators=(',', ':'))
    hash = hashlib.sha224(json_string.encode('utf-8')).hexdigest()
    return hash


def get_hash(args_or_hash):
    """Returns a hash-like string from either a dict or string.

    In case args_or_hash is already an string, it is assumed to be
    a hash.
    
    Args:
        args_or_hash: input dict or hash-like string.
    """

    if type(args_or_hash) == dict:
        hash = get_args_hash(args_or_hash)
    elif type(args_or_hash) == str:
        hash = args_or_hash
    
    return hash



# Cache class
class Cache:
    def __init__(self):
        """Sets up cache."""

        self.metadata_loader = filesys.MetadataLoader(
            filesys.dirs.exp_path(), 'metadata')
        self.hashmap_loader = filesys.HashmapLoader(
            filesys.dirs.exp_path(), 'hashmap')

    def exists(self, args_or_hash):
        """Determines if hash is found on cache.
        
        Args:
            args_or_hash: input dict or hash-like string.
        """

        hash = get_hash(args_or_hash)
        hashmap = self.hashmap_loader.load()

        return hash in hashmap

    def is_complete(self, args_or_hash):
        """Determines if a run identified by a hash has completed.
        
        Args:
            args_or_hash: input dict or hash-like string.
        """

        hash = get_hash(args_or_hash)
        hashmap = self.hashmap_loader.load()

        # Note that run's hashmap output is a list, and completion
        # status is saved on the 2nd slot.
        return hash in hashmap and hashmap[hash][1]

    def get_dir(self, args_or_hash):
        """Returns the directory associated with the hash.
        
        Args:
            args_or_hash: input dict or hash-like string.
        """

        hash = get_hash(args_or_hash)
        hashmap = self.hashmap_loader.load()

        if hash in hashmap:
            # Note that run's hashmap output is a list, and the run's
            # dir is saved on the 1st slot.
            return hashmap[hash][0]
        else:
            raise Exception('error: Hash not found in cache.')



    def assign_dir(self, args):
        """Assigns a new directory to a run.

        Args:
            args: input dict that represents a run.
        """

        id = self.metadata_loader.next_id()
        path = os.path.join(filesys.dirs.runs_path(), str(id))
        hash = get_hash(args)

        hashmap = self.hashmap_loader.load_and_lock_acquire()
        ##### Start of critical region

        # The hash is assigned a run's path and completion status
        hashmap[hash] = [path, False]

        ##### End of critical region
        self.hashmap_loader.save_and_lock_release(hashmap)
        
        return path

    def set_complete(self, args_or_hash):
        """Sets a run represented by a hash as complete.

        Args:
            args_or_hash: input dict or hash-like string.
        """

        hash = get_hash(args_or_hash)

        hashmap = self.hashmap_loader.load_and_lock_acquire()
        ##### Start of critical region

        # Update completion status from hash
        hashmap[hash][1] = True

        ##### End of critical region
        self.hashmap_loader.save_and_lock_release(hashmap)

    def merge_hashes(self, new_hash, old_hash):
        """Assigns the same cache bucket to both hashes.

        In detail, new_hash is assigned the same bucket as old_hash.
        For this reason, any bucket assigned to new_hash is lost.

        Args:
            args_or_hash: input dict or hash-like string.
        """

        hashmap = self.hashmap_loader.load_and_lock_acquire()
        ##### Start of critical region

        # Copy save dir and completion status assigned from old_hash
        # to new_hash
        hashmap[new_hash] = hashmap[old_hash]

        ##### End of critical region
        self.hashmap_loader.save_and_lock_release(hashmap)

import json
import hashlib
import copy
import os

from . import filesys

# Cache functions
def get_args_hash(args):
    hash = hashlib.sha224(json.dumps(sorted(args.items()), separators=(',', ':')).encode('utf-8')).hexdigest()
    return hash

def get_hash(args_or_hash):
    if type(args_or_hash) == dict:
        hash = get_args_hash(args_or_hash)
    elif type(args_or_hash) == str:
        hash = args_or_hash
    
    return hash

# Cache class
class Cache:
    def __init__(self):
        self.metadata_loader = filesys.MetadataLoader(filesys.dirs.exp_path(), 'metadata')
        self.hashmap_loader = filesys.HashmapLoader(filesys.dirs.exp_path(), 'hashmap')

    def exists(self, args_or_hash):
        hash = get_hash(args_or_hash)
        hashmap = self.hashmap_loader.load()

        return hash in hashmap

    def is_complete(self, args_or_hash):
        hash = get_hash(args_or_hash)
        hashmap = self.hashmap_loader.load()

        return hash in hashmap and hashmap[hash][1]

    def get_dir(self, args_or_hash):
        hash = get_hash(args_or_hash)
        hashmap = self.hashmap_loader.load()

        if hash in hashmap:
            return hashmap[hash][0]
        else:
            raise Exception('error: Hash not found in cache.')

    def assign_dir(self, args):
        id = self.metadata_loader.next_id()
        path = os.path.join(filesys.dirs.runs_path(), str(id))
        hash = get_hash(args)

        hashmap = self.hashmap_loader.load_and_lock_acquire()
        hashmap[hash] = [path, False]
        self.hashmap_loader.save_and_lock_release(hashmap)
        
        return path

    def set_complete(self, args_or_hash):
        hash = get_hash(args_or_hash)

        hashmap = self.hashmap_loader.load_and_lock_acquire()
        hashmap[hash][1] = True
        self.hashmap_loader.save_and_lock_release(hashmap)
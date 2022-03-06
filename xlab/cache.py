import pickle
import json
import hashlib
import copy
import os
import fasteners

exp_path = '.exp'
runs_path = 'runs'

metadata_path = os.path.join(exp_path, 'metadata.json')
hashmap_path = os.path.join(exp_path, 'hashmap.pkl')

metadata_lock_path = os.path.join(exp_path, '.metadata.lock')
hashmap_lock_path = os.path.join(exp_path, '.hashmap.lock')

hashmap_lock = fasteners.InterProcessReaderWriterLock(hashmap_lock_path)
metadata_lock = fasteners.InterProcessReaderWriterLock(metadata_lock_path)

# Setup .exp and runs
if not os.path.exists(exp_path):
    os.makedirs(exp_path, exist_ok=True)

if not os.path.exists(runs_path):
    os.makedirs(runs_path, exist_ok=True)

if not os.path.exists(metadata_path):
    metadata_lock.acquire_read_lock()
    with open(metadata_path, 'w') as out_file:
        json.dump({
            'next_id': 0
        }, out_file)
    metadata_lock.release_read_lock()

if not os.path.exists(hashmap_path):
    hashmap_lock.acquire_read_lock()
    with open(hashmap_path, 'wb') as out_file:
        pickle.dump({}, out_file)
    hashmap_lock.release_read_lock()

# Cache functions
def get_hash(args):
    hash = hashlib.sha224(json.dumps(sorted(args.items()), separators=(',', ':')).encode('utf-8')).hexdigest()
    return hash

def exists(args):
    if type(args) == dict:
        hash = get_hash(args)
    elif type(args) == str:
        hash = args

    hashmap_lock.acquire_read_lock()
    with open(hashmap_path, 'rb') as in_file:
        cache = pickle.load(in_file)
    hashmap_lock.release_read_lock()

    return hash in cache

def is_complete(args):
    if type(args) == dict:
        hash = get_hash(args)
    elif type(args) == str:
        hash = args

    hashmap_lock.acquire_read_lock()
    with open(hashmap_path, 'rb') as in_file:
        cache = pickle.load(in_file)
    hashmap_lock.release_read_lock()

    return hash in cache and cache[hash][1]

def get_dir(args):
    if type(args) == dict:
        hash = get_hash(args)
    elif type(args) == str:
        hash = args

    hashmap_lock.acquire_read_lock()
    with open(hashmap_path, 'rb') as in_file:
        cache = pickle.load(in_file)
    hashmap_lock.release_read_lock()

    if hash in cache:
        return cache[hash][0]
    else:
        raise Exception('error: Hash not found in cache.')

def assign_dir(args):
    metadata_lock.acquire_write_lock()
    with open(metadata_path, 'r') as in_file:
        metadata = json.load(in_file)

    id = metadata['next_id']
    metadata['next_id'] += 1

    with open(metadata_path, 'w') as out_file:
        json.dump(metadata, out_file)
    metadata_lock.release_write_lock()


    path = os.path.join(runs_path, str(id))
    hash = get_hash(args)

    hashmap_lock.acquire_write_lock()
    with open(hashmap_path, 'rb') as in_file:
        cache = pickle.load(in_file)

    cache[hash] = [path, False]

    with open(hashmap_path, 'wb') as out_file:
        pickle.dump(cache, out_file)
    hashmap_lock.release_write_lock()
    
    return path

def set_complete(args):
    if type(args) == dict:
        hash = get_hash(args)
    elif type(args) == str:
        hash = args

    hashmap_lock.acquire_write_lock()
    with open(hashmap_path, 'rb') as in_file:
        cache = pickle.load(in_file)

    cache[hash][1] = True

    with open(hashmap_path, 'wb') as out_file:
        pickle.dump(cache, out_file)
    hashmap_lock.release_write_lock()
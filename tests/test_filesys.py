import os

import pytest
import json
import pickle

from xlab.filesys import dirs, find_root_dir, Directories
from xlab.filesys import MetadataLoader, HashmapLoader

from .fixtures import xlab_project_missing, xlab_project_init



##### FIXTURES

@pytest.fixture(scope='function')
def dir_structure(tmpdir):
    # Root dir
    # .../
    a = tmpdir.mkdir('a')
    b = tmpdir.mkdir('b')

    # .../a: is a project
    a.mkdir('.exp')
    a_a = a.mkdir('a')
    a_b = a.mkdir('b')
    a_c = a.mkdir('c')

    # .../a/a: no nested projects
    a_a_a = a_a.mkdir('a')
    a_a_deep = a_a_a.mkdir('a').mkdir('a').mkdir('a')

    # .../a/b: deep nested project
    a_b_a = a_b.mkdir('a')
    a_b_a.mkdir('.exp')
    a_b_a_a = a_b_a.mkdir('a')
    a_b_deep = a_b_a_a.mkdir('a').mkdir('a').mkdir('a')

    # .../a/c: immediately nested project
    a_c.mkdir('.exp')
    a_c_a = a_c.mkdir('a')
    a_c_deep = a_c_a.mkdir('a').mkdir('a').mkdir('a')

    # .../b: is not a project
    b_a = b.mkdir('a')
    b_deep = b_a.mkdir('a').mkdir('a').mkdir('a')

    return tmpdir



##### TESTS

### Utilily functions

# @pytest.mark.usefixtures('create_directory_structure')
@pytest.mark.parametrize(('path', 'root'), [
    # Root tests
    ([], None),
    (['a'], ['a']),
    (['b'], None),

    # No nested projects
    (['a', 'a'], ['a']),
    (['a', 'a', 'a'], ['a']),
    (['a', 'a', 'a', 'a', 'a', 'a'], ['a']),

    # Deep nested project
    (['a', 'b'], ['a']),
    (['a', 'b', 'a'], ['a', 'b', 'a']),
    (['a', 'b', 'a', 'a'], ['a', 'b', 'a']),
    (['a', 'b', 'a', 'a', 'a', 'a'], ['a', 'b', 'a']),

    # Immediately nested project
    (['a', 'c'], ['a', 'c']),
    (['a', 'c', 'a'], ['a', 'c']),
    (['a', 'c', 'a', 'a', 'a'], ['a', 'c']),

    # Not a project
    (['b', 'a'], None),
    (['b', 'a', 'a', 'a', 'a'], None),
])
def test_find_root_dir(dir_structure, path, root):
    path = os.path.join(dir_structure, *path)
    root = os.path.join(dir_structure, *root) if root is not None else None

    assert find_root_dir(path) == root


@pytest.mark.skip(reason='not clear what behavior should be met for root dirs')
@pytest.mark.parametrize(('path'), [

])
def test_relative_root_path(dir_structure, path):
    # TODO: Pending tests

    assert dir_structure



### class Directories

def test_directories_set_root(xlab_project_missing):
    directories = Directories(xlab_project_missing['curdir'])
    directories.set_root(xlab_project_missing['root'])

    exp_path = os.path.join(xlab_project_missing['root'], '.exp')

    assert os.path.exists(exp_path)


def test_directories_root(xlab_project_init):
    directories = Directories(xlab_project_init['curdir'])

    root = directories.root()
    assert root == xlab_project_init['root']


def test_directories_exp_path(xlab_project_init):
    directories = Directories(xlab_project_init['root'])

    exp_path = os.path.join(xlab_project_init['root'], '.exp')
    assert directories.exp_path() == exp_path


def test_directories_runs_path(xlab_project_init):
    directories = Directories(xlab_project_init['curdir'])

    runs_path = os.path.join(xlab_project_init['root'], 'runs')

    assert not os.path.exists(runs_path)
    assert directories.runs_path() == runs_path
    assert os.path.exists(runs_path)



### class MetadataLoader

def test_metadataloader_init(tmpdir):
    name = 'metadata'
    MetadataLoader(tmpdir, name)
    metadata_path = os.path.join(tmpdir, '{}.json'.format(name))

    assert os.path.exists(metadata_path)
    assert os.path.exists(os.path.join(tmpdir, '.{}.lock'.format(name)))
    
    with open(metadata_path, 'r') as in_file:
        metadata = json.load(in_file)
    
    assert 'next_id' in metadata
    assert metadata['next_id'] == 0


def test_metadataloader_next_id(tmpdir):
    name = 'metadata'
    metadata_loader = MetadataLoader(tmpdir, name)
    metadata_path = os.path.join(tmpdir, '{}.json'.format(name))
    next_id = metadata_loader.next_id()

    assert next_id == 0
    
    with open(metadata_path, 'r') as in_file:
        metadata = json.load(in_file)

    assert metadata['next_id'] == 1



### class HashmapLoader

def test_hashmaploader_init(tmpdir):
    name = 'hashmap'
    HashmapLoader(tmpdir, name)
    hashmap_path = os.path.join(tmpdir, '{}.pkl'.format(name))

    assert os.path.exists(hashmap_path)
    assert os.path.exists(os.path.join(tmpdir, '.{}.lock'.format(name)))
    
    with open(hashmap_path, 'rb') as in_file:
        hashmap = pickle.load(in_file)
    
    assert hashmap == {}


def test_hashmaploader_load(tmpdir):
    name = 'hashmap'
    hashmap_loader = HashmapLoader(tmpdir, name)
    hashmap = hashmap_loader.load()

    assert hashmap == {}


@pytest.mark.skip(reason='not sure how to design test')
def test_hashmaploader_load_and_lock_acquire(tmpdir):
    name = 'hashmap'
    hashmap_loader = HashmapLoader(tmpdir, name)
    hashmap = hashmap_loader.load_and_lock_acquire()


@pytest.mark.skip(reason='not sure how to design test')
def test_hashmaploader_save_and_lock_release(tmpdir):
    name = 'hashmap'
    hashmap_loader = HashmapLoader(tmpdir, name)
    hashmap_loader.save_and_lock_release({})
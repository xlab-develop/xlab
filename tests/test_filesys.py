import pytest
import os

from xlab.filesys import find_root_dir, Directories


@pytest.fixture(scope='function')
def tmp_root_dir(tmpdir):
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
def test_find_root_dir(tmp_root_dir, path, root):
    path = os.path.join(tmp_root_dir, *path)
    root = os.path.join(tmp_root_dir, *root) if root is not None else None

    assert find_root_dir(path) == root


@pytest.mark.skip(reason='not clear what behavior should be met for root dirs')
@pytest.mark.parametrize(('path'), [
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
def test_relative_root_path(tmp_root_dir, path):
    assert tmp_root_dir
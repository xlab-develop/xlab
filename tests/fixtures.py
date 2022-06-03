import os
import shutil

import pytest
import json

from xlab.filesys import dirs


@pytest.fixture()
def xlab_project_missing(tmpdir):
    subdirs = [
        ['b'],
        ['a']
    ]

    path = tmpdir
    for subdir in subdirs:
        relative_path = os.path.join(*subdir) if type(subdir) == list else subdir
        path = os.path.join(tmpdir, relative_path)

        os.makedirs(path, exist_ok=True)
    
    future_curdir = path

    tests_path = os.path.dirname(os.path.realpath(__file__))
    templates_path = os.path.join(tests_path, 'script_templates')

    for filename in ['sampler.py', 'run.py', 'plot.py']:
        src_path = os.path.join(templates_path, filename)
        dst_path = os.path.join(future_curdir, filename)
    
        shutil.copyfile(src_path, dst_path)

    shutil.copyfile(
        os.path.join(templates_path, 'sampler.py'),
        os.path.join(tmpdir, 'b', 'sampler.py'))

    results_path = os.path.join(tmpdir, 'results.json')
    with open(results_path, 'w') as out_file:
        json.dump({}, out_file)

    return {
        'root': tmpdir,
        'curdir': future_curdir,
    }


@pytest.fixture()
def xlab_project_init(xlab_project_missing):
    dirs.set_root(xlab_project_missing['root'])

    return xlab_project_missing
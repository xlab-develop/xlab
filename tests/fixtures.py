import os
import shutil

import pytest


@pytest.fixture()
def project_setup(tmpdir, request):
    subdirs = request.param

    os.makedirs(os.path.join(tmpdir, '.exp'), exist_ok=True)

    path = tmpdir
    for subdir in subdirs:
        relative_path = os.path.join(*subdir) if type(subdir) == list else subdir
        path = os.path.join(tmpdir, relative_path)

        os.makedirs(path, exist_ok=True)
    
    future_curdir = path

    dirname = os.path.dirname(os.path.realpath(__file__))
    template_path = os.path.join(dirname, 'script_templates', 'main.py')
    script_path = os.path.join(future_curdir, 'main.py')

    shutil.copyfile(template_path, script_path)

    return {
        'root': tmpdir,
        'curdir': future_curdir,
        'script': script_path,
    }
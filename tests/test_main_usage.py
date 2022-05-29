import os

import pytest

from .fixtures import project_setup

@pytest.mark.parametrize('project_setup', [([])], indirect=True)
def test_normal_experiment(project_setup):
    script_path = project_setup['script']

    os.system('python {} a'.format(script_path))

    runs_path = os.path.join(project_setup['root'], 'runs')

    assert os.path.exists(runs_path)
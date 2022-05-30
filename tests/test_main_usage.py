import os

import pytest
import json

from .fixtures import project_setup


@pytest.mark.parametrize('project_setup', [([])], indirect=True)
def test_runs_dir_created(project_setup):
    path = project_setup['curdir']
    sampler_path = os.path.join(path, 'sampler.py')

    runs_path = os.path.join(project_setup['root'], 'runs')

    assert not os.path.exists(runs_path)

    os.system('python {} linear 0'.format(sampler_path))

    assert os.path.exists(runs_path)


@pytest.mark.parametrize('reps', [1, 10, 100])
@pytest.mark.parametrize('project_setup', [([])], indirect=True)
def test_run_results_saved(project_setup, reps):
    path = project_setup['curdir']
    sampler_path = os.path.join(path, 'sampler.py')
    
    os.system('python {} linear 0 --repetitions {}'.format(sampler_path, reps))

    test_results_path = os.path.join(project_setup['root'], 'test_data.json')
    with open(test_results_path, 'r') as in_file:
        test_results = json.load(in_file)
    
    assert len(test_results['sampler_data']) > 0
    assert test_results['sampler_data'][0]['data'] == [0 for _ in range(reps)]


@pytest.mark.parametrize('project_setup', [([])], indirect=True)
def test_run_once_cached(project_setup):
    path = project_setup['curdir']
    sampler_path = os.path.join(path, 'sampler.py')
    
    os.system('python {} linear 0'.format(sampler_path))


    test_results_path = os.path.join(project_setup['root'], 'test_data.json')
    with open(test_results_path, 'r') as in_file:
        test_results = json.load(in_file)

    assert test_results['sampler_calls'] == 1

    os.system('python {} linear 0'.format(sampler_path))

    with open(test_results_path, 'r') as in_file:
        test_results = json.load(in_file)
    
    assert test_results['sampler_calls'] == 1


@pytest.mark.parametrize('project_setup', [([])], indirect=True)
def test_run_force_repeated(project_setup):
    path = project_setup['curdir']
    sampler_path = os.path.join(path, 'sampler.py')
    
    os.system('python {} linear 0 --exp-force'.format(sampler_path))


    test_results_path = os.path.join(project_setup['root'], 'test_data.json')
    with open(test_results_path, 'r') as in_file:
        test_results = json.load(in_file)

    assert test_results['sampler_calls'] == 1

    os.system('python {} linear 0 --exp-force'.format(sampler_path))

    with open(test_results_path, 'r') as in_file:
        test_results = json.load(in_file)
    
    assert test_results['sampler_calls'] == 2


@pytest.mark.parametrize('project_setup', [([])], indirect=True)
def test_run_force_repeated(project_setup):
    path = project_setup['curdir']
    sampler_path = os.path.join(path, 'sampler.py')
    
    os.system('python {} linear 0 --exp-force'.format(sampler_path))


    test_results_path = os.path.join(project_setup['root'], 'test_data.json')
    with open(test_results_path, 'r') as in_file:
        test_results = json.load(in_file)

    assert test_results['sampler_calls'] == 1

    os.system('python {} linear 0 --exp-force'.format(sampler_path))

    with open(test_results_path, 'r') as in_file:
        test_results = json.load(in_file)
    
    assert test_results['sampler_calls'] == 2
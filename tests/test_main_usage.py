import os

import pytest
import json

from .fixtures import xlab_project_missing, xlab_project_init


def test_runs_dir_created(xlab_project_init):
    path = xlab_project_init['curdir']
    sampler_path = os.path.join(path, 'sampler.py')

    runs_path = os.path.join(xlab_project_init['root'], 'runs')

    assert not os.path.exists(runs_path)

    os.system('python {} linear 0'.format(sampler_path))

    assert os.path.exists(runs_path)


@pytest.mark.parametrize('reps', [1, 10, 100])
def test_run_results_saved(xlab_project_init, reps):
    path = xlab_project_init['curdir']
    sampler_path = os.path.join(path, 'sampler.py')
    
    os.system('python {} linear 0 --repetitions {}'.format(sampler_path, reps))

    test_results_path = os.path.join(xlab_project_init['root'], 'test_data.json')
    with open(test_results_path, 'r') as in_file:
        test_results = json.load(in_file)
    
    assert len(test_results['sampler_data']) > 0
    assert test_results['sampler_data'][0]['data'] == [0 for _ in range(reps)]


def test_run_once_cached(xlab_project_init):
    path = xlab_project_init['curdir']
    sampler_path = os.path.join(path, 'sampler.py')
    
    os.system('python {} linear 0'.format(sampler_path))

    test_results_path = os.path.join(xlab_project_init['root'], 'test_data.json')
    with open(test_results_path, 'r') as in_file:
        test_results = json.load(in_file)

    assert test_results['sampler_calls'] == 1

    os.system('python {} linear 0'.format(sampler_path))

    with open(test_results_path, 'r') as in_file:
        test_results = json.load(in_file)
    
    assert test_results['sampler_calls'] == 1


def test_run_force_repeated(xlab_project_init):
    path = xlab_project_init['curdir']
    sampler_path = os.path.join(path, 'sampler.py')
    
    os.system('python {} linear 0 --exp-force'.format(sampler_path))

    test_results_path = os.path.join(xlab_project_init['root'], 'test_data.json')
    with open(test_results_path, 'r') as in_file:
        test_results = json.load(in_file)

    assert test_results['sampler_calls'] == 1

    os.system('python {} linear 0 --exp-force'.format(sampler_path))

    with open(test_results_path, 'r') as in_file:
        test_results = json.load(in_file)
    
    assert test_results['sampler_calls'] == 2


def test_run_index_by_executable(xlab_project_init):
    root = xlab_project_init['root']
    sampler_a_path = os.path.join(root, 'a', 'sampler.py')
    sampler_b_path = os.path.join(root, 'b', 'sampler.py')
    
    os.system('python {} linear 0'.format(sampler_a_path))
    os.system('python {} linear 0'.format(sampler_b_path))

    test_results_path = os.path.join(xlab_project_init['root'], 'test_data.json')
    with open(test_results_path, 'r') as in_file:
        test_results = json.load(in_file)

    assert test_results['sampler_calls'] == 2
    
    sampler_data = test_results['sampler_data']
    assert sampler_data[0]['data'] == sampler_data[1]['data']
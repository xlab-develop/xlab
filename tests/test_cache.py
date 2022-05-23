import pytest

from xlab.cache import get_hash

@pytest.mark.parametrize(('a', 'b', 'eq'), [
    ### Hash equivalence tests

    # Hashes should be equal:
    ({'a':0}, {'a':0}, True),
    ({'a':0}, {'a':0}, True),
    ({'a':1.}, {'a':1.}, True),
    ({'a':'x'}, {'a':'x'}, True),
    ({'a':0, 'b':1., 'c':'x'}, {'a':0, 'b':1., 'c':'x'}, True),
    ({'a':[]}, {'a':[]}, True),
    ({'a':[0, 1, 2]}, {'a':[0, 1, 2]}, True),
    ({'a':{'k':0}}, {'a':{'k':0}}, True),
    ({'a':{'k':0, 'q':1}}, {'a':{'k':0, 'q':1}}, True),
    ({'a':[{'k':0, 'q':1}]}, {'a':[{'k':0, 'q':1}]}, True),

    # Hashes should be different:
    ({'a':0}, {'a':1}, False),
    ({'a':0}, {'b':0}, False),
    ({'a':0}, {'a':0, 'b':0}, False),
    ({'a':0}, {'a':[0]}, False),
    ({'a':0}, {'a':{'k':0}}, False),
    ({'a':0}, {'a':{'k':0}}, False),

    
    ### Hash order invariance tests

    # Key order invariant dicts
    ({'a':0, 'b':1}, {'b':1, 'a':0}, True),
    ({'a':0, 'b':1, 'c':2}, {'b':1, 'a':0, 'c':2}, True),
    ({'a':0, 'b':1, 'c':2}, {'c':2, 'a':0, 'b':1}, True),
    ({'a':{'k':0, 'q':1}}, {'a':{'q':1, 'k':0}}, True),
    
    # Order-sensitive lists
    ({'a':[0, 1]}, {'a':[1, 0]}, False),
    
    
    ### Mixed tests
    ({'a':[{'k':0}, {'q':1}]}, {'a':[{'q':1}, {'k':0}]}, False),
    ({'a':{'k':[0], 'q':[1]}}, {'a':{'q':[1], 'k':[0]}}, True),
    ({'b':2, 'a':{'k':0, 'q':1}}, {'a':{'q':1, 'k':0}, 'b':2}, True),
])
def test_get_hash(a, b, eq):
    assert (get_hash(a) == get_hash(b)) == eq
    # ### Hash equivalence tests

    # # Hashes should be equal:
    # assert get_hash({}) == get_hash({})
    # assert get_hash({'a':0}) == get_hash({'a':0})
    # assert get_hash({'a':1.}) == get_hash({'a':1.})
    # assert get_hash({'a':'x'}) == get_hash({'a':'x'})
    # assert get_hash({'a':0, 'b':1., 'c':'x'}) == get_hash({'a':0, 'b':1., 'c':'x'})
    # assert get_hash({'a':[]}) == get_hash({'a':[]})
    # assert get_hash({'a':[0, 1, 2]}) == get_hash({'a':[0, 1, 2]})
    # assert get_hash({'a':{'k':0}}) == get_hash({'a':{'k':0}})
    # assert get_hash({'a':{'k':0, 'q':1}}) == get_hash({'a':{'k':0, 'q':1}})
    # assert get_hash({'a':[{'k':0, 'q':1}]}) == get_hash({'a':[{'k':0, 'q':1}]})

    # # Hashes should be different:
    # assert get_hash({'a':0}) != get_hash({'a':1})
    # assert get_hash({'a':0}) != get_hash({'b':0})
    # assert get_hash({'a':0}) != get_hash({'a':0, 'b':0})
    # assert get_hash({'a':0}) != get_hash({'a':[0]})
    # assert get_hash({'a':0}) != get_hash({'a':{'k':0}})
    # assert get_hash({'a':0}) != get_hash({'a':{'k':0}})

    
    # ### Hash order invariance tests

    # # Key order invariant dicts
    # assert get_hash({'a':0, 'b':1}) == get_hash({'b':1, 'a':0})
    # assert get_hash({'a':0, 'b':1, 'c':2}) == get_hash({'b':1, 'a':0, 'c':2})
    # assert get_hash({'a':0, 'b':1, 'c':2}) == get_hash({'c':2, 'a':0, 'b':1})
    # assert get_hash({'a':{'k':0, 'q':1}}) == get_hash({'a':{'q':1, 'k':0}})
    
    # # Order-sensitive lists
    # assert get_hash({'a':[0, 1]}) != get_hash({'a':[1, 0]})
    
    
    # ### Mixed tests
    # assert get_hash({'a':[{'k':0}, {'q':1}]}) != get_hash({'a':[{'q':1}, {'k':0}]})
    # assert get_hash({'a':{'k':[0], 'q':[1]}}) == get_hash({'a':{'q':[1], 'k':[0]}})
    # assert get_hash({'b':2, 'a':{'k':0, 'q':1}}) == get_hash({'a':{'q':1, 'k':0}, 'b':2})
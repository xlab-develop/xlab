from argparse import Namespace
import copy
import sys
import os

def merge_dicts(a, b, output_type=None):
    a_type = type(a)
    b_type = type(b)

    if a_type == Namespace:
        a = dict(vars(a))
    if b_type == Namespace:
        b = dict(vars(b))

    a = copy.deepcopy(a)

    for key in b:
        val = b[key]
        if type(val) == dict and key in a and type(a[key]) == dict:
            a[key] = merge_dicts(a[key], val)
        else:
            a[key] = val

    if output_type == None:
        output_type = a_type
    if output_type == Namespace:
        a = Namespace(**a)

    return a

def substract_dict_keys(a, keys):
    a = copy.deepcopy(a)
    for key in keys:
        if key in a:
            del a[key]
    
    return a
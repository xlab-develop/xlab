from argparse import Namespace
import copy


def merge_dicts(a, b, output_type=None):
    """Merges one dict's args into the other.

    Merges dict b's args into a's, effectively replacing existing keys
    in a if they are also present in b.

    Args:
        a: dict or Namespace into which arguments will be marged
            from b.
        b: dict or Namespace from which new arguments will be added
            to a.
        output_type: merge output type. Can be any of:
            * None: input type from base dict a.
            * dict: returns a plain dict object.
            * Namespace: transforms the output to a Namespace object.
    """

    a_type = type(a)
    b_type = type(b)

    # If args are a Namespace, they are turned into a dict
    if a_type == Namespace:
        a = dict(vars(a))
    if b_type == Namespace:
        b = dict(vars(b))

    a = copy.deepcopy(a)

    # Recursively merge dicts within other dicts
    for key in b:
        val = b[key]
        if type(val) == dict and key in a and type(a[key]) == dict:
            a[key] = merge_dicts(a[key], val)
        else:
            a[key] = val

    # Transform to desired output type
    if output_type == None:
        output_type = a_type
    if output_type == Namespace:
        a = Namespace(**a)

    return a


def substract_dict_keys(a, keys):
    """Removes keys from a.

    If some key is not present in a, it is ignored.

    Args:
        a: regular dictionary.
        keys: list of strings representing keys in a.
    """

    a = copy.deepcopy(a)
    for key in keys:
        if key in a:
            del a[key]
    
    return a
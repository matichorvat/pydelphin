from itertools import chain, combinations
from operator import itemgetter
from delphin._exceptions import XmrsStructureError


first = itemgetter(0)
second = itemgetter(1)


class AccumulationDict(dict):
    def __init__(self, accumulator, *args, **kwargs):
        if not hasattr(accumulator, '__call__'):
            raise TypeError('Accumulator must be a binary function.')
        self.accumulator = accumulator
        self.accumulate(*args, **kwargs)

    def __additem__(self, key, value):
        if key in self:
            self[key] = self.accumulator(self[key], value)
        else:
            self[key] = value

    def __add__(self, other):
        result = AccumulationDict(self.accumulator, self)
        result.accumulate(other)
        return result

    def accumulate(self, *args, **kwargs):
        for arg in args:
            if isinstance(arg, dict):
                arg = arg.items()
            if not hasattr(arg, '__iter__'):
                raise TypeError('{} object is not iterable'
                                .format(arg.__class__.__name__))
            for (key, value) in arg:
                self.__additem__(key, value)
        for key in kwargs:
            self.__additem__(key, kwargs[key])


def dict_of_dicts(triples, dicttype=dict):
    d = dicttype()
    for a, b, c in triples:
        try:
            d[a][b] = c
        except KeyError:
            d[a] = dicttype()
            d[a][b] = c
    return d


# used for getting variable properties
class ReadOnceDict(dict):
    def __getitem__(self, key):
        val = dict.__getitem__(self, key)
        del self[key]
        return val

    def get(self, key, default=None):
        if key in self:
            val = dict.__getitem__(self, key)
            del self[key]
        else:
            val = default
        return val


# adapted from recipe in itertools documentation
def powerset(iterable):
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))

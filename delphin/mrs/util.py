from itertools import chain, combinations
from operator import itemgetter
from networkx import DiGraph, relabel_nodes
from delphin._exceptions import XmrsStructureError


first = itemgetter(0)
second = itemgetter(1)


class AccumulationDict(dict):
    def __init__(self, accumulator, *args, **kwargs):
        if not hasattr(accumulator, u'__call__'):
            raise TypeError(u'Accumulator must be a binary function.')
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
            if not hasattr(arg, u'__iter__'):
                raise TypeError(u'{} object is not iterable'
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
    return chain.from_iterable(combinations(s, r) for r in xrange(len(s)+1))

class XmrsDiGraph(DiGraph):
    def __init__(self, data=None, name=u'', **attr):
        DiGraph.__init__(self, data=data, name=name, attr=attr)
        self.nodeids = [] if data is None else data.nodeids
        self.labels = set([] if data is None else data.labels)
        self.refresh()

    def refresh(self):
        seen = set()
        for nid in self.nodeids:
            n = self.node[nid]
            if n.get(u'iv') is not None:
                iv = n[u'iv']
                if iv not in self.node:
                    raise XmrsStructureError(
                        u'Intrinsic variable ({}) of node {} is missing from '
                        u'the Xmrs graph.'
                        .format(iv, nid)
                    )
                # clear the first time
                if iv not in seen:
                    self.node[iv][u'bv'] = None
                    self.node[iv][u'iv'] = None
                    seen.add(iv)
                if n[u'pred'].is_quantifier():
                    self.add_edge(iv, nid, {u'bv': True})  # quantifier
                    self.node[iv][u'bv'] = nid
                else:
                    self.add_edge(iv, nid, {u'iv': True})  # intrinsic arg
                    self.node[iv][u'iv'] = nid


    def subgraph(self, nbunch):
        nbunch = list(nbunch)
        sg = DiGraph.subgraph(self, nbunch)
        node = sg.node
        sg.nodeids = [nid for nid in nbunch if u'pred' in node[nid]]
        sg.labels = set(node[nid][u'label'] for nid in nbunch
                        if u'label' in node[nid])
        g = XmrsDiGraph(sg)
        g.refresh()
        return g


    def relabel_nodes(self, mapping):
        g = relabel_nodes(self, mapping)
        # also need to fix where we store it ourselves
        for tnid in mapping.values():
            iv = g.node[tnid][u'iv']
            if iv is not None:
                v = u'bv' if g.node[tnid][u'pred'].is_quantifier() else u'iv'
                g.node[iv][v] = tnid
        g.nodeids = [mapping.get(n, n) for n in self.nodeids]
        g.labels = set(self.labels)
        return XmrsDiGraph(data=g)
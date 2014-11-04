
# SimpleDMRS codec
# Summary: This module implements serialization and deserialization of the
#          SimpleDMRS encoding of Distributed Minimal Recusion Semantics (DMRS). It
#          provides standard Pickle API calls of load, loads, dump, and dumps
#          for serializing and deserializing single SimpleDMRS instances. Further,
#          encode_list and decode_list are provided for lists of DMRX
#          instances, and they read and write incrementally.
#
# Author: Michael Wayne Goodman <goodmami@uw.edu>

from collections import OrderedDict
from io import BytesIO
import re
from delphin.mrs import (Dmrs, Node, Link, Pred, Lnk)
from delphin.mrs.config import (QUANTIFIER_SORT, EQ_POST)
from itertools import imap


##############################################################################
##############################################################################
# Pickle-API methods


def load(fh, single=False):
    ms = decode(fh)
    if single:
        ms = ms.next()
    return ms


def loads(s, single=False, encoding=u'utf-8'):
    ms = decode(BytesIO(str(s).encode(encoding)))
    if single:
        ms = ms.next()
    return ms


def dump(fh, ms, **kwargs):
    print >>fh, dumps(ms, **kwargs)


def dumps(ms, single=False, pretty_print=False, **kwargs):
    if single:
        ms = [ms]
    return encode(ms, indent=2 if pretty_print else None)

# for convenience

load_one = lambda fh: load(fh, single=True)
loads_one = lambda s: loads(s, single=True)
dump_one = lambda fh, m, **kwargs: dump(fh, m, single=True, **kwargs)
dumps_one = lambda m, **kwargs: dumps(m, single=True, **kwargs)

##############################################################################
##############################################################################
# Decoding

tokenizer = re.compile(ur'("[^"\\]*(?:\\.[^"\\]*)*"'
                       ur'|[^\s:#@\[\]<>"]+'
                       ur'|[:#@\[\]<>])')

def decode(fh):
    u"""Decode a SimpleDmrs-encoded DMRS structure."""
    # (dmrs { ... })*

def decode_dmrs(elem):
    # dmrs { NODES LINKS }
    return Dmrs(nodes=list(imap(decode_node)),
                links=list(imap(decode_link)),
                lnk=None,
                surface=None,
                identifier=None)


def decode_node(elem):
    return Node(pred=decode_pred(elem.find(u'*[1]')),
                nodeid=elem.get(u'nodeid'),
                sortinfo=decode_sortinfo(elem.find(u'sortinfo')),
                lnk=decode_lnk(elem),
                surface=elem.get(u'surface'),
                base=elem.get(u'base'),
                carg=elem.get(u'carg'))


def decode_pred(elem):
    if elem.tag == u'gpred':
        return Pred.grammarpred(elem.text)
    elif elem.tag == u'realpred':
        return Pred.realpred(elem.get(u'lemma'),
                             elem.get(u'pos'),
                             elem.get(u'sense'))


def decode_sortinfo(elem):
    return elem.attrib


def decode_link(elem):
    return Link(start=elem.get(u'from'),
                end=elem.get(u'to'),
                argname=elem.find(u'rargname').text,
                post=elem.find(u'post').text)


def decode_lnk(elem):
    return Lnk.charspan(elem.get(u'cfrom', u'-1'), elem.get(u'cto', u'-1'))

##############################################################################
##############################################################################
# Encoding

_graphtype = u'dmrs'
_graph = u'{graphtype} {graphid}{{{dmrsproperties}{nodes}{links}}}'
_dmrsproperties = u''
_node = u'{indent}{nodeid} [{pred}{lnk}{sortinfo}];'
_sortinfo = u' {cvarsort} {properties}'
_link = u'{indent}{start}:{pre}/{post} {arrow} {end};'

def encode(ms, encoding=u'unicode', indent=2):
    delim = u'\n' if indent is not None else u' '
    return delim.join(encode_dmrs(m, indent=indent) for m in ms)

def encode_dmrs(m, indent=2):
    if indent is not None:
        delim = u'\n'
        space = u' ' * indent
    else:
        delim = u''
        space = u' '

    nodes = [
        _node.format(
            indent=space,
            nodeid=n.nodeid,
            pred=unicode(n.pred),
            lnk=u'' if n.lnk is None else unicode(n.lnk),
            sortinfo=(
                u'' if not n.sortinfo else
                _sortinfo.format(
                    cvarsort=n.cvarsort,
                    properties=u' '.join(u'{}={}'.format(k, v)
                                        for k, v in n.properties.items()),
                )
            )
        )
        for n in m.nodes
    ]

    links = [
        _link.format(
            indent=space,
            start=l.start,
            pre=l.argname or u'',
            post=l.post,
            arrow=u'->' if l.argname or l.post != EQ_POST else u'--',
            end=l.end
        )
        for l in m.links
    ]

    return delim.join([u'dmrs {'] + nodes + links + [u'}'])


# DMRX codec
# Summary: This module implements serialization and deserialization of the
#          XML encoding of Distributed Minimal Recusion Semantics (DMRS). It
#          provides standard Pickle API calls of load, loads, dump, and dumps
#          for serializing and deserializing DMRX corpora. Further,
#          load_one, loads_one, dump_one, and dumps_one operate on a single
#          DMRX/DMRS.
#
# Author: Michael Wayne Goodman <goodmami@uw.edu>

from collections import OrderedDict
from io import BytesIO
import re
from delphin.mrs import (Dmrs, Node, Link, Pred, Lnk)
from delphin.mrs.config import QUANTIFIER_SORT

import xml.etree.ElementTree as etree
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
    return encode(ms, pretty_print=pretty_print)

# for convenience

load_one = lambda fh: load(fh, single=True)
loads_one = lambda s: loads(s, single=True)
dump_one = lambda fh, m, **kwargs: dump(fh, m, single=True, **kwargs)
dumps_one = lambda m, **kwargs: dumps(m, single=True, **kwargs)

##############################################################################
##############################################################################
# Decoding

def decode(fh):
    u"""Decode a DMRX-encoded DMRS structure."""
    # <!ELEMENT dmrs-list (dmrs)*>
    # if memory becomes a big problem, consider catching start events,
    # get the root element (later start events can be ignored), and
    # root.clear() after decoding each mrs
    for event, elem in etree.iterparse(fh, events=(u'end',)):
        if elem.tag == u'dmrs':
            yield decode_dmrs(elem)
            elem.clear()

def decode_dmrs(elem):
    # <!ELEMENT dmrs (node|link)*>
    # <!ATTLIST dmrs
    #           cfrom CDATA #REQUIRED
    #           cto   CDATA #REQUIRED
    #           surface   CDATA #IMPLIED
    #           ident     CDATA #IMPLIED >
    elem = elem.find(u'.')  # in case elem is an ElementTree rather than Element
    return Dmrs(nodes=list(imap(decode_node, elem.iter(u'node'))),
                links=list(imap(decode_link, elem.iter(u'link'))),
                lnk=decode_lnk(elem),
                surface=elem.get(u'surface'),
                identifier=elem.get(u'ident'))


def decode_node(elem):
    # <!ELEMENT node ((realpred|gpred), sortinfo)>
    # <!ATTLIST node
    #           nodeid CDATA #REQUIRED
    #           cfrom CDATA #REQUIRED
    #           cto   CDATA #REQUIRED
    #           surface   CDATA #IMPLIED
    #           base      CDATA #IMPLIED
    #           carg CDATA #IMPLIED >
    return Node(pred=decode_pred(elem.find(u'*[1]')),
                nodeid=elem.get(u'nodeid'),
                sortinfo=decode_sortinfo(elem.find(u'sortinfo')),
                lnk=decode_lnk(elem),
                surface=elem.get(u'surface'),
                base=elem.get(u'base'),
                carg=elem.get(u'carg'))


def decode_pred(elem):
    # <!ELEMENT realpred EMPTY>
    # <!ATTLIST realpred
    #           lemma CDATA #REQUIRED
    #           pos (v|n|j|r|p|q|c|x|u|a|s) #REQUIRED
    #           sense CDATA #IMPLIED >
    # <!ELEMENT gpred (#PCDATA)>
    if elem.tag == u'gpred':
        return Pred.grammarpred(elem.text)
    elif elem.tag == u'realpred':
        return Pred.realpred(elem.get(u'lemma'),
                             elem.get(u'pos'),
                             elem.get(u'sense'))


def decode_sortinfo(elem):
    # <!ELEMENT sortinfo EMPTY>
    # <!ATTLIST sortinfo
    #           cvarsort (x|e|i|u) #IMPLIED
    #           num  (sg|pl|u) #IMPLIED
    #           pers (1|2|3|1-or-3|u) #IMPLIED
    #           gend (m|f|n|m-or-f|u) #IMPLIED
    #           sf (prop|ques|comm|prop-or-ques|u) #IMPLIED
    #           tense (past|pres|fut|tensed|untensed|u) #IMPLIED
    #           mood (indicative|subjunctive|u) #IMPLIED
    #           prontype (std_pron|zero_pron|refl|u) #IMPLIED
    #           prog (plus|minus|u) #IMPLIED
    #           perf (plus|minus|u) #IMPLIED
    #           ind  (plus|minus|u) #IMPLIED >
    # note: Just accept any properties, since these are ERG-specific
    return elem.attrib


def decode_link(elem):
    # <!ELEMENT link (rargname, post)>
    # <!ATTLIST link
    #           from CDATA #REQUIRED
    #           to   CDATA #REQUIRED >
    # <!ELEMENT rargname (#PCDATA)>
    # <!ELEMENT post (#PCDATA)>
    return Link(start=elem.get(u'from'),
                end=elem.get(u'to'),
                argname=elem.find(u'rargname').text,
                post=elem.find(u'post').text)


def decode_lnk(elem):
    return Lnk.charspan(elem.get(u'cfrom', u'-1'), elem.get(u'cto', u'-1'))

##############################################################################
##############################################################################
# Encoding

_strict = False


def encode(ms, strict=False, encoding='UTF-8', pretty_print=False):
    e = etree.Element(u'dmrs-list')
    for m in ms:
        e.append(encode_dmrs(m, strict=strict))
    # for now, pretty_print=True is the same as pretty_print='LKB'
    if pretty_print in (u'LKB', u'lkb', u'Lkb', True):
        lkb_pprint_re = re.compile(r'(<dmrs[^>]+>|</node>|</link>|</dmrs>)')
        string = etree.tostring(e, encoding=encoding)
        return lkb_pprint_re.sub(r'\1\n', string)
    # pretty_print is only lxml. Look into tostringlist, maybe?
    # return etree.tostring(e, pretty_print=pretty_print, encoding='unicode')
    return etree.tostring(e, encoding=encoding)


def encode_dmrs(m, strict=False):
    _strict = strict
    attributes = OrderedDict([(u'cfrom', unicode(m.cfrom)),
                              (u'cto', unicode(m.cto))])
    if m.surface is not None:
        attributes[u'surface'] = m.surface
    if m.identifier is not None:
        attributes[u'ident'] = m.identifier
    if not _strict and m.index is not None:
        # index corresponds to a variable, so link it to a nodeid
        index_nodeid = m.get_nodeid(m.index)
        if index_nodeid is not None:
            attributes[u'index'] = unicode(index_nodeid)
    e = etree.Element(u'dmrs', attrib=attributes)
    for node in m.nodes:
        e.append(encode_node(node))
    for link in m.links:
        e.append(encode_link(link))
    return e


def encode_node(node):
    attributes = OrderedDict([(u'nodeid', unicode(node.nodeid)),
                              (u'cfrom', unicode(node.cfrom)),
                              (u'cto', unicode(node.cto))])
    if node.surface is not None:
        attributes[u'surface'] = node.surface
    if node.base is not None:
        attributes[u'base'] = node.base
    if node.carg is not None:
        attributes[u'carg'] = node.carg
    e = etree.Element(u'node', attrib=attributes)
    e.append(encode_pred(node.pred))
    e.append(encode_sortinfo(node))
    return e


def encode_pred(pred):
    if pred.type == Pred.GRAMMARPRED:
        e = etree.Element(u'gpred')
        e.text = pred.string.strip(u'"\'')
    elif pred.type in (Pred.REALPRED, Pred.STRINGPRED):
        attributes = {}
        if pred.lemma is not None:
            attributes[u'lemma'] = pred.lemma
        if pred.pos is not None:
            attributes[u'pos'] = pred.pos
        if pred.sense is not None:
            attributes[u'sense'] = unicode(pred.sense)
        e = etree.Element(u'realpred', attrib=attributes)
    return e


def encode_sortinfo(node):
    attributes = OrderedDict()
    # return empty <sortinfo/> for quantifiers
    if node.pred.pos == QUANTIFIER_SORT:
        return etree.Element(u'sortinfo')  # return empty <sortinfo/>
    if node.sortinfo:
        if not _strict:
            for k, v in node.sortinfo.items():
                attributes[k.lower()] = unicode(v)
        else:
            pass  # TODO add strict sortinfo
    e = etree.Element(u'sortinfo', attrib=attributes or {})
    return e


def encode_link(link):
    e = etree.Element(u'link', attrib={u'from': unicode(link.start),
                                      u'to': unicode(link.end)})
    argname = etree.Element(u'rargname')
    argname.text = link.argname
    post = etree.Element(u'post')
    post.text = link.post
    e.append(argname)
    e.append(post)
    return e

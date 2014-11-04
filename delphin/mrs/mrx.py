
# MRX codec
# Summary: This module implements serialization and deserialization of
#          the XML encoding of Minimal Recusion Semantics. It provides
#          standard Pickle API calls of load, loads, dump, and dumps for
#          serializing and deserializing single MRX instances.
#          Further, encode_list and decode_list are provided for lists
#          of MRX instances, and they read and write incrementally.
# Author: Michael Wayne Goodman <goodmami@uw.edu>

from collections import OrderedDict
from io import BytesIO
from delphin.mrs import Mrs
from delphin.mrs.components import (
    ElementaryPredication, Argument, Pred, MrsVariable, Lnk, HandleConstraint
)
from delphin._exceptions import XmrsDeserializationError as XDE
from delphin.mrs.config import IVARG_ROLE

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


def dumps(ms, single=False, encoding=u'unicode', pretty_print=False, **kwargs):
    if single:
        ms = [ms]
    return encode(ms, encoding=encoding, pretty_print=pretty_print)

# for convenience

load_one = lambda fh: load(fh, single=True)
loads_one = lambda s: loads(s, single=True)
dump_one = lambda fh, m, **kwargs: dump(fh, m, single=True, **kwargs)
dumps_one = lambda m, **kwargs: dumps(m, single=True, **kwargs)

##############################################################################
##############################################################################
# Decoding

# it's not ideal to have this here, but anyway make sure it is reset
# for each decoding. It's used to unify variables
_vars = {}


def decode(fh):
    u"""Decode an MRX-encoded MRS structure."""
    # <!ELEMENT mrs-list (mrs)*>
    # if memory becomes a big problem, consider catching start events,
    # get the root element (later start events can be ignored), and
    # root.clear() after decoding each mrs
    for event, elem in etree.iterparse(fh, events=(u'end',)):
        if elem.tag == u'mrs':
            yield decode_mrs(elem)
            elem.clear()


def decode_mrs(elem):
    # <!ELEMENT mrs (label, var, (ep|hcons)*)>
    # <!ATTLIST mrs
    #           cfrom     CDATA #IMPLIED
    #           cto       CDATA #IMPLIED
    #           surface   CDATA #IMPLIED
    #           ident     CDATA #IMPLIED >
    elem = elem.find(u'.')  # in case elem is ElementTree rather than Element
    global _vars
    _vars = {}
    # normalize_vars(elem) # try to make all vars have a sort
    return Mrs(hook=Hook(ltop=decode_label(elem.find(u'label')),
                         index=decode_var(elem.find(u'var'))),
               rels=list(imap(decode_ep, elem.iter(u'ep'))),
               hcons=list(imap(decode_hcons, elem.iter(u'hcons'))),
               lnk=decode_lnk(elem.get(u'cfrom'), elem.get(u'cto')),
               surface=elem.get(u'surface'),
               identifier=elem.get(u'ident'))


def decode_label(elem):
    # <!ELEMENT label (extrapair*)>
    # <!ATTLIST label
    #           vid CDATA #REQUIRED >
    return decode_var(elem, sort=u'h')


def decode_var(elem, sort=None):
    # <!ELEMENT var (extrapair*)>
    # <!ATTLIST var
    #           vid  CDATA #REQUIRED
    #           sort (x|e|h|u|l|i) #IMPLIED >
    vid = elem.get(u'vid')
    srt = sort or elem.get(u'sort')
    props = decode_extrapairs(elem.iter(u'extrapair'))
    if vid in _vars:
        if srt != _vars[vid].sort:
            raise XDE(u'Variable {}{} has a conflicting sort with {}'
                      .format(srt, vid, unicode(_vars[vid])))
        _vars[vid].properties.update(props)
    else:
        _vars[vid] = MrsVariable(vid=vid, sort=srt, properties=props)
    return _vars[vid]


def decode_extrapairs(elems):
    # <!ELEMENT extrapair (path,value)>
    # <!ELEMENT path (#PCDATA)>
    # <!ELEMENT value (#PCDATA)>
    return OrderedDict((e.find(u'path').text.upper(), e.find(u'value').text)
                       for e in elems)


def decode_ep(elem):
    # <!ELEMENT ep ((pred|spred|realpred), label, fvpair*)>
    # <!ATTLIST ep
    #           cfrom CDATA #IMPLIED
    #           cto   CDATA #IMPLIED
    #           surface   CDATA #IMPLIED
    #           base      CDATA #IMPLIED >
    return ElementaryPredication(pred=decode_pred(elem.find(u'./')),
                                 label=decode_label(elem.find(u'label')),
                                 args=decode_args(elem),
                                 lnk=decode_lnk(elem.get(u'cfrom'),
                                                elem.get(u'cto')),
                                 surface=elem.get(u'surface'),
                                 base=elem.get(u'base'))


def decode_pred(elem):
    # <!ELEMENT pred (#PCDATA)>
    # <!ELEMENT spred (#PCDATA)>
    # <!ELEMENT realpred EMPTY>
    # <!ATTLIST realpred
    #           lemma CDATA #REQUIRED
    #           pos (v|n|j|r|p|q|c|x|u|a|s) #REQUIRED
    #           sense CDATA #IMPLIED >
    if elem.tag == u'pred':
        return Pred.grammarpred(elem.text)
    elif elem.tag == u'spred':
        return Pred.stringpred(elem.text)
    elif elem.tag == u'realpred':
        return Pred.readpred(elem.get(u'lemma'),
                             elem.get(u'pos'),
                             elem.get(u'sense'))


def decode_args(elem):
    # <!ELEMENT fvpair (rargname, (var|constant))>
    # iv is the intrinsic variable (probably ARG0, given by IVARG_ROLE)
    # carg is the constant arg (e.g. a quoted string; given by CONSTARG_ROLE)
    # This code assumes that only cargs have constant values, and all
    # other args (including IVs) have var values.
    args = []
    for e in elem.findall(u'fvpair'):
        argname = e.find(u'rargname').text.upper()
        if e.find(u'constant') is not None:
            argval = e.find(u'constant').text
        elif e.find(u'var') is not None:
            argval = decode_var(e.find(u'var'))
        args.append(Argument.mrs_argument(argname, argval))
    return args


def decode_hcons(elem):
    # <!ELEMENT hcons (hi, lo)>
    # <!ATTLIST hcons
    #           hreln (qeq|lheq|outscopes) #REQUIRED >
    # <!ELEMENT hi (var)>
    # <!ELEMENT lo (label|var)>
    lo = elem.find(u'lo/')
    return HandleConstraint(decode_var(elem.find(u'hi/var')),
                            elem.get(u'hreln'),
                            decode_var(lo) if lo.tag == u'var' else
                            decode_label(lo))


def decode_lnk(cfrom, cto):
    if cfrom is cto is None:
        return None
    elif None in (cfrom, cto):
        raise ValueError(u'Both cfrom and cto, or neither, must be specified.')
    else:
        return Lnk.charspan(cfrom, cto)

##############################################################################
##############################################################################
# Encoding


def encode(ms, encoding=u'unicode', pretty_print=False):
    e = etree.Element(u'mrs-list')
    for m in ms:
        e.append(encode_mrs(m))
    if pretty_print:
        import re
        pprint_re = re.compile(ur'(<mrs[^-]|</mrs>|</mrs-list>'
                               ur'|<ep\s|<fvpair>|<extrapair>|<hcons\s)',
                               re.IGNORECASE)
        string = etree.tostring(e, encoding=encoding)
        return pprint_re.sub(ur'\n\1', string)
    return etree.tostring(e, encoding=encoding)


def encode_mrs(m):
    attributes = {u'cfrom': unicode(m.cfrom), u'cto': unicode(m.cto)}
    if m.surface is not None:
        attributes[u'surface'] = m.surface
    if m.identifier is not None:
        attributes[u'ident'] = m.identifier
    e = etree.Element(u'mrs', attrib=attributes)
    listed_vars = set()
    if m.ltop is not None:
        e.append(encode_label(m.ltop))
    if m.index is not None:
        e.append(encode_variable(m.index, listed_vars))
    for ep in m.rels:
        e.append(encode_ep(ep, listed_vars))
    for hcon in m.hcons:
        e.append(encode_hcon(hcon))
    return e


def encode_label(label):
    return etree.Element(u'label', vid=unicode(label.vid))


def encode_variable(v, listed_vars=None):
    if listed_vars is None:
        listed_vars = set()
    var = etree.Element(u'var', vid=unicode(v.vid), sort=v.sort)
    if v.vid not in listed_vars and v.properties:
        var.extend(encode_extrapair(key, val)
                   for key, val in v.properties.items())
        listed_vars.add(v.vid)
    return var


def encode_extrapair(key, value):
    extrapair = etree.Element(u'extrapair')
    path = etree.Element(u'path')
    path.text = key
    val = etree.Element(u'value')
    val.text = value
    extrapair.extend([path, val])
    return extrapair


def encode_ep(ep, listed_vars):
    attributes = {u'cfrom': unicode(ep.cfrom), u'cto': unicode(ep.cto)}
    if ep.surface is not None:
        attributes[u'surface'] = ep.surface
    if ep.base is not None:
        attributes[u'base'] = ep.base
    e = etree.Element(u'ep', attrib=attributes)
    e.append(encode_pred(ep.pred))
    e.append(encode_label(ep.label))
    if ep.iv is not None:
        e.append(encode_arg(IVARG_ROLE, encode_variable(ep.iv, listed_vars)))
    for arg in ep.args:
        if isinstance(arg.value, MrsVariable):
            e.append(encode_arg(arg.argname,
                                encode_variable(arg.value, listed_vars)))
        else:
            e.append(encode_arg(arg.argname, encode_constant(arg.value)))
    return e


def encode_pred(pred):
    p = None
    if pred.type == Pred.GRAMMARPRED:
        p = etree.Element(u'pred')
        p.text = pred.string
    elif pred.type == Pred.STRINGPRED:
        p = etree.Element(u'spred')
        p.text = pred.string
    elif pred.type == Pred.REALPRED:
        attributes = {u'lemma': pred.lemma, u'pos': pred.pos}
        if pred.sense is not None:
            attributes[u'sense'] = pred.sense
        p = etree.Element(u'realpred', attrib=attributes)
    return p


def encode_arg(key, value):
    fvpair = etree.Element(u'fvpair')
    rargname = etree.Element(u'rargname')
    rargname.text = key
    fvpair.append(rargname)
    fvpair.append(value)
    return fvpair


def encode_constant(value):
    const = etree.Element(u'constant')
    const.text = value
    return const


def encode_hcon(hcon):
    hcons = etree.Element(u'hcons', hreln=hcon.relation)
    hi = etree.Element(u'hi')
    hi.append(encode_variable(hcon.hi))
    lo = etree.Element(u'lo')
    lo.append(encode_variable(hcon.lo))
    hcons.extend([hi, lo])
    return hcons

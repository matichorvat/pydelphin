
# SimpleMRS codec
# Summary: This module implements serialization and deserialization of
#          the SimpleMRS encoding of Minimal Recusion Semantics. It
#          provides the standard Pickle API calls of load, loads, dump,
#          and dumps.
# Author: Michael Wayne Goodman <goodmami@uw.edu>

from collections import OrderedDict, deque
import re
from delphin.mrs import Mrs
from delphin.mrs.components import (
    Hook, ElementaryPredication, Argument, Pred,
    MrsVariable, Lnk, HandleConstraint, IndividualConstraint
)
from delphin.mrs.config import (HANDLESORT, QEQ, LHEQ, OUTSCOPES)
from delphin.mrs.util import ReadOnceDict
from delphin._exceptions import XmrsDeserializationError as XDE
from io import open
from itertools import imap

try:
    from pygments import highlight as highlight_
    from pygments.formatters import TerminalFormatter
    from delphin.extra.highlight import SimpleMrsLexer, mrs_colorscheme
    lexer = SimpleMrsLexer()
    formatter = TerminalFormatter(bg=u'dark', colorscheme=mrs_colorscheme)
    def highlight(text):
        return highlight_(text, lexer, formatter)
except ImportError:
    # warnings.warn
    def highlight(text):
        return text

# versions are:
#  * 1.0 long running standard
#  * 1.1 added support for MRS-level lnk, surface and EP-level surface
_default_version = 1.1
_latest_version = 1.1

_left_bracket = ur'['
_right_bracket = ur']'
_left_angle = ur'<'
_right_angle = ur'>'
_colon = ur':'
_hash = ur'#'
_at = ur'@'
_top = ur'TOP'
_ltop = ur'LTOP'
_index = ur'INDEX'
_rels = ur'RELS'
_hcons = ur'HCONS'
_icons = ur'ICONS'
_lbl = ur'LBL'
# possible relations for handle constraints
_qeq = ur'qeq'
_lheq = ur'lheq'
_outscopes = ur'outscopes'
_valid_hcons = [_qeq, _lheq, _outscopes]

# pretty-print options
_default_mrs_delim = u'\n'

##############################################################################
##############################################################################
# Pickle-API methods


def load(fh, single=False):
    u"""
    Deserialize SimpleMRSs from a file (handle or filename)

    Args:
      fh: filename or file object
      single: if True, only return the first read |Xmrs| object
    Returns:
      a generator of Xmrs objects (unless the *single* option is True)
    """
    if isinstance(fh, unicode):
        return loads(open(fh, u'r').read(), single=single)
    return loads(fh.read(), single=single)


def loads(s, single=False):
    u"""
    Deserialize SimpleMRS string representations

    Args:
      s: a SimpleMRS string
      single: if True, only return the first read Xmrs object
    Returns:
      a generator of Xmrs objects (unless the *single* option is True)
    """
    ms = deserialize(s)
    if single:
        return ms.next()
    else:
        return ms


def dump(fh, ms, single=False, version=_default_version,
         pretty_print=False, color=False, **kwargs):
    u"""
    Serialize Xmrs objects to a SimpleMRS representation and write to a
    file

    Args:
      fh: filename or file object
      ms: an iterator of Xmrs objects to serialize (unless the
        *single* option is True)
      single: if True, treat ms as a single Xmrs object instead of
        as an iterator
      pretty_print: if True, the output is formatted to be easier to
        read
      color: if True, colorize the output with ANSI color codes
    Returns:
      None
    """
    print >>fh, dumps(ms,
                single=single,
                version=version,
                pretty_print=pretty_print,
                color=color,
                **kwargs)


def dumps(ms, single=False, version=_default_version,
          pretty_print=False, color=False, **kwargs):
    u"""
    Serialize an Xmrs object to a SimpleMRS representation

    Args:
      ms: an iterator of Xmrs objects to serialize (unless the
        *single* option is True)
      single: if True, treat ms as a single Xmrs object instead of
        as an iterator
      pretty_print: if True, the output is formatted to be easier to
        read
      color: if True, colorize the output with ANSI color codes
    Returns:
        a SimpleMrs string representation of a corpus of Xmrs
    """
    if single:
        ms = [ms]
    return serialize(ms, version=version,
                     pretty_print=pretty_print, color=color, **kwargs)


# for convenience

load_one = lambda fh: load(fh, single=True)
loads_one = lambda s: loads(s, single=True)
dump_one = lambda fh, m, **kwargs: dump(fh, m, single=True, **kwargs)
dumps_one = lambda m, **kwargs: dumps(m, single=True, **kwargs)

##############################################################################
##############################################################################
# Deserialization

# The tokenizer has 3 sub-regexen:
#   the first is for strings (e.g. "_dog_n_rel", "\"quoted string\"")
#   the second is for args, variables, preds, etc (e.g. ARG1, _dog_n_rel, x4)
#   the last is for contentful punctuation (e.g. [ ] < > : # @)

tokenizer = re.compile(ur'("[^"\\]*(?:\\.[^"\\]*)*"'
                       ur'|[^\s:#@\[\]<>"]+'
                       ur'|[:#@\[\]<>])')


def tokenize(string):
    u"""Split the SimpleMrs string into tokens."""
    return deque(tokenizer.findall(string))


def validate_token(token, expected):
    u"""Make sure the given token is as expected, or raise an error. This
       comparison is case insensitive."""
    # uppercase the input, since expected tokens are all upper case
    if token.upper() != expected:
        invalid_token_error(token, expected)


def validate_tokens(tokens, expected):
    for exp_tok in expected:
        validate_token(tokens.popleft(), exp_tok)


def is_variable(token):
    try:
        MrsVariable.sort_vid_split(token)
        return True
    except ValueError:
        return False


def invalid_token_error(token, expected):
    raise XDE(u'Invalid token: "{}"\tExpected: "{}"'.format(token, expected))


def deserialize(string):
    # FIXME: consider buffering this so we don't read the whole string at once
    tokens = tokenize(string)
    while tokens:
        yield read_mrs(tokens)


def read_mrs(tokens, version=_default_version):
    u"""Decode a sequence of Simple-MRS tokens. Assume LTOP, INDEX, RELS,
       HCONS, and ICONS occur in that order."""
    # variables needs to be passed to any function that can call read_variable
    variables = {}
    # [ LTOP : handle INDEX : variable RELS : rels-list HCONS : hcons-list ]
    try:
        validate_token(tokens.popleft(), _left_bracket)
        ltop = index = surface = lnk = None
        # SimpleMRS extension for encoding surface string
        if tokens[0] == _left_angle:
            lnk = read_lnk(tokens)
        if tokens[0].startswith(u'"'): # and tokens[0].endswith('"'):
            surface = tokens.popleft()[1:-1] # get rid of first quotes
        if tokens[0] in (_ltop, _top):
            _, ltop = read_featval(tokens, variables=variables)
        if tokens[0] == _index:
            _, index = read_featval(tokens, feat=_index, variables=variables)
        rels = read_rels(tokens, variables=variables)
        hcons = read_hcons(tokens, variables=variables)
        icons = read_icons(tokens, variables=variables)
        validate_token(tokens.popleft(), _right_bracket)
        m = Mrs(hook=Hook(ltop=ltop, index=index),
                rels=rels,
                hcons=hcons,
                icons=icons,
                lnk=lnk,
                surface=surface)
    except IndexError:
        unexpected_termination_error()
    return m


def read_featval(tokens, feat=None, sort=None, variables=None):
    # FEAT : (var-or-handle|const)
    if variables is None:
        variables = {}
    name = tokens.popleft()
    if feat is not None:
        validate_token(name, feat)
    validate_token(tokens.popleft(), _colon)
    # if it's not a variable, assume it's a constant
    if is_variable(tokens[0]):
        value = read_variable(tokens, sort=sort, variables=variables)
    else:
        value = tokens.popleft()
    return name, value


def read_variable(tokens, sort=None, variables=None):
    u"""Read and return the MrsVariable object for the value of the
       variable. Fail if the sort does not match the expected."""
    # var [ vartype PROP : val ... ]
    if variables is None:
        variables = {}
    var = tokens.popleft()
    srt, vid = MrsVariable.sort_vid_split(var)
    # consider something like not(srt <= sort) in the case of subsumptive sorts
    if sort is not None and srt != sort:
        raise XDE(u'Variable {} has sort "{}", expected "{}"'
                  .format(var, srt, sort))
    vartype, props = read_props(tokens)
    if vartype is not None and srt != vartype:
        raise XDE(u'Variable "{}" and its cvarsort "{}" are not the same.'
                  .format(var, vartype))
    if srt == u'h' and props:
        raise XDE(u'Handle variable "{}" has a non-empty property set {}.'
                  .format(var, props))
    if vid in variables:
        if srt != variables[vid].sort:
            raise XDE(u'Variable {} has a conflicting sort with {}'
                      .format(var, unicode(variables[vid])))
        variables[vid].properties.update(props)
    else:
        variables[vid] = MrsVariable(vid=vid, sort=srt, properties=props)
    return variables[vid]


def read_props(tokens):
    u"""Read and return a dictionary of variable properties."""
    # [ vartype PROP1 : val1 PROP2 : val2 ... ]
    props = OrderedDict()
    if not tokens or tokens[0] != _left_bracket:
        return None, props
    tokens.popleft()  # get rid of bracket (we just checked it)
    vartype = tokens.popleft()
    # check if a vartype wasn't given (next token is : )
    if tokens[0] == _colon:
        invalid_token_error(vartype, u"variable type")
    while tokens[0] != _right_bracket:
        prop = tokens.popleft()
        validate_token(tokens.popleft(), _colon)
        val = tokens.popleft()
        props[prop] = val
    tokens.popleft()  # we know this is a right bracket
    return vartype, props


def read_rels(tokens, variables=None):
    u"""Read and return a RELS set of ElementaryPredications."""
    # RELS: < ep* >
    if tokens[0] != _rels:
        return None
    tokens.popleft()  # pop "RELS"
    if variables is None:
        variables = {}
    rels = []
    validate_tokens(tokens, [_colon, _left_angle])
    while tokens[0] != _right_angle:
        rels += [read_ep(tokens, variables=variables)]
    tokens.popleft()  # we know this is a right angle
    return rels


def read_ep(tokens, variables=None):
    u"""Read and return an ElementaryPredication."""
    # [ pred LBL : lbl ARG : variable-or-handle ... ]
    # or [ pred < lnk > ...
    if variables is None:
        variables = {}
    validate_token(tokens.popleft(), _left_bracket)
    pred = Pred.string_or_grammar_pred(tokens.popleft())
    lnk = read_lnk(tokens)
    if tokens[0].startswith(u'"'):
        surface = tokens.popleft()[1:-1] # get rid of first quotes
    else:
        surface = None
    _, label = read_featval(tokens, feat=_lbl, sort=HANDLESORT,
                            variables=variables)
    args = []
    while tokens[0] != _right_bracket:
        args.append(read_argument(tokens, variables=variables))
    tokens.popleft()  # we know this is a right bracket
    return ElementaryPredication(pred, label, args=args,
                                 lnk=lnk, surface=surface)


def read_argument(tokens, variables=None):
    u"""Read and return an Argument."""
    # ARGNAME: (VAR|CONST)
    if variables is None:
        variables = {}
    argname, value = read_featval(tokens, variables=variables)
    return Argument.mrs_argument(argname, value)


def read_lnk(tokens):
    u"""Read and return a tuple of the pred's lnk type and lnk value,
       if a pred lnk is specified."""
    # < FROM : TO > or < FROM # TO > or < TOK... > or < @ EDGE >
    lnk = None
    if tokens[0] == _left_angle:
        tokens.popleft()  # we just checked this is a left angle
        if tokens[0] == _right_angle:
            pass  # empty <> brackets the same as no lnk specified
        # edge lnk: ['@', EDGE, ...]
        elif tokens[0] == _at:
            tokens.popleft()  # remove the @
            lnk = Lnk.edge(tokens.popleft())  # edge lnks only have one number
        # character span lnk: [FROM, ':', TO, ...]
        elif tokens[1] == _colon:
            lnk = Lnk.charspan(tokens.popleft(), tokens[1])
            tokens.popleft()  # this should be the colon
            tokens.popleft()  # and this is the cto
        # chart vertex range lnk: [FROM, '#', TO, ...]
        elif tokens[1] == _hash:
            lnk = Lnk.chartspan(tokens.popleft(), tokens[1])
            tokens.popleft()  # this should be the hash
            tokens.popleft()  # and this is the to vertex
        # tokens lnk: [(TOK,)+ ...]
        else:
            lnkdata = []
            while tokens[0] != _right_angle:
                lnkdata.append(int(tokens.popleft()))
            lnk = Lnk.tokens(lnkdata)
        validate_token(tokens.popleft(), _right_angle)
    return lnk


def read_hcons(tokens, variables=None):
    # HCONS:< HANDLE (qeq|lheq|outscopes) HANDLE ... >
    u"""Read and return an HCONS list."""
    if tokens[0] != _hcons:
        return None
    tokens.popleft()  # pop "HCONS"
    if variables is None:
        variables = {}
    hcons = []
    validate_tokens(tokens, [_colon, _left_angle])
    while tokens[0] != _right_angle:
        hi = read_variable(tokens, sort=u'h', variables=variables)
        # rels are case-insensitive and the convention is lower-case
        rel = tokens.popleft().lower()
        if rel == _qeq:
            rel = QEQ
        elif rel == _lheq:
            rel = LHEQ
        elif rel == _outscopes:
            rel = OUTSCOPES
        else:
            invalid_token_error(rel, u'('+u'|'.join(_valid_hcons)+u')')
        lo = read_variable(tokens, sort=u'h', variables=variables)
        hcons.append(HandleConstraint(hi, rel, lo))
    tokens.popleft()  # we know this is a right angle
    return hcons

def read_icons(tokens, variables=None):
    # ICONS:< TARGET RELATION CLAUSE ... >
    if tokens[0] != _icons:
        return None
    tokens.popleft()  # pop "ICONS"
    if variables is None:
        variables = {}
    icons = []
    validate_tokens(tokens, [_colon, _left_angle])
    while tokens[0] != _right_angle:
        target = read_variable(tokens, variables=variables)
        relation = tokens.popleft().lower()
        clause = read_variable(tokens, variables=variables)
        icons.append(IndividualConstraint(target, relation, clause))
    tokens.popleft()  # we know this is a right angle
    return icons


def unexpected_termination_error():
    raise XDE(u'Invalid MRS: Unexpected termination.')

##############################################################################
##############################################################################
# Encoding


def serialize(ms, version=_default_version, pretty_print=False, color=False):
    u"""Serialize an MRS structure into a SimpleMRS string."""
    delim = u'\n' if pretty_print else _default_mrs_delim
    output = delim.join(
        serialize_mrs(m, version=version, pretty_print=pretty_print)
        for m in ms
    )
    if color:
        output = highlight(output)
    return output


def serialize_mrs(m, version=_default_version, pretty_print=False):
    # note that listed_vars is modified as a side-effect of the lower
    # functions
    g = m._graph
    varprops = ReadOnceDict((v.vid, v.properties) for v in g.nodes()
                            if isinstance(v, MrsVariable))
    listed_vars = set()
    toks = []
    if version >= 1.1:
        header_toks = []
        if m.lnk is not None:
            header_toks.append(serialize_lnk(m.lnk))
        if m.surface is not None:
            header_toks.append(u'"{}"'.format(m.surface))
        if header_toks:
            toks.append(u' '.join(header_toks))
    if m.ltop is not None:
        toks.append(serialize_argument(
            _top if version >= 1.1 else _ltop, m.ltop, varprops
        ))
    if m.index is not None:
        toks.append(serialize_argument(
            _index, m.index, varprops
        ))
    delim = u' ' if not pretty_print else u'\n          '
    toks.append(u'RELS: < {eps} >'.format(
        eps=delim.join(serialize_ep(g, nid, varprops, version=version)
                       for nid in g.nodeids)
    ))
    #if len(g.nodeids) is not None:
    #    toks += [serialize_rels(g, listed_vars, version=version,
    #                            pretty_print=pretty_print)]
    if m.hcons is not None:
        toks += [u' '.join([serialize_hcons(m.hcons, listed_vars)])]
    if version >= 1.1 and m.icons:  # `is not None` if you want "ICONS: < >""
        toks += [u' '.join([serialize_icons(m.icons, listed_vars)])]
    delim = u' ' if not pretty_print else u'\n  '
    return u'{} {} {}'.format(_left_bracket, delim.join(toks), _right_bracket)


def serialize_argument(rargname, value, varprops):
    u"""Serialize an MRS argument into the SimpleMRS format."""
    _argument = u'{rargname}: {value}{props}'
    if isinstance(value, MrsVariable):
        props = varprops.get(value.vid, {})
        var = unicode(value)
        return _argument.format(
            rargname=rargname,
            value=var,
            props=u'' if not props else u' [ {} {} ]'.format(
                value.sort,
                u' '.join(imap(u'{0[0]}: {0[1]}'.format, props.items())))
        )
    else:
        return _argument.format(
            rargname=rargname,
            value=unicode(value),
            props=u''
        )


def serialize_ep(g, nid, varprops, version=_default_version):
    u"""Serialize an Elementary Predication into the SimpleMRS encoding."""
    node = g.node[nid]
    arglist = u' '.join([serialize_argument(rarg, val, varprops)
                        for rarg, val in node[u'rargs'].items()])
    surface = None if version < 1.1 else node[u'surface']
    pred = node[u'pred']
    predstr = pred.string
    return u'[ {pred}{lnk}{surface} LBL: {label}{s}{args} ]'.format(
        pred=predstr,
        lnk=serialize_lnk(node[u'lnk']),
        surface=u' "{}"'.format(surface) if surface is not None else u'',
        label=unicode(node[u'label']),
        s=u' ' if arglist else u'',
        args=arglist
    )


def serialize_lnk(lnk):
    u"""Serialize a predication lnk to surface form into the SimpleMRS
       encoding."""
    s = u""
    if lnk is not None:
        s = _left_angle
        if lnk.type == Lnk.CHARSPAN:
            cfrom, cto = lnk.data
            s += u''.join([unicode(cfrom), _colon, unicode(cto)])
        elif lnk.type == Lnk.CHARTSPAN:
            cfrom, cto = lnk.data
            s += u''.join([unicode(cfrom), _hash, unicode(cto)])
        elif lnk.type == Lnk.TOKENS:
            s += u' '.join([unicode(t) for t in lnk.data])
        elif lnk.type == Lnk.EDGE:
            s += u''.join([_at, unicode(lnk.data)])
        s += _right_angle
    return s


def serialize_hcons(hcons, listed_vars):
    u"""Serialize |HandleConstraints| into the SimpleMRS encoding."""
    toks = [_hcons + _colon, _left_angle]
    for hcon in hcons:
        if hcon.relation == QEQ:
            rel = _qeq
        elif hcon.relation == LHEQ:
            rel = _lheq
        elif hcon.relation == OUTSCOPES:
            rel = _outscopes
        toks += [unicode(hcon.hi), rel, unicode(hcon.lo)]
    toks += [_right_angle]
    return u' '.join(toks)

def serialize_icons(icons, listed_vars):
    u"""Serialize |IndividualConstraints| into the SimpleMRS encoding."""
    toks = [_icons + _colon, _left_angle]
    for icon in icons:
        toks += [unicode(icon.target),
                 icon.relation,
                 unicode(icon.clause)]
    toks += [_right_angle]
    return u' '.join(toks)
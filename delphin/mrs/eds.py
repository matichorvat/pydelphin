
from itertools import count
from delphin.mrs.query import get_outbound_args

def dump(fh, ms, single=False, pretty_print=True, color=False, **kwargs):
    print >>fh, dumps(ms,
                single=single,
                pretty_print=pretty_print,
                color=color,
                **kwargs)

def dumps(ms, single=False, pretty_print=True, color=False, **kwargs):
    if single:
        ms = [ms]
    return u'\n'.join(
        serialize(ms, pretty_print=pretty_print, color=color, **kwargs)
    )

eds = u'{{{index}{delim}{ed_list}}}'
ed =  u'{membership}{id}:{pred}{lnk}{carg}[{dep_list}]{delim}'
carg = u'({constant})'
dep = u'{argname} {value}'

def serialize(ms, pretty_print=True, color=False, **kwargs):
    q_ids = (u'_{}'.format(i) for i in count(start=1))
    delim = u'\n'
    connected = u' '
    disconnected = u'|'
    if not pretty_print:
        delim = u' '
        connected = u''
    for m in ms:
        yield eds.format(
            index=unicode(m.index) + u':' if m.index is not None else u'',
            delim=delim,
            ed_list=u''.join(
                ed.format(
                    membership=connected,  # if m.is_connected(ep.nodeid)?
                    id=ep.iv if not ep.is_quantifier() else q_ids.next(),
                    pred=ep.pred.short_form(),
                    lnk=unicode(ep.lnk),
                    carg=carg.format(constant=ep.carg) if ep.carg else u'',
                    dep_list=(
                        u', '.join(
                            dep.format(argname=a.argname, value=a.value)
                            for a in get_outbound_args(m, ep.nodeid,
                                                       allow_unbound=False)
                        ) if not ep.is_quantifier() else
                        dep.format(argname=u'BV', value=ep.iv)
                    ),
                    delim=delim
                )
                for ep in m.eps
            )
        )

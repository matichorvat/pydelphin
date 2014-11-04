
import networkx as nx


def xmrs_node_match(ndata1, ndata2):
    carg1 = carg2 = None
    if isinstance(ndata1[u'node_label'], unicode):
        carg1 = ndata1[u'node_label']
    if isinstance(ndata2[u'node_label'], unicode):
        carg2 = ndata2[u'node_label']
    matching = True
    if u'pred' in ndata1 and u'pred' in ndata2:
        matching = (
            ndata1[u'pred'] == ndata2[u'pred'] and
            ndata1[u'iv'].properties == ndata2[u'iv'].properties
        )
    elif u'hcons' in ndata1 and u'hcons' in ndata2:
        matching = ndata1[u'hcons'].relation == ndata2[u'hcons'].relation
    elif u'icons' in ndata2 and u'icons' in ndata2:
        matching = ndata1[u'icons'].relation == ndata2[u'icons'].relation
    else:
        matching = set(ndata1.keys()) == set(ndata2.keys())
    return matching


def xmrs_edge_match(edata1, edata2):
    matching = False if (
        edata1.get(u'iv') != edata2.get(u'iv') or
        edata1.get(u'bv') != edata2.get(u'bv') or
        edata1.get(u'rargname') != edata2.get(u'rargname') or
        edata1.get(u'relation') != edata2.get(u'relation')
        ) else True
    return matching


def isomorphic(xmrs1, xmrs2):
    g1 = nx.convert_node_labels_to_integers(
        xmrs1._graph, label_attribute=u'node_label'
    )
    g2 = nx.convert_node_labels_to_integers(
        xmrs2._graph, label_attribute=u'node_label'
    )
    return nx.is_isomorphic(
        g1,
        g2,
        node_match=xmrs_node_match,
        edge_match=xmrs_edge_match
    )


def compare_bags(testbag, goldbag, count_only=True):
    u"""
    Compare two bags of Xmrs objects, returning a triple of
    (unique in test, shared, unique in gold).

    Args:
        testbag: An iterable of Xmrs objects to test.
        goldbag: An iterable of Xmrs objects to compare against.
        count_only: If True, the returned triple will only have the
            counts of each; if False, a list of Xmrs objects will be
            returned for each (using the ones from testbag for the
            shared set)
    Returns:
        A triple of (unique in test, shared, unique in gold), where
        each of the three items is an integer count if the count_only
        parameter is True, or a list of Xmrs objects otherwise.
    """
    gold_remaining = list(goldbag)
    test_unique = []
    shared = []
    for test in testbag:
        gold_match = None
        for gold in gold_remaining:
            if isomorphic(test, gold):
                gold_match = gold
                break
        if gold_match is not None:
            gold_remaining.remove(gold_match)
            shared.append(test)
        else:
            test_unique.append(test)
    if count_only:
        return (len(test_unique), len(shared), len(gold_remaining))
    else:
        return (test_unique, shared, gold_remaining)

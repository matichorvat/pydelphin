# -*- coding: UTF-8 -*-
from collections import OrderedDict
import unittest
from delphin.mrs.components import (
    MrsVariable, AnchorMixin, Lnk, LnkMixin, Hook,
    Argument, Link, HandleConstraint,
    Pred, Node, ElementaryPredication as EP
)
from delphin.mrs.config import (
    QEQ, LHEQ, OUTSCOPES, CVARSORT, IVARG_ROLE, CONSTARG_ROLE,
    EQ_POST, HEQ_POST, NEQ_POST, H_POST, NIL_POST,
    LTOP_NODEID, FIRST_NODEID, ANCHOR_SORT,
)

class TestMrsVariable(unittest.TestCase):
    def test_construct(self):
        self.assertRaises(TypeError, MrsVariable)
        self.assertRaises(TypeError, MrsVariable, 1)
        self.assertRaises(TypeError, MrsVariable, sort=u'h')
        self.assertRaises(TypeError, MrsVariable, 1, properties={u'a':1})
        v = MrsVariable(1, u'h')
        self.assertNotEqual(v, None)

    def test_from_string(self):
        self.assertRaises(ValueError, MrsVariable.from_string(u'1x'))
        self.assertRaises(ValueError, MrsVariable.from_string(u'var'))
        v = MrsVariable.from_string(u'x1')
        self.assertNotEqual(v, None)

    def test_values(self):
        v = MrsVariable(1, u'x')
        self.assertEqual(v.vid, 1)
        self.assertEqual(v.sort, u'x')
        self.assertEqual(len(v.properties), 0)
        v = MrsVariable(10, u'event', properties={u'a':1})
        self.assertEqual(v.vid, 10)
        self.assertEqual(v.sort, u'event')
        self.assertEqual(v.properties, {u'a':1})
        v = MrsVariable.from_string(u'event10')
        self.assertEqual(v.vid, 10)
        self.assertEqual(v.sort, u'event')
        self.assertEqual(len(v.properties), 0)

    def test_str(self):
        v = MrsVariable(1, u'x')
        self.assertEqual(unicode(v), u'x1')
        v = MrsVariable(10, u'individual')
        self.assertEqual(unicode(v), u'individual10')

    def test_equality(self):
        v = MrsVariable(1, u'x')
        self.assertEqual(v, MrsVariable(1, u'x'))
        self.assertEqual(v, u'x1')
        self.assertNotEqual(v, u'x2')
        self.assertNotEqual(v, u'e1')
        self.assertNotEqual(v, u'x')
        self.assertEqual(v, 1)

    def test_hashable(self):
        v1 = MrsVariable(1, u'x')
        v2 = MrsVariable(2, u'e')
        d = {v1:u'one', v2:u'two'}
        self.assertEqual(d[v1], u'one')
        self.assertEqual(d[u'x1'], u'one')
        self.assertEqual(d[v2], u'two')
        self.assertRaises(KeyError, d.__getitem__, v1.vid)
        self.assertRaises(KeyError, d.__getitem__, v1.sort)
        # note: it's invalid to have two variables with different VIDs
        v3 = MrsVariable(2, u'x')
        d[v3] = u'three'
        self.assertEqual(len(d), 3)
        self.assertEqual(d[v3], u'three')

    def test_sort_vid_split(self):
        svs = MrsVariable.sort_vid_split
        self.assertEqual(svs(u'x1'), (u'x', u'1'))
        self.assertEqual(svs(u'event10'), (u'event', u'10'))
        self.assertRaises(ValueError, svs, u'x')
        self.assertRaises(ValueError, svs, u'1')
        self.assertRaises(ValueError, svs, u'1x')


class TestAnchorMixin(unittest.TestCase):
    def test_inherit(self):
        class NoNodeId(AnchorMixin):
            pass
        n = NoNodeId()
        self.assertRaises(AttributeError, getattr, n, u'anchor')
        class WithNodeId(AnchorMixin):
            def __init__(self):
                self.nodeid = 0
        n = WithNodeId()
        self.assertEqual(n.anchor, MrsVariable(0, ANCHOR_SORT))
        n.anchor = MrsVariable(1, ANCHOR_SORT)
        self.assertEqual(n.anchor, MrsVariable(1, ANCHOR_SORT))


class TestLnk(unittest.TestCase):
    def testLnkTypes(self):
        # invalid Lnk type
        self.assertRaises(ValueError, Lnk, data=(0,1), type=u'invalid')
        self.assertRaises(ValueError, Lnk, data=(0,1), type=None)

    def testCharSpanLnk(self):
        lnk = Lnk.charspan(0, 1)
        self.assertEqual(lnk.type, Lnk.CHARSPAN)
        self.assertEqual(lnk.data, (0,1))
        lnk = Lnk.charspan(u'0', u'1')
        self.assertEqual(lnk.data, (0,1))
        self.assertRaises(TypeError, Lnk.charspan, 1)
        self.assertRaises(TypeError, Lnk.charspan, [1])
        self.assertRaises(TypeError, Lnk.charspan, 1, 2, 3)
        self.assertRaises(ValueError, Lnk.charspan, u'a', u'b')

    def testChartSpanLnk(self):
        lnk = Lnk.chartspan(0, 1)
        self.assertEqual(lnk.type, Lnk.CHARTSPAN)
        self.assertEqual(lnk.data, (0,1))
        lnk = Lnk.chartspan(u'0', u'1')
        self.assertEqual(lnk.data, (0,1))
        self.assertRaises(TypeError, Lnk.chartspan, 1)
        self.assertRaises(TypeError, Lnk.chartspan, [1])
        self.assertRaises(TypeError, Lnk.chartspan, 1, 2, 3)
        self.assertRaises(ValueError, Lnk.chartspan, u'a', u'b')

    def testTokensLnk(self):
        lnk = Lnk.tokens([1, 2, 3])
        self.assertEqual(lnk.type, Lnk.TOKENS)
        self.assertEqual(lnk.data, (1,2,3))
        lnk = Lnk.tokens([u'1'])
        self.assertEqual(lnk.data, (1,))
        # empty tokens list might be invalid, but accept for now
        lnk = Lnk.tokens([])
        self.assertEqual(lnk.data, tuple())
        self.assertRaises(TypeError, Lnk.tokens, 1)
        self.assertRaises(ValueError, Lnk.tokens, [u'a',u'b'])

    def testEdgeLnk(self):
        lnk = Lnk.edge(1)
        self.assertEqual(lnk.type, Lnk.EDGE)
        self.assertEqual(lnk.data, 1)
        lnk = Lnk.edge(u'1')
        self.assertEqual(lnk.data, 1)
        self.assertRaises(TypeError, Lnk.edge, None)
        self.assertRaises(TypeError, Lnk.edge, (1,))
        self.assertRaises(ValueError, Lnk.edge, u'a')


class TestLnkMixin(unittest.TestCase):
    def test_inherit(self):
        class NoLnk(LnkMixin):
            pass
        n = NoLnk()
        self.assertEqual(n.cfrom, -1)
        self.assertEqual(n.cto, -1)
        class WithNoneLnk(LnkMixin):
            def __init__(self):
                self.lnk = None
        n = WithNoneLnk()
        self.assertEqual(n.cfrom, -1)
        self.assertEqual(n.cto, -1)
        class WithNonCharspanLnk(LnkMixin):
            def __init__(self):
                self.lnk = Lnk.chartspan(0,1)
        n = WithNonCharspanLnk()
        self.assertEqual(n.cfrom, -1)
        self.assertEqual(n.cto, -1)
        class WithCharspanLnk(LnkMixin):
            def __init__(self):
                self.lnk = Lnk.charspan(0,1)
        n = WithCharspanLnk()
        self.assertEqual(n.cfrom, 0)


class TestHook(unittest.TestCase):
    def test_construct(self):
        h = Hook()
        self.assertEqual(h.ltop, None)
        self.assertEqual(h.index, None)
        self.assertEqual(h.xarg, None)
        h = Hook(ltop=MrsVariable(1, u'h'), index=MrsVariable(2, u'e'),
                 xarg=MrsVariable(3, u'x'))
        self.assertEqual(h.ltop, u'h1')
        self.assertEqual(h.index, u'e2')
        self.assertEqual(h.xarg, u'x3')


class TestArgument(unittest.TestCase):
    def test_construct(self):
        a = Argument(1, u'ARG', u'val')
        self.assertEqual(a.nodeid, 1)
        self.assertEqual(a.argname, u'ARG')
        self.assertEqual(a.value, u'val')

    def test_MrsArgument(self):
        a = Argument.mrs_argument(u'ARG', u'val')
        self.assertEqual(a.nodeid, None)
        self.assertEqual(a.argname, u'ARG')
        self.assertEqual(a.value, u'val')

    def test_RmrsArgument(self):
        a = Argument.rmrs_argument(MrsVariable(1, ANCHOR_SORT), u'ARG', u'val')
        self.assertEqual(a.nodeid, 1)
        self.assertEqual(a.argname, u'ARG')
        self.assertEqual(a.value, u'val')

    def test_equality(self):
        a1 = Argument(None, u'ARG', u'val')
        a2 = Argument(1, u'ARG', u'val')
        a3 = Argument(2, u'ARG', u'val')
        a4 = Argument(None, u'FOO', u'val')
        a5 = Argument(None, u'FOO', u'bar')
        self.assertEqual(a1, a1)
        self.assertEqual(a1, a2)
        self.assertNotEqual(a2, a3)
        self.assertNotEqual(a1, a4)
        self.assertNotEqual(a4, a5)

    def test_infer_type(self):
        a = Argument(None, IVARG_ROLE, MrsVariable(1, u'x'))
        self.assertEqual(a.infer_argument_type(), Argument.INTRINSIC_ARG)
        a = Argument(None, u'ARG', MrsVariable(1, u'x'))
        self.assertEqual(a.infer_argument_type(), Argument.VARIABLE_ARG)
        a = Argument(None, u'ARG', MrsVariable(1, u'h'))
        self.assertEqual(a.infer_argument_type(), Argument.HANDLE_ARG)
        # fake an Xmrs where h0 is QEQ'd and others are not
        class FakeXmrs(object):
            def get_hcons(self, var):
                if var == u'h0':
                    return 1  # any value is ok for now
                return None
        x = FakeXmrs()
        a = Argument(None, u'ARG', MrsVariable(0, u'h'))
        self.assertEqual(a.infer_argument_type(xmrs=x), Argument.HCONS_ARG)
        a = Argument(None, u'ARG', MrsVariable(1, u'h'))
        self.assertEqual(a.infer_argument_type(xmrs=x), Argument.LABEL_ARG)
        a = Argument(None, CONSTARG_ROLE, u'constant')
        self.assertEqual(a.infer_argument_type(), Argument.CONSTANT_ARG)
        a = Argument(None, u'OTHER', u'constant')
        self.assertEqual(a.infer_argument_type(), Argument.CONSTANT_ARG)


class TestLink(unittest.TestCase):
    def test_construct(self):
        self.assertRaises(TypeError, Link)
        self.assertRaises(TypeError, Link, 0)
        l = Link(0, 1)
        self.assertEqual(l.start, 0)
        self.assertEqual(l.end, 1)
        self.assertEqual(l.argname, None)
        self.assertEqual(l.post, None)
        l = Link(u'0', u'1')
        self.assertEqual(l.start, 0)
        self.assertEqual(l.end, 1)
        self.assertEqual(l.argname, None)
        self.assertEqual(l.post, None)
        l = Link(0, 1, argname=u'ARG')
        self.assertEqual(l.start, 0)
        self.assertEqual(l.end, 1)
        self.assertEqual(l.argname, u'ARG')
        self.assertEqual(l.post, None)
        l = Link(0, 1, post=u'NEQ')
        self.assertEqual(l.start, 0)
        self.assertEqual(l.end, 1)
        self.assertEqual(l.argname, None)
        self.assertEqual(l.post, u'NEQ')
        l = Link(0, 1, argname=u'ARG', post=u'NEQ')
        self.assertEqual(l.start, 0)
        self.assertEqual(l.end, 1)
        self.assertEqual(l.argname, u'ARG')
        self.assertEqual(l.post, u'NEQ')


class TestHandleConstraint(unittest.TestCase):
    def test_construct(self):
        h1 = MrsVariable(1, u'handle')
        h2 = MrsVariable(2, u'handle')
        self.assertRaises(TypeError, HandleConstraint)
        self.assertRaises(TypeError, HandleConstraint, h1)
        self.assertRaises(TypeError, HandleConstraint, h1, QEQ)
        # planned:
        # self.assertRaises(MrsHconsException, HandleConstraint, h1, QEQ, h1)
        hc = HandleConstraint(h1, QEQ, h2)
        self.assertEqual(hc.hi, h1)
        self.assertEqual(hc.relation, QEQ)
        self.assertEqual(hc.lo, h2)
        hc = HandleConstraint(h1, LHEQ, h2)
        self.assertEqual(hc.relation, LHEQ)

    def test_equality(self):
        h1 = MrsVariable(1, u'h')
        h2 = MrsVariable(2, u'h')
        hc1 = HandleConstraint(h1, QEQ, h2)
        self.assertEqual(hc1, HandleConstraint(h1, QEQ, h2))
        self.assertNotEqual(hc1, HandleConstraint(h2, QEQ, h1))
        self.assertNotEqual(hc1, HandleConstraint(h1, LHEQ, h2))

    def test_hashable(self):
        hc1 = HandleConstraint(MrsVariable(1, u'h'), QEQ, MrsVariable(2, u'h'))
        hc2 = HandleConstraint(MrsVariable(3, u'h'), QEQ, MrsVariable(4, u'h'))
        d = {hc1:1, hc2:2}
        self.assertEqual(d[hc1], 1)
        self.assertEqual(d[hc2], 2)


class TestPred(unittest.TestCase):
    def testGpred(self):
        p = Pred.grammarpred(u'pron_rel')
        self.assertEqual(p.type, Pred.GRAMMARPRED)
        self.assertEqual(p.string, u'pron_rel')
        self.assertEqual(p.lemma, u'pron')
        self.assertEqual(p.pos, None)
        self.assertEqual(p.sense, None)
        p = Pred.grammarpred(u'udef_q_rel')
        self.assertEqual(p.string, u'udef_q_rel')
        self.assertEqual(p.lemma, u'udef')
        self.assertEqual(p.pos, u'q')
        self.assertEqual(p.sense, None)
        p = Pred.grammarpred(u'abc_def_ghi_rel')
        self.assertEqual(p.type, Pred.GRAMMARPRED)
        self.assertEqual(p.string, u'abc_def_ghi_rel')
        # pos must be a single character, so we get abc_def, ghi, rel
        self.assertEqual(p.lemma, u'abc_def')
        self.assertEqual(p.pos, None)
        self.assertEqual(p.sense, u'ghi')

    def testSpred(self):
        p = Pred.stringpred(u'_dog_n_rel')
        self.assertEqual(p.type, Pred.STRINGPRED)
        self.assertEqual(p.string, u'_dog_n_rel')
        self.assertEqual(p.lemma, u'dog')
        self.assertEqual(p.pos, u'n')
        self.assertEqual(p.sense, None)
        p = Pred.stringpred(u'_犬_n_rel')
        self.assertEqual(p.type, Pred.STRINGPRED)
        self.assertEqual(p.string, u'_犬_n_rel')
        self.assertEqual(p.lemma, u'犬')
        self.assertEqual(p.pos, u'n')
        self.assertEqual(p.sense, None)
        p = Pred.stringpred(u'"_dog_n_1_rel"')
        self.assertEqual(p.type, Pred.STRINGPRED)
        self.assertEqual(p.string, u'"_dog_n_1_rel"')
        self.assertEqual(p.lemma, u'dog')
        self.assertEqual(p.pos, u'n')
        self.assertEqual(p.sense, u'1')
        #TODO: the following shouldn't throw warnings.. the code should
        # be more robust, but there should be some Warning or logging
        #self.assertRaises(ValueError, Pred.stringpred, '_dog_rel')
        #self.assertRaises(ValueError, Pred.stringpred, '_dog_n_1_2_rel')

    def testStringOrGrammarPred(self):
        p = Pred.string_or_grammar_pred(u'_dog_n_rel')
        self.assertEqual(p.type, Pred.STRINGPRED)
        p = Pred.string_or_grammar_pred(u'pron_rel')
        self.assertEqual(p.type, Pred.GRAMMARPRED)

    def testRealPred(self):
        # basic, no sense arg
        p = Pred.realpred(u'dog', u'n')
        self.assertEqual(p.type, Pred.REALPRED)
        self.assertEqual(p.string, u'_dog_n_rel')
        self.assertEqual(p.lemma, u'dog')
        self.assertEqual(p.pos, u'n')
        self.assertEqual(p.sense, None)
        # try with arg names, unicode, and sense
        p = Pred.realpred(lemma=u'犬', pos=u'n', sense=u'1')
        self.assertEqual(p.type, Pred.REALPRED)
        self.assertEqual(p.string, u'_犬_n_1_rel')
        self.assertEqual(p.lemma, u'犬')
        self.assertEqual(p.pos, u'n')
        self.assertEqual(p.sense, u'1')
        # in case sense is int, not str
        p = Pred.realpred(u'dog', u'n', 1)
        self.assertEqual(p.type, Pred.REALPRED)
        self.assertEqual(p.string, u'_dog_n_1_rel')
        self.assertEqual(p.lemma, u'dog')
        self.assertEqual(p.pos, u'n')
        self.assertEqual(p.sense, u'1')
        self.assertRaises(TypeError, Pred.realpred, lemma=u'dog')
        self.assertRaises(TypeError, Pred.realpred, pos=u'n')

    def testEq(self):
        self.assertEqual(Pred.stringpred(u'_dog_n_rel'),
                         Pred.realpred(lemma=u'dog', pos=u'n'))
        self.assertEqual(Pred.stringpred(u'_dog_n_rel'), u'_dog_n_rel')
        self.assertEqual(u'_dog_n_rel', Pred.realpred(lemma=u'dog', pos=u'n'))
        self.assertEqual(Pred.stringpred(u'"_dog_n_rel"'),
                         Pred.stringpred(u"'_dog_n_rel'"))
        self.assertEqual(Pred.grammarpred(u'pron_rel'), u'pron_rel')
        self.assertNotEqual(Pred.string_or_grammar_pred(u'_dog_n_rel'),
                            Pred.string_or_grammar_pred(u'dog_n_rel'))


class TestNode(unittest.TestCase):
    def test_construct(self):
        # minimum is a nodeid and a pred
        self.assertRaises(TypeError, Node)
        self.assertRaises(TypeError, Node, 10000)
        n = Node(10000, Pred.stringpred(u'_dog_n_rel'))
        self.assertEqual(n.nodeid, 10000)
        self.assertEqual(n.pred, u'_dog_n_rel')

    def test_sortinfo(self):
        n = Node(10000, Pred.stringpred(u'_dog_n_rel'))
        self.assertEqual(len(n.sortinfo), 0)
        n = Node(10000, Pred.stringpred(u'_dog_n_rel'),
                 sortinfo=[(CVARSORT, u'x')])
        self.assertEqual(len(n.sortinfo), 1)
        n = Node(10000, Pred.stringpred(u'_dog_n_rel'),
                 sortinfo=[(CVARSORT, u'x'), (u'PER', u'3')])
        self.assertEqual(len(n.sortinfo), 2)
        n2 = Node(10001, Pred.stringpred(u'_cat_n_rel'),
                  sortinfo=OrderedDict([(CVARSORT,u'x'), (u'PER',u'3')]))
        self.assertEqual(n.sortinfo, n2.sortinfo)

    def test_properties(self):
        n = Node(10000, Pred.stringpred(u'_dog_n_rel'))
        self.assertEqual(len(n.properties), 0)
        n = Node(10000, Pred.stringpred(u'_dog_n_rel'),
                 sortinfo=[(CVARSORT, u'x')])
        self.assertEqual(len(n.properties), 0)
        n = Node(10000, Pred.stringpred(u'_dog_n_rel'),
                 sortinfo=[(CVARSORT, u'x'), (u'PER', u'3')])
        self.assertEqual(len(n.properties), 1)
        n2 = Node(10001, Pred.stringpred(u'_unknowncat_n_rel'),
                  sortinfo=OrderedDict([(CVARSORT,u'u'), (u'PER',u'3')]))
        self.assertEqual(n.properties, n2.properties)

    def test_lnk(self):
        n = Node(10000, Pred.stringpred(u'_dog_n_rel'))
        self.assertEqual(n.lnk, None)
        self.assertEqual(n.cfrom, -1)
        self.assertEqual(n.cto, -1)
        n = Node(10000, Pred.stringpred(u'_dog_n_rel'),
                 lnk=Lnk.charspan(0,1))
        self.assertEqual(n.lnk, Lnk.charspan(0,1))
        self.assertEqual(n.cfrom, 0)
        self.assertEqual(n.cto, 1)

    def test_cvarsort(self):
        n = Node(10000, Pred.stringpred(u'_dog_n_rel'))
        self.assertEqual(n.cvarsort, None)
        n.cvarsort = u'x'
        self.assertEqual(n.cvarsort, u'x')
        self.assertEqual(n.sortinfo, OrderedDict([(CVARSORT, u'x')]))
        n = Node(10000, Pred.stringpred(u'_run_v_rel'),
                 sortinfo=OrderedDict([(CVARSORT, u'e')]))
        self.assertEqual(n.cvarsort, u'e')

    def test_get_property(self):
        n = Node(10000, Pred.stringpred(u'_dog_n_rel'))
        self.assertEqual(n.get_property(u'PER'), None)
        n = Node(10000, Pred.stringpred(u'_dog_n_rel'),
                 sortinfo=OrderedDict([(CVARSORT, u'x'), (u'PER', u'3')]))
        self.assertEqual(n.get_property(u'PER'), u'3')


class TestElementaryPredication(unittest.TestCase):
    def test_construct(self):
        self.assertRaises(TypeError, EP)
        self.assertRaises(TypeError, EP, Pred.stringpred(u'_dog_n_rel'))
        e = EP(Pred.stringpred(u'_dog_n_rel'), MrsVariable(vid=1,sort=u'h'))
        self.assertEqual(e.pred, u'_dog_n_rel')
        self.assertEqual(e.label, MrsVariable(vid=1, sort=u'h'))

    def test_anchor(self):
        e = EP(Pred.stringpred(u'_dog_n_rel'), MrsVariable(vid=1, sort=u'h'))
        self.assertEqual(e.anchor, None)
        self.assertEqual(e.nodeid, None)
        e = EP(Pred.stringpred(u'_dog_n_rel'), MrsVariable(vid=1, sort=u'h'),
               anchor=MrsVariable(vid=10000, sort=ANCHOR_SORT))
        self.assertEqual(e.anchor, MrsVariable(vid=10000, sort=ANCHOR_SORT))
        self.assertEqual(e.nodeid, 10000)

    def test_properties(self):
        p = Pred.stringpred(u'_dog_n_rel')
        lbl = MrsVariable(vid=1, sort=u'h')
        e = EP(p, lbl)
        self.assertEqual(len(e.properties), 0)
        v = MrsVariable(vid=2, sort=u'x', properties={u'num': u'sg'})
        # properties only come from intrinsic arg
        e = EP(p, lbl, args=[Argument.mrs_argument(u'ARG1', v)])
        self.assertEqual(len(e.properties), 0)
        e = EP(p, lbl, args=[Argument.mrs_argument(IVARG_ROLE, v)])
        self.assertEqual(len(e.properties), 1)
        self.assertEqual(e.properties[u'num'], u'sg')

    def test_args(self):
        p = Pred.stringpred(u'_chase_v_rel')
        lbl = MrsVariable(vid=1, sort=u'h')
        e = EP(p, lbl)
        self.assertEqual(len(e.args), 0)
        v1 = MrsVariable(vid=2, sort=u'e', properties={u'tense': u'pres'})
        e = EP(p, lbl, args=[Argument.mrs_argument(IVARG_ROLE, v1)])
        self.assertEqual(len(e.args), 1)
        self.assertEqual(e.arg_value(IVARG_ROLE), v1)
        v2 = MrsVariable(vid=3, sort=u'x', properties={u'num': u'sg'})
        e = EP(p, lbl, args=[Argument.mrs_argument(IVARG_ROLE, v1),
                             Argument.mrs_argument(u'ARG1', v2)])
        self.assertEqual(len(e.args), 2)
        self.assertEqual(e.arg_value(IVARG_ROLE), v1)
        self.assertEqual(e.arg_value(u'ARG1'), v2)

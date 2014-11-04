from delphin.mrs.semi import Vpm
import unittest

class TestVpm(unittest.TestCase):
    def setUp(self):
        return
        # simple just maps A:a1 <> X:x1
        self.simple = Vpm(mappings=[
            ((u'A',),(u'X',),[((u'a1',),u'<>',(u'x1',))])])
        # many_r has multiple right-side targets: A:a1 <> X:x1 Y:y1
        self.many_r = Vpm(mappings=[
            ((u'A',),(u'X',u'Y'),[((u'a1',),u'<>',(u'x1',u'y1'))])])
        # many_l has multiple left-side sources: A:a1 B:b1 <> X:x1
        self.many_l = Vpm(mappings=[
            ((u'A',u'B'),(u'X',),[((u'a1',u'b1'),u'<>',(u'x1',))])])
        # many_lr has multiple sources and targets: A:a1 B:b1 <> X:x1 Y:y1
        self.many_lr = Vpm(mappings=[
            ((u'A',u'B'),(u'X',u'Y'),[((u'a1',u'b1'),u'<>',(u'x1',u'y1'))])])

    def test_find_map(self):
        return
        props1 = {u'A':u'a1', u'B':u'b1'}
        props2 = {u'A':u'a2', u'B':u'b2'}
        rev_props1 = {u'X':u'x1', u'Y':u'y1'}
        rev_props2 = {u'X':u'x2', u'Y':u'y2'}
        fm = self.simple.find_map
        self.assertEqual(fm(props1, (u'A',)), {u'X':u'x1'})
        self.assertEqual(fm(props2, (u'A',)), {u'A':u'a2'})
        self.assertEqual(fm(rev_props1, (u'X',), reverse=True), {u'A':u'a1'})
        self.assertEqual(fm(rev_props2, (u'X',), reverse=True), {u'X':u'x2'})

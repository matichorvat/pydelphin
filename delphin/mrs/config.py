# encoding: UTF-8

# constants used throughout the mrs library
# In the future, these should probably move to a proper settings module

LTOP_NODEID    = 0
FIRST_NODEID   = 10000 # the nodeid assigned to the first node
# sortal values
UNKNOWNSORT    = u'u' # when nothing is known about the sort
HANDLESORT     = u'h' # for scopal relations
QUANTIFIER_SORT= u'q' # for quantifier preds
# HCONS
QEQ            = u'qeq'
LHEQ           = u'lheq'
OUTSCOPES      = u'outscopes'
# MRS strings
IVARG_ROLE     = u'ARG0'
CONSTARG_ROLE  = u'CARG'
# RMRS strings
ANCHOR_SORT    = HANDLESORT # LKB output is like h10001, but in papers it's a1
# DMRS strings
RSTR_ROLE      = u'RSTR' # DMRS establishes that quantifiers have a RSTR link
EQ_POST        = u'EQ'
HEQ_POST       = u'HEQ'
NEQ_POST       = u'NEQ'
H_POST         = u'H'
NIL_POST       = u'NIL'
CVARSORT       = u'cvarsort'

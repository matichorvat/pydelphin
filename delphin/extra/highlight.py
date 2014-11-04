
import re
from pygments.lexer import RegexLexer, include, bygroups
from pygments.token import (
    Token, Whitespace, Text, Number, String,
    Keyword, Name, Operator, Punctuation,
    Comment, Error
)

tdl_break_characters = re.escape(ur'<>!=:.#&,[];$()^/')

class TdlLexer(RegexLexer):
    name = u'TDL'
    aliases = [u'tdl']
    filenames = [u'*.tdl']

    tokens = {
        u'root': [
            (ur'\s+', Text),
            include(u'comment'),
            (ur'(\S+?)(\s*)(:[=<+])', bygroups(Name.Class, Text, Operator),
             u'typedef'),
            (ur'(%)(\s*\(\s*)(letter-set)',
             bygroups(Operator, Punctuation, Name.Builtin),
             (u'letterset', u'letterset')),  # need to pop twice
            (ur':begin', Name.Builtin, u'macro')
        ],
        u'comment': [
            (ur';.*?$', Comment.Singleline),
            (ur'#\|', Comment.Multiline, u'multilinecomment')
        ],
        u'multilinecomment': [
            (ur'[^#|]', Comment.Multiline),
            (ur'#\|', Comment.Multiline, u'#push'),
            (ur'\|#', Comment.Multiline, u'#pop'),
            (ur'[#|]', Comment.Multiline)
        ],
        u'typedef': [
            (ur'\s+', Text),
            (ur'\.', Punctuation, u'#pop'),
            # probably ok to reuse letterset for %suffix and %prefix
            (ur'(%prefix|%suffix)', Name.Builtin, u'letterset'),
            include(u'conjunction')
        ],
        u'conjunction': [
            (ur'\s+', Text),
            (ur'&', Operator),
            (ur'"[^"\\]*(?:\\.[^"\\]*)*"', String.Doc),
            include(u'term'),
            (ur'', Text, u'#pop')
        ],
        u'term': [
            include(u'comment'),
            (ur'\[', Punctuation, u'avm'),
            (ur'<!', Punctuation, u'difflist'),
            (ur'<', Punctuation, u'conslist'),
            (ur'#[^\s{}]+'.format(tdl_break_characters), Name.Label),
            include(u'strings'),
            (ur'\*top\*', Keyword.Constant),
            (ur'\.\.\.', Name),
            (ur'[^\s{}]+'.format(tdl_break_characters), Name),
            (ur'', Text, u'#pop')
        ],
        u'avm': [
            include(u'comment'),
            (ur'\s+', Text),
            (ur'\]', Punctuation, u'#pop'),
            (ur',', Punctuation),
            (ur'((?:[^\s{0}]+)(?:\s*\.\s*[^\s{0}]+)*)'
             .format(tdl_break_characters), Name.Attribute, u'conjunction')
        ],
        u'conslist': [
            (ur'>', Punctuation, u'#pop'),
            (ur',|\.', Punctuation),
            include(u'conjunction')
        ],
        u'difflist': [
            (ur'!>', Punctuation, u'#pop'),
            (ur',|\.', Punctuation),
            include(u'conjunction')
        ],
        u'strings': [
            (ur'"[^"\\]*(?:\\.[^"\\]*)*"', String.Double),
            (ur"'[^ \\]*(?:\\.[^ \\]*)*", String.Single),
            (ur"\^[^ \\]*(?:\\.[^ \\]*)*\$", String.Regex)
        ],
        u'letterset': [
            (ur'\(', Punctuation, u'#push'),
            (ur'\)|\n', Punctuation, u'#pop'),
            (ur'!\w', Name.Variable),
            (ur'\s+', Text),
            (ur'\*', Name.Constant),
            (ur'.', String.Char)
        ],
        u'macro': [
            (ur'\s+', Text),
            include(u'comment'),
            (ur'(:end.*?)(\.)', bygroups(Name.Builtin, Punctuation), u'#pop'),
            (ur'(:begin.*?)(\.)', bygroups(Name.Builtin, Punctuation), u'#push'),
            (ur':[-\w]+', Name.Builtin),
            include(u'strings'),
            (ur'[-\w]+', Name),
            (ur'\.', Punctuation)
        ]
    }


mrs_colorscheme = {
    Token:              (u'',            u''),

    #Whitespace:         ('lightgray',   'darkgray'),
    #Comment:            ('lightgray',   'darkgray'),
    #Comment.Preproc:    ('teal',        'turquoise'),
    #Keyword:            ('darkblue',    'blue'),
    #Keyword.Type:       ('teal',        'turquoise'),
    Operator.Word:      (u'__',          u'__'),  # HCONS or ICONS relations
    Name.Builtin:       (u'**',          u'**'),  # LTOP, RELS, etc
    # used for variables
    Name.Label:         (u'brown',       u'*yellow*'),  # handles
    Name.Function:      (u'*purple*',    u'*fuchsia*'),  # events
    Name.Variable:      (u'*darkblue*',  u'*blue*'),  # ref-inds (x)
    Name.Other:         (u'*teal*',      u'*turquoise*'),  # underspecified (i, p, u)
    # role arguments
    Name.Namespace:     (u'__',          u'__'),  # LBL
    Name.Class:         (u'__',          u'__'),  # ARG0
    Name.Constant:      (u'darkred',     u'red'),  # CARG
    Name.Tag:           (u'__',          u'__'),  # others
    #Name.Exception:     ('teal',        'turquoise'),
    #Name.Decorator:     ('darkgray',    'lightgray'),
    Name.Attribute:     (u'darkgray',    u'darkgray'),  # variable properties
    String:             (u'brown',       u'brown'),
    String.Symbol:      (u'darkgreen',   u'green'),
    String.Other:       (u'green',       u'darkgreen'),
    Number:             (u'lightgray',   u'lightgray'),  # lnk

    # Generic.Deleted:    ('red',        'red'),
    # Generic.Inserted:   ('darkgreen',  'green'),
    # Generic.Heading:    ('**',         '**'),
    # Generic.Subheading: ('*purple*',   '*fuchsia*'),
    # Generic.Error:      ('red',        'red'),

    Error:              (u'_red_',       u'_red_'),
}


class SimpleMrsLexer(RegexLexer):
    name = u'SimpleMRS'
    aliases = [u'mrs']
    filenames = [u'*.mrs']

    tokens = {
        u'root': [
            (ur'\s+', Text),
            (ur'\[|\]', Punctuation, u'mrs')
        ],
        u'mrs': [
            (ur'\s+', Text),
            include(u'strings'),
            include(u'vars'),
            (ur'\]', Punctuation, u'#pop'),
            (ur'<', Number, u'lnk'),
            (ur'(TOP|LTOP|INDEX)(\s*)(:)',
             bygroups(Name.Builtin, Text, Punctuation)),
            (ur'(RELS|HCONS|ICONS)(\s*)(:)(\s*)(<)',
             bygroups(Name.Builtin, Text, Punctuation, Text, Punctuation),
             u'list'),
        ],
        u'strings': [
            (ur'"[^"\\]*(?:\\.[^"\\]*)*"', String.Double),
            (ur"'[^ \\]*(?:\\.[^ \\]*)*", String.Single),
        ],
        u'vars': [
            (ur'(?:h|handle)\d+', Name.Label),
            (ur'(?:e|event)\d+', Name.Function, u'var'),
            (ur'(?:x|ref-ind)\d+', Name.Variable, u'var'),
            (ur'(?:i|individual|p|non_event|u|semarg)\d+', Name.Other, u'var'),
        ],
        u'var': [
            (ur'\s+', Text),
            (ur'\[', Punctuation, u'proplist'),
            (ur'', Text, u'#pop')
        ],
        u'proplist': [
            (ur'\s+', Text),
            (ur'([^:\s]+)(\s*)(:)(\s*)([^\s]+)',
             bygroups(Name.Attribute, Text, Punctuation, Text, Text)),
            (ur'\]', Punctuation, u'#pop'),
            (ur'e|event|x|ref-ind', Name.Variable),
            (ur'\w+', Name.Other)
        ],
        u'lnk': [
            (ur'\s+', Text),
            (ur'>', Number, u'#pop'),
            (ur'\d+[:#]\d+|@\d+|\d+(?:\s+\d+)*', Number),
        ],
        u'list': [
            (ur'\s+', Text),
            (ur'>', Punctuation, u'#pop'),
            (ur'\[', Punctuation, (u'ep', u'pred')),
            include(u'vars'),
            (ur'qeq|outscopes|lheq|[^\s]+', Operator.Word),
        ],
        u'ep': [
            (ur'\s+', Text),
            (ur'<', Number, u'lnk'),
            (ur'\]', Punctuation, u'#pop'),
            include(u'strings'),
            (ur'(LBL)(\s*)(:)',
             bygroups(Name.Namespace, Text, Punctuation)),
            (ur'(ARG0)(\s*)(:)',
             bygroups(Name.Class, Text, Punctuation)),
            (ur'(CARG)(\s*)(:)',
             bygroups(Name.Constant, Text, Punctuation)),
            (ur'([^:\s]+)(\s*)(:)',
             bygroups(Name.Tag, Text, Punctuation)),
            include(u'vars')
        ],
        u'pred': [
            (ur'\s+', Text),
            (ur'"[^"_\\]*(?:\\.[^"\\]*)*"', String.Symbol, u'#pop'),
            (ur"'[^ _\\]*(?:\\.[^ \\]*?)*", String.Symbol, u'#pop'),
            (ur'[^ <]+', String.Symbol, u'#pop')
        ]
    }

    def get_tokens_unprocessed(self, text):
        for index, token, value in RegexLexer.get_tokens_unprocessed(self, text):
            if token is String.Symbol and u'_q_' in value:
                yield index, String.Other, value
            else:
                yield index, token, value

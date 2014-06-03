# -*- coding: utf-8 -*-
"""
    pygments.lexers.sw
    ~~~~~~~~~~~~~~~~~~~~~

    Lexers for semantic web languages.

    :copyright: 2007 by Philip Cooper <philip.cooper@openvest.com>.
    :license: BSD, see LICENSE for more details.
    
    Modified and extended by Gerrit Niezen. (LICENSE file described above is missing, wasn't distributed with original file) 
"""

import re

from pygments.lexer import RegexLexer, include, bygroups
from pygments.token import Error, Punctuation, \
     Text, Comment, Operator, Keyword, Name, String, Number, Literal
from pygments.util import shebang_matches

__all__ = ['Notation3Lexer']

# The N3 lexer should be close to the not really correct grammar at
# http://www.w3.org/2000/10/swap/grammar/n3-ietf.txt
# Comments indicate to which grammar rule the various regular
# expressions correspond.

_explicit_uri = r'<[^>]*>'
_qname = r'((\w[-\w]*)?:)?\w[-\w]*|(\w[-\w]*)?:' #(([:letter:][-\w]*)?:)?[:letter:][.\w]*
_symbol = '(' + _qname + '|' + _explicit_uri +')'
_quickvariable = r'\?\w+'

def expression(symbolAction, nextState):
    #expression ::=  | pathitem pathtail
    #pathitem ::= | "("  pathlist  ")" 
    #             | "["  propertylist  "]" 
    #             | "{"  formulacontent  "}" 
    #             | boolean
    #             | literal
    #             | numericliteral
    #             | quickvariable
    #             | symbol
    if not isinstance(nextState,tuple):
        nextState = (nextState,)
    nextState = nextState + ('pathtail',)
    return [
        #pathlist
        (r'\(', Punctuation, nextState + ('list',)),
        #properylist
        (r'\[', Punctuation, nextState + ('propertyList',)),
        #formulacontent
        (r'\{', Punctuation, nextState + ('root',)),
        #boolean
        (r'@false|@true', Keyword.Constant, nextState),
        #literal
        (r'("""[^"\\]*(?:(?:\\.|"(?!""))[^"\\]*)*""")|("[^"\\]*(?:\\.[^"\\]*)*")', String, nextState + ('dtlang',)),
        #numericliteral ::= double|integer|rational
        (r'[-+]?[0-9]+(\.[0-9]+)?([eE][-+]?[0-9]+)', Number.Float, nextState),
        (r'[-+]?[0-9]+', Number.Integer, nextState),
        (r'[-+]?[0-9]+/[0-9]+', Number, nextState),
        #quickvariable
        (_quickvariable, Name.Variable, nextState),
        #symbol
        (_symbol, symbolAction, nextState),
    ]

class Notation3Lexer(RegexLexer):
    """
    Lexer for the N3 / Turtle / NT
    """
    name = 'N3'
    aliases = ['n3', 'turtle']
    filenames = ['*.n3', '*.ttl', '*.NT']
    mimetypes = ['text/rdf+n3','application/x-turtle','application/n3']

    tokens = {
        'whitespaces': [
            (r'(#.*)', Comment),
            (r'\s+', Text),
        ],
        'pathtailExpression': expression(Name.Function, '#pop'),
        'pathtail': [
            # No whitespaces allowed in front!
            (r'(^|!|\.)(?!\s)', Operator, 'pathtailExpression'),
            (r'', Text, '#pop'),
        ],
        # statement:
        'root': [
            include('whitespaces'),
            # declaration ::= base|prefix|keywords
            (r'(@(?:prefix|base)\s*)(\w*:\s+)?(<[^>]*>\s*\.)', bygroups(Keyword,Name.Variable,Name.Namespace)),
            (r'(@keywords)(\s*\w+\s*,)*(\s*\w+)', bygroups(Keyword,Text,Text)),
            # existential|universal
            (r'@forSome|@forAll', Name.Class, 'symbol_csl'),
            # Terminating a formula
            (r'\}', Punctuation, '#pop'),
        ] + expression(Name.Class, 'propertyList'),
        'propertyList': [
            #predicate ::= | "<=" 
            #              | "=" 
            #              | "=>" 
            #              | "@a" 
            #              | "@has"  expression
            #              | "@is"  expression  "@of" 
            #              | expression
            include('whitespaces'),
            (r';', Punctuation),
            (r'(<=|=>|=|@?a(?=\s))', Operator, 'objectList'),
            (r'\.', Punctuation, '#pop'),
            (r'\]', Punctuation, '#pop'),
            (r'(?=\})', Text, '#pop'),
        ] + expression(Name.Function, 'objectList'),
        'objectList': [
            include('whitespaces'),
            (r',', Punctuation),
            (r'(?=;)', Text, '#pop'),
            (r'(?=\.)', Text, '#pop'),
            (r'(?=\])', Text, '#pop'),
            (r'(?=\})', Text, '#pop'),
        ] + expression(Name.Attribute, ()),
        'list': [
            include('objectList'),
            (r'\)', Punctuation, '#pop'),
        ],
        'symbol_csl': [
            include('whitespaces'),
            (r',', Punctuation),
            (_symbol, Name.Variable),
            (r'.', Punctuation, '#pop'),
        ],
        'dtlang': [
            #dtlang ::= "@" langcode|"^^" symbol|void
            (r'@[a-z]+(-[a-z0-9]+)*', Name.Attribute, '#pop'),
            (r'\^\^'+_symbol, Name.Attribute, '#pop'),
            (r'', Text, '#pop'),
        ],
    }

#!/usr/bin/env python3

import sys
import argparse
from delphin.mrs import simplemrs, mrx, dmrx, eds, simpledmrs
from io import open

mrsformats = {
    u'simplemrs': simplemrs,
    u'mrx': mrx,
    u'dmrx': dmrx,
    u'eds': eds,
    u'simpledmrs': simpledmrs
}

parser = argparse.ArgumentParser(description=u"Utility for manipulating MRSs")
subparsers = parser.add_subparsers(dest=u'command')

convert_parser = subparsers.add_parser(u'convert', aliases=[u'c'])
convert_parser.add_argument(u'--from', u'-f', dest=u'srcfmt',
                            choices=list(mrsformats.keys()))
convert_parser.add_argument(u'--to', u'-t', dest=u'tgtfmt',
                            choices=list(mrsformats.keys()))
convert_parser.add_argument(u'--pretty-print', u'-p', action=u'store_true')
convert_parser.add_argument(u'--color', u'-c', action=u'store_true')
convert_parser.add_argument(u'infile', metavar=u'PATH', nargs=u'?')

path_parser = subparsers.add_parser(u'paths', aliases=[u'p'])
path_parser.add_argument(u'--format', u'-f', choices=list(mrsformats.keys()))
path_parser.add_argument(u'--depth', u'-d', default=-1)
path_parser.add_argument(u'infile', metavar=u'PATH', nargs=u'?')

args = parser.parse_args()
if args.command in (u'convert', u'c'):
    srcfmt = mrsformats[args.srcfmt]
    if args.infile is not None:
        ms = srcfmt.load(open(args.infile, u'r'))
    else:
        ms = srcfmt.loads(sys.stdin.read())
    outstream = sys.stdout
    mrsformats[args.tgtfmt].dump(outstream, ms,
                                 pretty_print=args.pretty_print,
                                 color=args.color)
elif args.command in (u'paths', u'p'):
    from delphin.mrs import path as mrspath
    if args.infile is not None:
        instream = open(args.infile, u'r')
    else:
        instream = sys.stdin
    outstream = sys.stdout
    ms = mrsformats[args.format].load(instream)
    for m in ms:
        paths = list(mrspath.get_paths(m, max_depth=int(args.depth)))
        print u'\t'.join(paths)

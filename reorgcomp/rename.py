#!/usr/bin/env python

import os
import sys
import hashlib

import argparse

from pprint import pprint
from difflib import SequenceMatcher

# https://pypi.python.org/pypi/python-magic/
import magic


def fixname(s):
    return s.replace("Chord", "Magnet").replace("chord", "magnet")


def longestpath(x, y):
    return -cmp(len(x[0]) + len(x[1]), len(y[0]) + len(y[1]))

    
def rename_dirs():

    paths = []

    for (dirpath, dirnames, filenames,) in os.walk('.'):
        for dirname in dirnames:
            paths.append((dirpath, dirname))

    paths.sort(longestpath)

    for (dirpath, dirname) in paths:

        newname = fixname(dirname)
        if newname != dirname:

            oldname = os.path.join(dirpath, dirname)
            newname = os.path.join(dirpath, newname)
            print "Renaming '%s' -> '%s'" % (oldname, newname,)
            os.rename(oldname, newname)


def is_text_mimetype(filename):

    mimetype = magic.from_file(filename, mime=True)
    return ('text/' in mimetype) or ('xml' in mimetype)


def rename_files():

    for (dirpath, dirnames, filenames,) in os.walk('.'):
        for filename in filenames:

            oldname = os.path.join(dirpath, filename)
            newname = fixname(oldname)

            if oldname != newname:

                print "Renaming '%s' to '%s'" % (oldname, newname,)
                os.rename(oldname, newname)

            if is_text_mimetype(newname):

                with open(newname) as fp:
                    data = fp.read()

                if ("chord" in data) or ("Chord" in data):

                    data = fixname(data)
                    print "Replacing content in '%s'" % (newname,)

                    with open(newname, 'w') as fp:
                        fp.write(data)


def get_uniqueness_of_files():

    names = {}

    for (dirpath, dirnames, filenames,) in os.walk('.'):
        for filename in filenames:
            ls = names.setdefault(filename, [])
            ls.append(dirpath)

    return names


def get_pairs(ls):
    yielded = set()
    for x in ls:
        for y in ls:
            if ( x != y ):
                already = str.join('', sorted([x, y]))
                if already in yielded:
                    continue
                yielded.add(already)
                yield x, y


def get_ratio(data1, data2):
    return SequenceMatcher(str.isspace, data1, data2).ratio()


def are_file_names_unique():

    names = get_uniqueness_of_files()

    for filen in names:

        if len(names[filen]) > 1:

            print filen, names[filen]
            for (dirx, diry) in get_pairs(names[filen]):

                pathx = os.path.join(dirx, filen)
                datax = open(pathx).read()

                pathy = os.path.join(diry, filen)
                datay = open(pathy).read()

                hashx = hashlib.sha1(datax).digest()
                hashy = hashlib.sha1(datay).digest()

                if hashy == hashx:
                    print (dirx, diry, 0)

                else:
                    if is_text_mimetype(pathx) and is_text_mimetype(pathy):
                        print (dirx, diry, get_ratio(datax, datay))
                    else:
                        print "Binary files where different..."


_get_matching_names_cache = {}

def get_dirs_with_filename(scandir, target):

    if scandir not in _get_matching_names_cache:
        _get_matching_names_cache[scandir] = {}
        d = _get_matching_names_cache[scandir]
        for (dirpath, dirnames, filenames,) in os.walk(scandir):
            for filename in filenames: 
                d.setdefault(filename, []).append(dirpath)

    d = _get_matching_names_cache[scandir]
    if target in d:
        return d[target]

    return []
    

def detect_move(basenew = None, oldfile = None):
    matches = []
    oldfiledir, oldfilename = os.path.split(oldfile)
    dataold = open(oldfile).read()
    for dirpath in get_dirs_with_filename(basenew, oldfilename):
        fullpath = os.path.join(dirpath, oldfilename)
        ratio = -1
        if is_text_mimetype(fullpath):
            data = open(fullpath).read()
            ratio = get_ratio(dataold, data)
        matches.append( (fullpath, ratio) )
    return matches


def detect_moves(basenew = None, baseold = None):
    moves = []
    for (dirpath, dirnames, filenames,) in os.walk(baseold):
        if 'zmq' in dirpath:
            continue
        print dirpath
        for filename in filenames:
            fp = os.path.join(dirpath, filename)
            moves.append( (fp, detect_move(basenew, fp)) )
    return moves


COMMAND_RENAME = "rename"
COMMAND_UNIQUE = "unique"
COMMAND_FINDMOVE = "findmove"
COMMAND_FINDMOVES = "findmoves"

COMMANDS = [
    COMMAND_RENAME,
    COMMAND_UNIQUE,
    COMMAND_FINDMOVE,
    COMMAND_FINDMOVES,
]


def parse_arguments(args=sys.argv[1:]):

    parser = argparse.ArgumentParser()

    parser.add_argument("--addrename", nargs=2, action="append")

    parser.add_argument("--basenew")
    parser.add_argument("--oldfile")
    parser.add_argument("--baseold")

    parser.add_argument("--cmd", choices=COMMANDS)

    namespace = parser.parse_args(args)

    if namespace.cmd == COMMAND_FINDMOVE:
        if not namespace.basenew:
            parser.error("Command requires --basenew")
        if not namespace.oldfile:
            parser.error("Command requires --oldfile")
    if namespace.cmd == COMMAND_FINDMOVES:
        if not namespace.basenew:
            parser.error("Command requires --basenew")
        if not namespace.baseold:
            parser.error("Command requires --baseold")

    return namespace


def main():

    config = parse_arguments()

    if  config.cmd == COMMAND_RENAME:
        rename_dirs()
        rename_files()

    elif config.cmd == COMMAND_UNIQUE:
        are_file_names_unique()

    elif config.cmd == COMMAND_FINDMOVE:
        matches = detect_move(basenew = sys.argv[2], oldfile = sys.argv[3])
        pprint(matches)

    elif config.cmd == COMMAND_FINDMOVES:
        moves = detect_moves(basenew = sys.argv[2], baseold = sys.argv[3])
        pprint(moves)


if __name__ == '__main__':
    main()
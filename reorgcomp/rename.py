#!/usr/bin/env python

import os
import sys
import hashlib
import subprocess
import argparse

from pprint import pprint, pformat

from difflib import SequenceMatcher

# https://pypi.python.org/pypi/python-magic/
import magic

from unrepr import unrepr


PRETEND_OPS = False

_fixname_renames = []

def fixname(s):
    for (from_, to_) in _fixname_renames:
        s = s.replace(from_, to_)
    return s


def longestpath(x, y):
    return -cmp(len(x[0]) + len(x[1]), len(y[0]) + len(y[1]))


_rename_target = "."

def rename_dirs(
    os_walk = os.walk,
    os_rename = os.rename
    ):

    paths = []

    for (dirpath, dirnames, filenames,) in os_walk(_rename_target):
        for dirname in dirnames:
            paths.append((dirpath, dirname))

    paths.sort(longestpath)

    for (dirpath, dirname) in paths:

        newname = fixname(dirname)
        if newname != dirname:

            oldname = os.path.join(dirpath, dirname)
            newname = os.path.join(dirpath, newname)
            print "Renaming '%s' -> '%s'" % (oldname, newname,)

            if not PRETEND_OPS:
                os_rename(oldname, newname)


def is_text_mimetype(filename):

    mimetype = magic.from_file(filename, mime=True)
    return ('text/' in mimetype) or ('/xml' in mimetype)


def rename_files():

    for (dirpath, dirnames, filenames,) in os.walk(_rename_target):
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
    return sorted(matches, cmp=lambda x,y: -cmp(x[1], y[1]))


def save_output(outfile, output):
    fp = open(outfile, 'w')
    fp.write(pformat(output, 0, 80))


def read_input(filename):
    return unrepr(open(filename).read())


def detect_moves(basenew = None, baseold = None, outfile = None):
    moves = []
    for (dirpath, dirnames, filenames,) in os.walk(baseold):
        if 'zmq' in dirpath:
            continue
        print dirpath
        for filename in filenames:
            fp = os.path.join(dirpath, filename)
            moves.append( (fp, detect_move(basenew, fp)) )
    if outfile != None:
        save_output(outfile, moves)
    return moves


def pick_likely_moves(movesfile, outfile = None):

    approved = []
    moves = read_input(movesfile)

    for move in moves:

        index = 0

        filename, matches = move
        print ">>> For file: %s" % (filename,)

        while True:

            if not matches:
                print ">>> No potential matches for: %s" % (filename,)
                approved.append((filename, None,))
                break

            match = matches[index]
            potential, ratio = match

            print ">>> Considering this location: %s (ratio = %.02f)" % (potential, ratio,)

            print (">>> Select action " +
                "(a = accept, r = reject, d = diff, n = next, p = previous):"),

            try:
                inp = raw_input()
            except KeyboardInterrupt:
                return

            if   inp == 'a':
                approved.append( (filename, potential,) )
                break
            elif inp == 'r':
                matches.pop(index)
                if len(matches) <= 0:
                    print "!!! Warning: all files rejected"
                    break
                index = (index) % len(matches)
            elif inp == 'd':
                subprocess.call(["meld", filename, potential])
                continue
            elif inp == 'n':
                index = (index + 1) % len(matches)
            elif inp == 'p':
                index = (index - 1)
                if index < 0: index = len(matches) - 1
            elif inp == '':
                continue
            else:
                print ">>> Invalid selection!"

    if outfile:
        save_output(outfile, approved)

    return approved


COMMAND_RENAME = "rename"
COMMAND_UNIQUE = "unique"
COMMAND_FINDMOVE = "findmove"
COMMAND_FINDMOVES = "findmoves"
COMMAND_PICK = "pick"

COMMANDS = [
    COMMAND_RENAME,
    COMMAND_UNIQUE,
    COMMAND_FINDMOVE,
    COMMAND_FINDMOVES,
    COMMAND_PICK,
]


def parse_arguments(args=sys.argv[1:]):

    global PRETEND_OPS
    global _rename_target

    parser = argparse.ArgumentParser()

    parser.add_argument("--pretend", action="store_true")

    parser.add_argument("--addrename", nargs=2, action="append")
    parser.add_argument("--rename_target")

    parser.add_argument("--basenew")
    parser.add_argument("--oldfile")
    parser.add_argument("--baseold")
    parser.add_argument("--infile")
    parser.add_argument("--outfile")

    parser.add_argument("--cmd", choices=COMMANDS)

    namespace = parser.parse_args(args)

    if namespace.cmd == COMMAND_FINDMOVE:
        if not namespace.basenew:
            parser.error("Command requires --basenew")
        if not namespace.oldfile:
            parser.error("Command requires --oldfile")

    elif namespace.cmd == COMMAND_FINDMOVES:
        if not namespace.basenew:
            parser.error("Command requires --basenew")
        if not namespace.baseold:
            parser.error("Command requires --baseold")

    elif namespace.cmd == COMMAND_PICK:
        if not namespace.infile:
            parser.error("Command requires --infile=<INFILE>")

    if namespace.pretend:
        PRETEND_OPS = True

    if namespace.rename_target:
        _rename_target = namespace.rename_target

    if namespace.addrename:
        for (from_, to_) in namespace.addrename:
            _fixname_renames.append((from_, to_,))

    return namespace


def main():

    config = parse_arguments()

    if config.cmd == COMMAND_RENAME:

        rename_dirs()
        rename_files()

    elif config.cmd == COMMAND_UNIQUE:
        are_file_names_unique()

    elif config.cmd == COMMAND_FINDMOVE:
        matches = detect_move(basenew = config.basenew, oldfile = config.oldfile)
        pprint(matches)

    elif config.cmd == COMMAND_FINDMOVES:
        moves = detect_moves(basenew = config.basenew,
                             baseold = config.baseold,
                             outfile = config.outfile)
        pprint(moves)

    elif config.cmd == COMMAND_PICK:
        picks = pick_likely_moves(config.infile, outfile = config.outfile)
        pprint(picks)


if __name__ == '__main__':
    main()
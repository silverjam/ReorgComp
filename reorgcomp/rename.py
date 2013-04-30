#!/usr/bin/env python

import re
import os
import sys
import difflib
import hashlib
import subprocess
import argparse
import textwrap

from pprint import pprint, pformat

from difflib import SequenceMatcher

# https://pypi.python.org/pypi/python-magic/
import magic

from unrepr import unrepr


GLOBAL_EXCLUDE = None
GLOBAL_INCLUDE = None

PRETEND_OPS = False

_fixname_renames = []

def fixname(s):
    for (from_, to_) in _fixname_renames:
        s = s.replace(from_, to_)
    return s

def fixnameable(s):
    for (target, _) in _fixname_renames:
        if target in s:
            return True
    return False

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
                if fixnameable(data):
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


def get_ratio_of_files(file1, file2):
    return SequenceMatcher(str.isspace, open(file1).read(), open(file2).read()).ratio()

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
        if GLOBAL_EXCLUDE and GLOBAL_EXCLUDE.search(dirpath):
            continue
        print dirpath
        for filename in filenames:
            fp = os.path.join(dirpath, filename)
            moves.append( (fp, detect_move(basenew, fp)) )
    if outfile != None:
        save_output(outfile, moves)
    return moves


def generate_ratios(infile, outfile = None):

    ratios = []
    moves = read_input(infile)

    for (orig, dest) in moves:

        print "%s -> %s" % (orig, dest)

        if not dest:
            continue

        if not (is_text_mimetype(orig) and is_text_mimetype(dest)):
            continue

        ratio = get_ratio_of_files(orig, dest)

        ratios.append((orig, dest, ratio))

    if outfile:
        save_output(outfile, ratios)

    return ratios


def find_duplicate_targets(infile, outfile = None):

    moves = read_input(infile)
    targets = {}

    for move in moves:

        orig = move[0]
        dest = move[1]

        ratio = None
        if len(move) > 2:
            ratio = move[2]

        if ratio:
            targets.setdefault(dest, []).append((orig, ratio))
        else:
            targets.setdefault(dest, []).append((orig,))


    for key in targets.keys():
        if not len(targets[key]) > 1:
            del targets[key]

    targets = targets.items()

    if outfile != None:
        save_output(outfile, targets)

    return targets


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


def filter_picks(infile, outfile = None):

    filtered = []
    moves = read_input(infile)

    for move in moves:

        orig = move[0]
        dest = move[1]

        ratio = None

        if len(move) > 2:
            ratio = move[2]

        include = None

        if GLOBAL_INCLUDE:

            include = False 

            if GLOBAL_INCLUDE.search(orig):
                include = True
            if dest and GLOBAL_INCLUDE.search(dest):
                include = True
            #if ratio and GLOBAL_INCLUDE.search(ratio):
            #    include = True

        if GLOBAL_EXCLUDE:

            include = True
            
            if GLOBAL_EXCLUDE.search(orig):
                include = False
            if dest and GLOBAL_EXCLUDE.search(dest):
                include = False
            #if ratio and GLOBAL_EXCLUDE.search(ratio):
            #    include = False

        item = (orig, dest)
        if ratio:
            item = (orig, dest, ratio)

        if include:
            filtered.append(item)

        print "%s -> %s" % (orig, dest)

    if outfile:
        save_output(outfile, filtered)

    return filtered


def average_ratios(infile):

    moves = read_input(infile)
    ratio_sum = 0
    count = 0
    for (_, _, ratio) in moves:
        ratio_sum += ratio
        count += 1
    return ratio_sum / count


def pick_top_of_dupes(infile, outfile = None):

    dupes = read_input(infile)
    picks = []

    for (dest, origs) in dupes:

        origs.sort(cmp = lambda x,y: -cmp(x[1], y[1]))
        picks.append((origs[0][0], dest, origs[0][1],))

    if outfile:
        save_output(outfile, picks) 

    return picks


def remove_unresolved_pick(infile, additional, outfile = None):

    filtered = []
    moves = read_input(infile)
    resolved = read_input(additional)

    resolved_dict = {}
    for resolve in resolved:
        resolved_dict[resolve[1]] = resolve[0]

    for move in moves:

        orig = move[0]
        dest = move[1]

        #print orig, dest

        ratio = None

        if len(move) > 2:
            ratio = move[2]

        if dest in resolved_dict:
            source = resolved_dict[dest]
            if orig != source:
                print 'REMOVED: ', dest
                continue

        item = (orig, dest)
        if ratio:
            item = (orig, dest, ratio)

        filtered.append(item)

    if outfile:
        save_output(outfile, filtered)

    return filtered


def merge_adds_and_deletes(infile, baseold, basenew, outfile = None):

    withaddsdels = []
    moves = read_input(infile)

    orig_set = set() 
    dest_set = set() 

    for move in moves:
        orig = move[0]
        orig_set.add(orig)
        dest = move[1]
        dest_set.add(dest)

    for (dirpath, dirnames, filenames,) in os.walk(baseold):
        for filename in filenames:
            fp = os.path.join(dirpath, filename)
            if GLOBAL_EXCLUDE and GLOBAL_EXCLUDE.search(fp):
                continue
            if fp not in orig_set:
                withaddsdels.append((fp, None, -1))

    withaddsdels = []

    for (dirpath, dirnames, filenames,) in os.walk(basenew):
        for filename in filenames:
            fp = os.path.join(dirpath, filename)
            if GLOBAL_EXCLUDE and GLOBAL_EXCLUDE.search(fp):
                continue
            if fp not in dest_set:
                withaddsdels.append((None, fp, -1))


    moves.extend(withaddsdels)

    def insort(idx):
        def func(x, y):
            if x[idx] == None or y[idx] == None:
                return 0
            return cmp(x[idx], y[idx])
        return func

    def insortadds():
        return insort(0)

    def insortdels():
        return insort(1)

    moves.sort(cmp=insortadds())
    moves.sort(cmp=insortdels())

    if outfile:
        save_output(outfile, moves)

    return moves


def generate_diffs(infile):

    moves = read_input(infile)

    for move in moves:

        orig = move[0]
        dest = move[1]

        regex = re.compile('\r\n|\n|\r')

        if orig != None and not is_text_mimetype(orig):
            continue

        if dest != None and not is_text_mimetype(dest):
            continue

        orig_data = []
        if orig != None:
            orig_data = regex.split(open(orig).read())

        dest_data = []
        if dest != None:
            dest_data = regex.split(open(dest).read())

        diff = difflib.unified_diff([S.rstrip() + '\n' for S in orig_data], [S.rstrip() + '\n' for S in dest_data], orig, dest) 
        print ''.join(diff)


COMMAND_RENAME = "rename"
COMMAND_UNIQUE = "unique"
COMMAND_FINDMOVE = "findmove"
COMMAND_FINDMOVES = "findmoves"
COMMAND_PICK = "pick"
COMMAND_RATIO = "ratio"
COMMAND_FILTER_PICKS = "filter"
COMMAND_AVERAGE = "average"
COMMAND_DUPLICATES = "duplicates"
COMMAND_UNDUPE = "undupe"
COMMAND_UNRESOLVE = "unresolve"
COMMAND_DIFF = "diff"
COMMAND_WITHADDSDELS = "w_addsdels"

COMMANDS = [
    COMMAND_RENAME,
    COMMAND_UNIQUE,
    COMMAND_FINDMOVE,
    COMMAND_FINDMOVES,
    COMMAND_PICK,
    COMMAND_RATIO,
    COMMAND_FILTER_PICKS,
    COMMAND_AVERAGE,
    COMMAND_DUPLICATES,
    COMMAND_UNDUPE,
    COMMAND_UNRESOLVE,
    COMMAND_DIFF,
    COMMAND_WITHADDSDELS,
]


def parse_arguments(args=sys.argv[1:]):

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent("""
            Commands available (--cmd):

            - 'rename'    : rename all the directories, files, and then contents according
                            to the specified renames (added with --addrename)

            - 'unique'    : attempt to determine how unique the file names are in the 
                            current directory

            - 'findmove'  : for a particular file (--oldfile) determine if that file has
                            been moved within a new directory (--basenew), also returns 
                            the edit ratio similarity of those files

            - 'findmoves' : for a given old directory (--baseold) determine where files
                            have moved according to their name and edit similarity to 
                            files with the same name in the new directory (--basenew),
                            moves generated should be saved with --outfile

            - 'pick'      : for a given set of moves (--inflie), display a UI to allow
                            the user to pick a move that most closely matches, during which
                            the use is allowed to diff the files and view the match ratio

            - 'ratio'     : for a given set of picks (--inflie), generate the similarity
                            ratio between it and the picked destination

            - 'filter'    : for a given set of picks (--inflie), filter the picks based on
                            the given criteria

            - 'average'   : for a given set of picks (--inflie), give the average ratio 
                            of those picks

            - 'duplicates': for a given set of picks (--inflie), find files that have
                            duplicate targets

            - 'undupe'    : for a given set of duplicates (--inflie), pick the dest file
                            that most closely matches

            - 'unresolve' : for a given set of picks (--infile), remove the picks that where
                            not selected as 'correct' during a 'duplicates' + 'undupe' pass

            - 'diff'      : generate diffs for a given set of moves (--infile)

            - 'w_addsdels': put adds and deletes back in to the list of files so that a
                            'diff' command will display them
                           
        """)
    )

    parser.add_argument("--pretend", action="store_true")

    parser.add_argument("--addrename", nargs=2, action="append")
    parser.add_argument("--rename_target")

    parser.add_argument("--exclude")
    parser.add_argument("--include")

    parser.add_argument("--basenew", help="base of the new collection of files")
    parser.add_argument("--oldfile", help="the path to the old file within the old base")
    parser.add_argument("--baseold", help="base of the old collection of files")
    parser.add_argument("--infile", help="input file for certain commands (pick, filter, ratio, average, duplicates, undupe, unresolve)")
    parser.add_argument("--infile2", help="additional input file for certain commands (unresolve)")
    parser.add_argument("--outfile", help="output file to save the results of certain commands (findmoves, pick, filter, ratio, filter, duplicates, undupe, unresolve)")

    parser.add_argument("--cmd", choices=COMMANDS, help="perform a command, see above for descriptions")

    namespace = parser.parse_args(args)

    requires_infile = set([
        COMMAND_PICK,
        COMMAND_FILTER_PICKS,
        COMMAND_RATIO,
        COMMAND_AVERAGE,
        COMMAND_DUPLICATES,
        COMMAND_UNDUPE,
        COMMAND_UNRESOLVE,
        COMMAND_DIFF,
        COMMAND_WITHADDSDELS,
        ])

    requires_baseold = set([
        COMMAND_FINDMOVE,
        COMMAND_FINDMOVES,
        COMMAND_WITHADDSDELS,
        ])

    requires_basenew = set([
        COMMAND_FINDMOVE,
        COMMAND_FINDMOVES,
        COMMAND_WITHADDSDELS,
        ])

    if namespace.cmd == COMMAND_FINDMOVE:
        if not namespace.oldfile:
            parser.error("Command requires --oldfile")

    if namespace.cmd in requires_basenew:
        if not namespace.basenew:
            parser.error("Command requires --basenew")

    if namespace.cmd in requires_baseold:
        if not namespace.baseold:
            parser.error("Command requires --baseold")

    if namespace.cmd in requires_infile:
        if not namespace.infile:
            parser.error("Command requires --infile=<INFILE>")

    if namespace.cmd == COMMAND_UNRESOLVE:
        if not namespace.infile2:
            parser.error("Command requires --infile2=<INFILE2>")

    global PRETEND_OPS

    if namespace.pretend:
        PRETEND_OPS = True

    global _rename_target

    if namespace.rename_target:
        _rename_target = namespace.rename_target

    if namespace.addrename:
        for (from_, to_) in namespace.addrename:
            _fixname_renames.append((from_, to_,))

    global GLOBAL_EXCLUDE, GLOBAL_INCLUDE

    if namespace.exclude:
        GLOBAL_EXCLUDE = re.compile(namespace.exclude)

    if namespace.include:
        GLOBAL_INCLUDE = re.compile(namespace.include)

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

    elif config.cmd == COMMAND_RATIO:
        ratios = generate_ratios(config.infile, outfile = config.outfile)
        pprint(ratios)

    elif config.cmd == COMMAND_FILTER_PICKS:
        filtered = filter_picks(config.infile, outfile = config.outfile)
        pprint(filtered)

    elif config.cmd == COMMAND_AVERAGE:
        average = average_ratios(config.infile)
        pprint(average)

    elif config.cmd == COMMAND_DUPLICATES:
        dupes = find_duplicate_targets(config.infile, outfile= config.outfile)
        pprint(dupes)

    elif config.cmd == COMMAND_UNDUPE:
        undupe = pick_top_of_dupes(config.infile, outfile=config.outfile)
        pprint(undupe)

    elif config.cmd == COMMAND_UNRESOLVE:
        filtered = remove_unresolved_pick(config.infile, config.infile2, outfile=config.outfile)
        pprint(filtered)

    elif config.cmd == COMMAND_DIFF:
        generate_diffs(config.infile)

    elif config.cmd == COMMAND_WITHADDSDELS:
        moves = merge_adds_and_deletes(config.infile, config.baseold, config.basenew, outfile=config.outfile)
        pprint(moves)


if __name__ == '__main__':
    main()
ReorgCompare
============

A tool to prep directories (with source files) for comparison.  These will be
directories that should be very similar (e.g. two different snapshots of a
projects source code).  

The tool should be able to prep the directories by performing various known
renames and/or automatically detecting moved / renamed files.

Help output:

    usage: reorg [-h] [--pretend] [--addrename ADDRENAME ADDRENAME]
                [--rename_target RENAME_TARGET] [--exclude EXCLUDE]
                [--include INCLUDE] [--basenew BASENEW] [--oldfile OLDFILE]
                [--baseold BASEOLD] [--infile INFILE] [--infile2 INFILE2]
                [--outfile OUTFILE]
                [--cmd {rename,unique,findmove,findmoves,pick,ratio,filter,average,duplicates,undupe,unresolve,diff}]

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

    optional arguments:
    -h, --help            show this help message and exit
    --pretend
    --addrename ADDRENAME ADDRENAME
    --rename_target RENAME_TARGET
    --exclude EXCLUDE
    --include INCLUDE
    --basenew BASENEW     base of the new collection of files
    --oldfile OLDFILE     the path to the old file within the old base
    --baseold BASEOLD     base of the old collection of files
    --infile INFILE       input file for certain commands (pick, filter, ratio,
                            average, duplicates, undupe, unresolve)
    --infile2 INFILE2     additional input file for certain commands (unresolve)
    --outfile OUTFILE     output file to save the results of certain commands
                            (findmoves, pick, filter, ratio, filter, duplicates,
                            undupe, unresolve)
    --cmd {rename,unique,findmove,findmoves,pick,ratio,filter,average,duplicates,undupe,unresolve,diff}
                            perform a command, see above for descriptions


Usage example:

    reorg --cmd rename --rename_target=NewThing --addrename OLD NEW \
        --addrename Old New --addrename old new
    reorg --cmd findmoves --basenew NewThing --baseold OldThing \
        --outfile moves.txt
    reorg --cmd pick --basenew NewThing --baseold NewThing --infile moves.txt \
        --outfile reorg_picks.txt 
    reorg --cmd ratio --infile reorg_picks.txt --outfile reorg_picks_ratios.txt
    reorg --cmd filter --infile reorg_picks_ratios.txt --include "_v11" \
        --outfile v11_picks.txt
    reorg --cmd filter --infile reorg_picks_ratios.txt --include "_v10" \
        --outfile v10_picks.txt
    reorg --cmd average --infile v11_picks.txt
    reorg --cmd average --infile v11_picks.txt
    reorg --cmd filter --infile reorg_picks_ratios.txt --exclude "_v11" \
        --outfile reorg_picks_ratios_no_v11.txt
    reorg --cmd filter --infile reorg_picks_ratios.txt --include "TestV10" \
        --outfile api10_picks.txt
    reorg --cmd filter --infile reorg_picks_ratios.txt --include "TestV15" \
        --outfile api15_picks.txt
    reorg --cmd average --infile api15_picks.txt 
    reorg --cmd average --infile api10_picks.txt 
    reorg --cmd filter --outfile reorg_picks_ratios_no_v11_no_api15.txt \
        --exclude "TestV15" --infile reorg_picks_ratios_no_v11.txt
    reorg --cmd duplicates --infile reorg_picks_ratios_no_v11_no_api15.txt \
        --outfile dupes.txt
    reorg --cmd undupe --infile dupes.txt --outfile resolved_picks.txt
    reorg --cmd unresolve --infile2 resolved_picks.txt \
        --infile reorg_picks_ratios_no_v11_no_api15.txt \
        --outfile reorg_picks_ratios_no_v11_no_api15_no_dupes.txt
    reorg --cmd diff --infile reorg_picks_ratios_no_v11_no_api15_no_dupes.txt

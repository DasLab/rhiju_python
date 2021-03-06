#!/usr/bin/python

from sys import argv,exit
from os import popen, system
from os.path import basename,exists,expanduser
import string
import commands
from glob import glob

def Help():
    print
    print 'Usage: '+argv[0]+' <silent out file 1> < silent file 2> ... <N> '
    print '  Will extract N decoys with lowest score from each silent file.'
    print '  If you want to select based on another column, say 12 (Rg), the'
    print '    last arguments should be -12 <N>  (for lowest Rg) or +12 <N>'
    print '    (for highest Rg).'
    print

    exit()


if len(argv)<2:
    Help()

replace_names = 1
if argv.count('-no_replace_names'):
    pos = argv.index('-no_replace_names')
    del( argv[pos] )
    replace_names = 0


extract_first_chain = 0
if argv.count('-extract_first_chain'):
    pos = argv.index('-extract_first_chain')
    del( argv[pos] )
    extract_first_chain = 1

start_at_zero = 0
if argv.count('-start_at_zero'):
    pos = argv.index('-start_at_zero')
    del( argv[pos] )
    start_at_zero = 1

use_start_pdb = 0
if argv.count('-start_pdb'):
    pos = argv.index('-start_pdb')
    del( argv[pos] )
    start_pdb_file = argv[ pos ]
    del( argv[pos] )
    use_start_pdb = 1

output_virtual = 0
if argv.count('-output_virtual'):
    pos = argv.index('-output_virtual')
    del( argv[pos] )
    output_virtual = 1

#output_virtual = 1
#if argv.count('-no_virtual'):
#    pos = argv.index('-no_virtual')
#    del( argv[pos] )
#    output_virtual = 0

try:
    NSTRUCT = int(argv[-1])
    del(argv[-1])
except:
    NSTRUCT = 2

scorecol_defined = 0
try:
    scorecol = int(argv[-1])
    del(argv[-1])
    scorecol_defined = 1
except:
    scorecol = -1


REVERSE = ''
if scorecol > 0:
    REVERSE = ' --reverse '

#Another possibility... user supplies -rms or +rms
scorecol_name_defined = 0
if not scorecol_defined:
    scorecol_name = argv[-1]
    if scorecol_name[0] == '-':
        scorecol_name_defined = 1
        scorecol_name = scorecol_name[1:]
        del( argv[-1] )
        REVERSE = ''
    if scorecol_name[0] == '+':
        scorecol_name_defined = 1
        scorecol_name = scorecol_name[1:]
        REVERSE = '-r'
        del( argv[-1] )

infiles = argv[1:]

HOMEDIR = expanduser('~')

MINI_DIR = HOMEDIR + '/src/mini/bin/'
DB = HOMEDIR+'/minirosetta_database'

if exists( HOMEDIR+'/src/rosetta_protein_rna/rosetta_source/bin/' ):
    MINI_DIR = HOMEDIR + '/src/rosetta_protein_rna/rosetta_source/bin/'
    DB = HOMEDIR + '/src/rosetta_protein_rna/rosetta_database/'

if exists( HOMEDIR+'/src/rosetta_TRUNK/rosetta_source/bin/' ):
    MINI_DIR = HOMEDIR + '/src/rosetta_TRUNK/rosetta_source/bin/'
    DB = HOMEDIR + '/src/rosetta_TRUNK/rosetta_database/'

for infile in infiles:
    tags = []

    scoretags = string.split( popen('head -n 2 '+infile).readlines()[1] )
    scoretag=''
    if scorecol_defined:
        scoretag = scoretags[ abs(scorecol) ]

    if scorecol_name_defined:
        scorecol_names = string.split( scorecol_name,',' )
        scorecols = []
        for s in scorecol_names:
            assert( scoretags.count( s ))
            scorecol = scoretags.index( s )
            scorecols.append( scorecol )
        scoretag = scorecol_name
    else:
        scorecols  = [scorecol]


    binary_silentfile = 0
    remark_lines = popen('head -n 7 '+infile).readlines()
    for line in remark_lines:
        if ( len( line ) > 6 and line[:6] == "REMARK" ):
            remark_tags = line.split()
            if remark_tags.count('BINARY_SILENTFILE'):
                binary_silentfile = 1
            if remark_tags.count('BINARY'):
                binary_silentfile = 1

    coarse = 0
    if exists( 'remark_tags') and remark_tags.count('COARSE'):
        coarse = 1

    assert(infile[-3:] == 'out')
#    lines = popen('grep SCORE '+infile+' |  sort -k %d -n %s | head -n %d' % (abs(SCORECOL)+1, REVERSE, NSTRUCT+1) ).readlines()


    # Check if this run appeared to use -termini
    terminiflag = ''
    fid = open( infile, 'r')
    line = 'ATOM'
    while (line.count('ATOM') or line.count('SCORE') or
           line.count('SEQU') or line.count('JUMP') or line.count('FOLD')):
        line = fid.readline()
    if line.count('AAV'):
        terminiflag = ' -termini '


    # Make the list of decoys to extract
    lines = popen( 'grep SCORE '+infile+' | grep -v NATIVE').readlines()

    score_plus_lines = []
    for line in lines:
        cols = string.split( line )
        score = 0.0
        try:
            for scorecol in scorecols: score += float( cols[ abs(scorecol) ] )
        except:
            continue
        if REVERSE: score *= -1
        score_plus_lines.append( ( score, line ))

    score_plus_lines.sort()
    lines = map( lambda x:x[-1], score_plus_lines[:NSTRUCT] )

    templist_name = 'temp.%s.list'% basename(infile)

    fid = open(templist_name,'w')
    count = 0
    for line in lines:
        cols = string.split(line)
        tag = cols[-1]
        if tag.find('desc') < 0:
            fid.write(tag+'\n')
            tags.append(tag)
            count = count+1
        if count >= NSTRUCT:
            break
    outfilename = infile

    fid.close()

    startpdbflag = ''
    if (use_start_pdb): startpdbflag = '-start_pdb '+start_pdb_file

    extract_first_chain_tag = ''
    if (extract_first_chain): extract_first_chain_tag = ' -extract_first_chain '

    #Set up bonds file?
    softlink_bonds_file = 0
    wanted_bonds_file = infile+'.bonds'
    wanted_rot_templates_file = infile+'.rot_templates'
    bonds_files = glob( '*.bonds')
    if len( bonds_files ) > 0:
        if not exists( wanted_bonds_file ):
            softlink_bonds_file = 1
            system( 'ln -fs '+bonds_files[0]+' '+wanted_bonds_file )
            system( 'ln -fs '+bonds_files[0].replace('.bonds','.rot_templates') \
                    +' '+wanted_rot_templates_file )


    # Centroid readout?
    MINI_EXE = MINI_DIR+'extract_pdbs.linuxgccrelease'
    if not exists( MINI_EXE):
        MINI_EXE = MINI_DIR+'/extract_pdbs.macosgccrelease'

    command = '%s -in:file:silent  %s   -in:file:tags %s -database %s -out:file:residue_type_set centroid ' % \
                  ( MINI_EXE, outfilename, string.join( tags ), DB )

    old_rosetta = 0
    scorelabels = string.split( popen( 'head -n 2 '+outfilename ).readlines()[-1] )
    if "SCORE" in scorelabels:
        EXE = HOMEDIR+'/src/rosetta++/rosetta.gcc'
        if not exists( EXE ):
            EXE = 'rm boinc* ros*txt; '+HOMEDIR+'/src/rosetta++/rosetta.mactelboincgraphics '
        assert( exists( EXE ) )
        command = '%s -extract -l %s -paths %s/src/rosetta++/paths.txt -s %s %s %s '% (EXE, templist_name, HOMEDIR,outfilename, terminiflag, startpdbflag+extract_first_chain_tag)
        old_rosetta = 1
        print "OLD_ROSETTA", old_rosetta

    # Check if this is an RNA run.
    fid = open( infile, 'r')
    line = fid.readline(); # Should be the sequence.
    print line
    rna = 0
    sequence = string.split(line)[-1]
    rna = 1
    for c in sequence:
        if not ( c == 'a' or c == 'c' or c == 'u' or c == 'g'):
            rna = 0
            break
    if rna:     command  += ' -enable_dna -enable_rna '


    #        command = command.replace('rosetta++','rosetta_rna')
    #print "RNA? ", rna


    # Check if this is full atom.
    lines = popen('head -n 8 '+outfilename).readlines()
    if len(string.split(lines[6])) > 10:
        command += ' -fa_input'

    # Hey this could be a new mini RNA file
    if rna and not old_rosetta:
        #MINI_EXE = HOMEDIR+'/src/mini/bin/rna_extract.linuxgccrelease'
        #if not exists( MINI_EXE ):
        #    MINI_EXE = HOMEDIR+'/src/mini/bin/rna_extract.macosgccrelease'

        command = '%s -database %s -in::file::silent %s -tags %s  -extract' % \
                  ( MINI_EXE, DB, outfilename, string.join( tags ) )

        if binary_silentfile:
            silent_struct_type = 'binary_rna'
        else:
            silent_struct_type = 'rna'

        command = '%s -database %s -in:file:silent %s -in:file:tags %s -in:file:silent_struct_type %s  ' % \
                  ( MINI_EXE, DB,outfilename, string.join( tags ), silent_struct_type )

        if coarse:
            command += " -out:file:residue_type_set coarse_rna "
        else:
            command += " -out:file:residue_type_set rna "

        if output_virtual: command += " -output_virtual "

    elif ( binary_silentfile ):

        MINI_EXE = MINI_DIR+'extract_pdbs.linuxgccrelease'
        if not exists( MINI_EXE):
            MINI_EXE = MINI_DIR+'/extract_pdbs.macosgccrelease'


        command = '%s -in:file:silent  %s  -in:file:silent_struct_type binary  -in:file:tags %s -database %s  ' % \
                  ( MINI_EXE, outfilename, string.join( tags ), DB )
        if output_virtual: command += " -output_virtual "

        if (scoretags.count('vdw')): command += ' -out:file:residue_type_set centroid '


    print(command)
    system(command)


    if outfilename.find('t343')>0:
        command = HOMEDIR+'/python/extract_t343.py %s %s' % (outfilename,
                                                                 string.join(tags,' '))
        print(command)
        system(command)


    count = 1
    if start_at_zero: count = 0

    if replace_names:
        for tag in tags:
            if scorecol_defined or scorecol_name_defined:
                command = 'mv %s.pdb %s.%s.%d.pdb' % (tag,basename(infile),scoretag,count)
            else:
                command = 'mv %s.pdb %s.%d.pdb' % (tag,basename(infile),count)
            print(command)
            system(command)
            count += 1

    command = 'rm '+templist_name
    print(command)
    system(command)

    if (softlink_bonds_file):
        #system( 'rm '+wanted_bonds_file+' '+wanted_rot_templates_file )
        print ' WARNING! WARNING'
        print ' Found a .bonds and .rot_templates file and used it!'


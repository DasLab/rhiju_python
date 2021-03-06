#!/usr/bin/python

from sys  import argv,exit
from os import system

def Help():
    print
    print 'Usage: pdb2casp.py [-refinement] <file1.pdb> <file2.pdb> ... <CASP number>'
    print
    exit()

try:
    targetnum = int( argv[-1] )
    del(argv[-1])
except:
    try:
        targetnum = int( argv[1][1:4])
    except:
        print 75*'*'
        print 'Last argument must be an integer with CASP target number, e.g. 283'
        print 75*'*'
        Help()

oligomer = 0
if argv.count('-oligomer'):
    oligomer = 1
    pos = argv.index('-oligomer')
    del( argv[pos] )

sg = 0
if argv.count('-sg'):
    sg = 1
    pos = argv.index('-sg')
    del( argv[pos] )

refinement = 0
if argv.count('-refinement'):
    refinement = 1
    pos = argv.index('-refinement')
    del( argv[pos] )

infiles = argv[1:]

## if len(infiles)>5:
##     print 75*'*'
##     print 'TOO MANY MODELS!!!!!'
##     print 75*'*'
##     Help()


for infile in infiles:
    if not infile[-4:] == '.pdb':
        print 75*'*'
        print 'Infiles must end in .pdb.'
        print 75*'*'
        Help()

targetletter = 'T'
if sg:
    targetletter = 'S'

targetletter2 = '0'
refined_tag = ''
if refinement:
    targetletter2 = 'R'
    refined_tag = 'REFINED'

count = 0
for infile in infiles:
    count= count+1

    system( 'cp '+infile+' temp.pdb')
    system( 'replace_chain_inplace.py temp.pdb _ ' )
    system( 'renumber_pdb_in_place.py temp.pdb' )

    lines = open('temp.pdb','r').readlines()

    #outfile = infile[:-4] + '.casp'
    outfile = '%s%s%3d_%d.casp' % (targetletter,targetletter2,targetnum,count)
    fid = open(outfile,'w')

    fid.write('PFRMAT TS\n')
    fid.write('TARGET %s%s%3d' % (targetletter,targetletter2,targetnum) )
    if oligomer: fid.write(' OLIGOMER\n')
    fid.write('\n')
    #    fid.write('AUTHOR 5377-6500-7869\n')
    fid.write('AUTHOR  3598-2403-2731\n')
    fid.write('METHOD ROSETTA provides both ab initio and\n')

    fid.write('METHOD comparative models of protein domains. It\n')
    fid.write('METHOD uses the ROSETTA fragment insertion method\n')
    fid.write('METHOD [Simons et al. J Mol Biol 1997;268:209-225].\n')
    fid.write('METHOD Comparative models are built from structures\n')
    fid.write('METHOD detected by PSI-BLAST, FFAS03, or 3DJury-A1\n')
    fid.write('METHOD and aligned by the K*SYNC alignment method.\n')
    fid.write('METHOD Loop regions are assembled from fragments and\n')
    fid.write('METHOD optimized to fit the aligned template structure.\n')
    fid.write('METHOD For some submissions, models have been refined.\n')
    fid.write('METHOD and scored with a full-atom energy function\n')
    fid.write('METHOD [Bradley et al. Science 2005;309:1868-1871].\n')
    fid.write('MODEL  %d %s\n' % (count,refined_tag) )
    fid.write('PARENT N/A\n')
#    fid.write('PARENT 2f6s_A 2g03_A\n')
    for line in lines:
        if line[:5] == 'ATOM ' or line[:5]=='HETATM':
            line = line[:56] + '1.00  1.00\n'
            fid.write(line)
    fid.write('TER\n')
    fid.write('END\n')

    fid.close()

    system( 'rm temp.pdb' )

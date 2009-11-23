#!/usr/bin/python

from sys import argv
from os import system, getcwd, chdir
from os.path import exists,abspath,expanduser
from glob import glob

outfiles = argv[1:]

try:
    NUM_JOBS_PER_NODE = int( outfiles[-1] )
    del( outfiles[ -1 ] )
except:
    NUM_JOBS_PER_NODE = 20


EXE = './run_charmm_minimize.py'
HOMEDIR = expanduser('~')

bsub_file = open( 'bsubCHARMM','w' )
condor_file = open( 'CHARMM.condor','w' )
condor_file.write('+TGProject = TG-MCB090153\n')
condor_file.write('universe = vanilla\n')
condor_file.write('executable = %s\n' % EXE )
    
CWD = getcwd()

total_count = 0

for outfile in outfiles:

    print outfile

    # Create a directory for extraction
    outdir = outfile.replace( '.out','_OUT')
    if not exists( outdir ):
        command = 'mkdir -p '+outdir
        print( command )
        system( command )


    ####################################################
    # Extract PDB's
    chdir( outdir )
    if ( len(glob( 'S*pdb' )) == 0 and len(glob( 'S*OUT' )) == 0 ) :
        command = 'ln -fs ../'+outfile+' . '
        print( command )
        system( command )

        MINI_EXE = HOMEDIR + '/src/mini/bin/rna_extract.linuxgccrelease'
        if not exists( MINI_EXE ):
            MINI_EXE = HOMEDIR+'/src/mini/bin/rna_extract.macosgccrelease'

        command = '%s -database %s/minirosetta_database/ -in::file::silent %s -in::file::silent_struct_type binary_rna' % \
                  ( MINI_EXE, HOMEDIR, outfile )
        print( command )
        system( command )

        command = 'rm '+outfile # just a soft link anyway
        print( command )
        system( command )

    ####################################################
    # Make subdirectories for each job, and copy in the PDBs, and add line to condor script
    if ( len(glob( 'S*OUT' )) == 0 ) :
        globfiles = glob( 'S_*pdb' )
        for file in globfiles:
            workdir = file.replace( '.pdb', '_OUT' )
            command = 'mkdir -p '+workdir
            print( command )
            system( command )

            command = 'mv '+file+' '+workdir
            print( command )
            system( command )

    count = 0
    start = 0
    globfiles = glob( 'S_*OUT/S*.pdb' )
    globfiles.sort()
    print len( globfiles ),
    if outfile.count( '_native' ) and len( globfiles ) > 1000   : globfiles = globfiles[:1000]
    if outfile.count( '_ideal' ) and len( globfiles ) > 1000    : globfiles = globfiles[:1000]
    if outfile.count( '_nonative' ) and len( globfiles ) > 2000 :   globfiles = globfiles[:2000]
    print len( globfiles )

    for file in globfiles:
        min_pdb_file = file+'.min_pdb'
        if exists( min_pdb_file ):
            continue

        if ( (count % NUM_JOBS_PER_NODE) == 0):
            if ( start == 1 ):
                bsub_file.write( '\n' )
                condor_file.write( '\nQueue 1\n' )
            else:
                start = 1
            bsub_file.write( '\nbsub -W 16:0 %s ' % EXE )
            condor_file.write( '\narguments = ' )
        count += 1
        bsub_file.write( '  '+outdir+'/'+file )
        condor_file.write( '  '+outdir+'/'+file )
        
    if (not count % NUM_JOBS_PER_NODE == 0):
        bsub_file.write( '\n')
        condor_file.write( '\nQueue 1\n')

    chdir( CWD )

    total_count += count

print 'Total number of PDBs to minimize: ', total_count


####################################################
# Create a master script as an "executable" for condor that
# will serially process say, 10 PDBs.
chdir( CWD )
system( 'cp -rf '+HOMEDIR+'/python/charmm_minimize.py .' )
system( 'cp -rf '+HOMEDIR+'/python/run_charmm_minimize.py .' )


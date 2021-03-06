#!/usr/bin/python

from sys import argv,exit
from os import system, getcwd, chdir
from os.path import exists,abspath
from glob import glob


outfiles = argv[1:]

try:
    NUM_JOBS_PER_NODE = int( outfiles[-1] )
    del( outfiles[ -1 ] )
except:
    NUM_JOBS_PER_NODE = 20


####################################################
# Create condor script.
condor_file = open( 'jobTINKER','w' )
condor_file.write('universe     = vanilla\n')
condor_file.write('\n')
condor_file.write('Notify_user  = rhiju@u.washington.edu\n')
condor_file.write('notification = Error\n')
condor_file.write('\n')
condor_file.write('Executable   = ./run_tinker_minimize.py\n')
condor_file.write('\n')
condor_file.write('GetEnv       = True\n')
condor_file.write('\n')

EXE = './run_tinker_minimize.py'

bsub_file = open( 'bsubTINKER','w' )

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

        MINI_EXE = '/work/rhiju/src/mini/bin/rna_extract.linuxgccrelease'
        if not exists( MINI_EXE ):
            MINI_EXE = '~rhiju/src/mini/bin/rna_extract.macosgccrelease'
            if not exists( MINI_EXE ):
                MINI_EXE = '~rhiju/src/mini/bin/rna_extract.linuxgccrelease'

        command = '%s -database ~rhiju/minirosetta_database/ -in::file::silent %s -in::file::silent_struct_type binary_rna' % \
                  ( MINI_EXE, outfile )
        print( command )
        system( command )

        command = 'rm '+outfile # just a soft link anyway
        print( command )
        system( command )

    ####################################################
    # Make subdirectories for each job, and copy in the PDBs, and add line to condor script
    if ( len(glob( 'S*OUT' )) == 0 ) :
        globfiles = glob( 'S_*.pdb' )
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

    globfiles.sort()
    print len( globfiles )
    if outfile.count( '_native' ) and len( globfiles ) > 1000 : globfile = globfiles[:1000]
    if outfile.count( '_ideal' ) and len( globfiles ) > 1000 : globfile = globfiles[:1000]
    if outfile.count( '_nonative' ) and len( globfiles ) > 2000 :   globfiles = globfiles[:2000]

    for file in globfiles:
        minimize_file = file.replace( '/S','/minimize_S')
        rms_file = minimize_file.replace( '.pdb','.rms.txt' )
        if exists( minimize_file ):
            continue

        if ( (count % NUM_JOBS_PER_NODE) == 0):
            if ( start == 1 ):
                condor_file.write( '\nQueue 1\n')
                bsub_file.write( '\n' )
            else:
                start = 1
            condor_file.write( '\narguments = ' )
            bsub_file.write( '\nbsub -W 16:0 %s ' % EXE )
        count += 1
        condor_file.write( '  '+outdir+'/'+file )
        bsub_file.write( '  '+outdir+'/'+file )

    if (not count % NUM_JOBS_PER_NODE == 0):
        condor_file.write( '\nQueue 1\n')
        bsub_file.write( '\n')

    chdir( CWD )

    total_count += count

print 'Total number of PDBs to minimize: ', total_count

condor_file.close()

####################################################
# Create a master script as an "executable" for condor that
# will serially process say, 10 PDBs.
chdir( CWD )
system( 'cp -rf ~rhiju/python/tinker_minimize.py .' )
system( 'cp -rf ~rhiju/python/run_tinker_minimize.py .' )

#TINKER_MINIMIZE_PY = abspath( 'tinker_minimize.py' ).replace('Users','home')
#fid = open( 'run_tinker_minimize.py','w')

#fid.write('#!/usr/bin/python\n')
#fid.write('\n')
#fid.write('from sys import argv\n')
#fid.write('from os import getcwd, chdir, system\n')
#fid.write('from os.path import basename, dirname, exists\n')
#fid.write('\n')
#fid.write('CWD = getcwd()\n')
#fid.write('pdbfiles = argv[1:]\n')
#fid.write('\n')
#fid.write('for file in pdbfiles:\n')
#fid.write('    chdir( dirname( file ) )\n')
#fid.write('\n')
#fid.write('    if exists( \"minimize_\"+basename(file) ):\n')
#fid.write('        chdir( CWD )\n')
#fid.write('        continue\n')
#fid.write('\n')
#fid.write('    command = \" '+TINKER_MINIMIZE_PY+'  \"+ basename( file ) \n')
#fid.write('    print( command )\n')
#fid.write('    system( command )\n')
#fid.write('\n')
#fid.write('    chdir( CWD )\n')
#fid.close()
#
#system( 'chmod 777 run_tinker_minimize.py' )
#
#

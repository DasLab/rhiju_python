#!/usr/bin/python

from sys import argv,exit
from os import system,getcwd
from os.path import basename,dirname,expanduser,exists
import string

def Help():
    print argv[0]+' <text file with rosetta command> <outdir> <# jobs>  [# hours]'
    exit()

if len( argv ) < 4:
    Help()

infile = argv[1]
outdir = argv[2]
try:
    n_jobs = int( argv[3] )
except:
    print 'NEED TO SUPPLY NUMBER OF JOBS'


save_logs = False
if argv.count( '-save_logs' )>0:
    save_logs = True
    pos = argv.index( '-save_logs' )
    del( argv[pos] )

nhours = 16
if len( argv ) > 4:
    nhours = int( argv[4] )
    if ( nhours > 168 ):  Help()

lines = open(infile).readlines()

bsub_file = 'bsubMINI'
condor_file = 'condorMINI'
qsub_file = 'qsubMINI'

fid = open( bsub_file,'w')
fid_condor = open( condor_file,'w')
fid_qsub = open( qsub_file,'w')

tot_jobs = 0

universe = 'vanilla';
fid_condor.write('+TGProject = "TG-MCB090153"\n')
fid_condor.write('universe = %s\n' % universe)
fid_condor.write('notification = never\n')

HOMEDIR = expanduser('~')
CWD = getcwd()

qsub_file_dir = 'qsub_files/'
if not exists( qsub_file_dir ): system( 'mkdir '+qsub_file_dir )

for line in  lines:

    if len(line) == 0: continue
    if line[0] == '#': continue
    #if string.split( line[0]) == []: continue

    dir = outdir + '/$(Process)/'
    command_line = line[:-1].replace( 'out:file:silent  ','out:file:silent ').replace( '-out:file:silent ', '-out:file:silent '+dir)
    command_line = command_line.replace( '-out::file::silent ', '-out::file::silent '+dir)
    command_line = command_line.replace( '-out:file:o ', '-out:file:o '+dir)
    command_line = command_line.replace( '-o ', '-o '+dir)
    command_line = command_line.replace( '-seed_offset 0', '-seed_offset $(Process)')
    command_line = command_line.replace( 'macosgcc', 'linuxgcc')
    command_line = command_line.replace( 'Users', 'home')
    command_line = command_line.replace( '~/', HOMEDIR+'/')
    command_line = command_line.replace( '/home/rhiju',HOMEDIR)

    cols = string.split( command_line )

    if len( cols ) == 0: continue

    if '-total_jobs' in cols:
        pos = cols.index( '-total_jobs' )
        cols[ pos+1 ] = '%d' % n_jobs
        command_line = string.join( cols )
    if '-job_number' in cols:
        pos = cols.index( '-job_number' )
        cols[ pos+1 ] = '$(Process)'
        command_line = string.join( cols )

    if save_logs:
        outfile_general = '$(Process).out'
        errfile_general = '$(Process).err'
    else:
        outfile_general = '/dev/null'
        errfile_general = '/dev/null'

    for i in range( n_jobs ):
        dir_actual = dir.replace( '$(Process)', '%d' % i)
        system( 'mkdir -p '+ dirname(dir_actual) )

        outfile = outfile_general.replace( '$(Process)', '%d' % i )
        errfile = errfile_general.replace( '$(Process)', '%d' % i )

        command =  'bsub -W %d:0 -o %s -e %s ' % (nhours, outfile, errfile )
        command_line_explicit = command_line.replace( '$(Process)', '%d' % i )
        command += command_line_explicit
        fid.write( command + '\n')

        # qsub
        qsub_submit_file = '%s/qsub%d.sh' % (qsub_file_dir, tot_jobs )
        fid_qsub_submit_file = open( qsub_submit_file, 'w' )
        fid_qsub_submit_file.write( '#!/bin/bash\n'  )
        fid_qsub_submit_file.write('#PBS -N %s\n' %  (CWD+'/'+dir_actual[:-1]).replace( '/', '_' ) )
        fid_qsub_submit_file.write('#PBS -o %s\n' % outfile)
        fid_qsub_submit_file.write('#PBS -e %s\n' % errfile)
        fid_qsub_submit_file.write('#PBS -l walltime=48:00:00\n\n')
        fid_qsub_submit_file.write( 'cd %s\n\n' % CWD )
        fid_qsub_submit_file.write( command_line_explicit+' > /dev/null 2> /dev/null \n' )
        fid_qsub_submit_file.close()

        fid_qsub.write( 'qsub %s\n' % qsub_submit_file )

        tot_jobs += 1

    EXE = cols[ 0 ]
    if not exists( EXE ): EXE = EXE.replace( 'linux', 'macos' )
    if not exists( EXE ): EXE = EXE.replace( 'macos', 'linux' )
    if not exists( EXE ):
        EXE = HOMEDIR + '/src/rosetta_TRUNK/rosetta_source/bin/'+EXE
    if not exists( EXE ):
        EXE = HOMEDIR + '/src/mini/bin/'+EXE
        assert( exists( EXE ) )
    arguments = string.join( cols[ 1: ] )


    fid_condor.write('\nexecutable = %s\n' % EXE )
    fid_condor.write('arguments = %s\n' % arguments)
    if save_logs:
        fid_condor.write( 'output = %s\n' % outfile_general )
        fid_condor.write( 'error  = %s\n' % errfile_general )
    fid_condor.write('Queue %d\n' % n_jobs )


fid.close()
fid_condor.close()
fid_qsub.close()

print 'Created bsub submission file ',bsub_file,' with ',tot_jobs, ' jobs queued. To run, type: '
print '>source',bsub_file
print
print 'Created condor submission file ',condor_file,' with ',tot_jobs, ' jobs queued. To run, type: '
print '>condor_submit',condor_file
print
print 'Created qsub submission files ',qsub_file,' with ',tot_jobs, ' jobs queued. To run, type: '
print '>source ',qsub_file

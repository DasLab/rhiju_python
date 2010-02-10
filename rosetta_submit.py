#!/usr/bin/python

from sys import argv,exit
from os import system
from os.path import basename,dirname,expanduser
import string

if len( argv ) < 4:
    print argv[0]+' <text file with rosetta command> <outdir> <# jobs>'
    exit()

infile = argv[1]
outdir = argv[2]
try:
    n_jobs = int( argv[3] )
except:
    print 'NEED TO SUPPLY NUMBER OF JOBS'


lines = open(infile).readlines()

bsub_file = 'bsubMINI'
condor_file = 'condorMINI'
fid = open( bsub_file,'w')
fid_condor = open( condor_file,'w')

tot_jobs = 0

universe = 'vanilla';
fid_condor.write('+TGProject = TG-MCB090153\n')
fid_condor.write('universe = %s\n' % universe)

HOMEDIR = expanduser('~')

for line in  lines:

    if len(line) == 0: continue
    if line[0] == '#': continue
    if string.split( line[0]) == []: continue

    dir = outdir + '/$(Process)/'
    command_line = line[:-1].replace( '-out:file:silent ', '-out:file:silent '+dir)
    command_line = command_line.replace( '-out::file::silent ', '-out::file::silent '+dir)
    command_line = command_line.replace( 'macosgcc', 'linuxgcc')
    command_line = command_line.replace( 'Users', 'home')

    command_line = command_line.replace( '/home/rhiju',HOMEDIR)

    cols = string.split( command_line )
    if '-total_jobs' in cols:
        pos = cols.index( '-total_jobs' )
        cols[ pos+1 ] = '%d' % n_jobs
        command_line = string.join( cols )
    if '-job_number' in cols:
        pos = cols.index( '-job_number' )
        cols[ pos+1 ] = '$(Process)'
        command_line = string.join( cols )

    for i in range( n_jobs ):
        dir_actual = dir.replace( '$(Process)', '%d' % i)
        system( 'mkdir -p '+ dirname(dir_actual) )

        command =  'bsub -W 16:0 -o /dev/null -e /dev/null ' + command_line.replace( '$(Process)', '%d' % i )
        fid.write( command + '\n')

        tot_jobs += 1

    EXE = cols[ 0 ]
    arguments = string.join( cols[ 1: ] )
    fid_condor.write('\nexecutable = %s\n' % EXE )
    fid_condor.write('arguments = %s\n' % arguments)
    fid_condor.write('Queue %d' % n_jobs )

fid.close()
fid_condor.close()

print 'Created bsub submission file ',bsub_file,' with ',tot_jobs, ' jobs queued. To run, type: '
print '>source',bsub_file
print
print 'Created condor submission file ',condor_file,' with ',tot_jobs, ' jobs queued. To run, type: '
print '>condor_submit',condor_file
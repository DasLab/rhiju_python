#!/usr/bin/python

from sys import argv,exit
import string
from os import system,popen
from os.path import basename,exists
from random import randrange
from time import sleep

from dagman_LSF import *
#from dagman_condor import *


#########################################
# Parse dagman file
#########################################
dagman_file = argv[1]
lines = open( dagman_file ).readlines()

jobs = []
condor_submit_file = {}
post_script = {}
pre_script = {}
parents = {}
for line in lines:
    if len( line ) > 4 and line[:3] == "JOB":
        cols = string.split( line )
        job = cols[1]
        jobs.append( job )
        condor_submit_file[ job ] = cols[2]
    elif len( line ) > 6 and line[:6] == "SCRIPT":
        cols = string.split( line )
        job = cols[2]
        if cols[1] == "PRE":
            pre_script[ job ] = string.join( cols[3:] )
        else:
            assert( cols[1] == "POST" )
            post_script[ job ] = string.join( cols[3:] )
    elif len( line ) > 7 and line[:6] == "PARENT":
        cols = string.split( line )
        assert( cols.count( "CHILD" ) )
        child_index = cols.index( "CHILD" )
        parent_jobs =  cols[1:child_index]
        child_jobs =  cols[child_index:]
        for child_job in child_jobs:
            if child_job not in parents.keys():
                parents[ child_job ] = []
            for parent_job in parent_jobs: parents[ child_job ].append( parent_job )

done = {}
queued = {}
for job in jobs:
    done[ job ] = 0
    queued[ job ] = 0

#job_tags = {}
output_files = {}
all_done = 0

while not all_done:

    ###################################################
    # Find jobs that are ready to go but not done.
    ###################################################
    all_done = 1
    for job in jobs:
        if not done[ job ]:
            all_done = 0

            if not queued[ job ]:
                #Consider queuing the job

                ready_to_queue = 1
                if job in parents.keys():
                    for parent_job in parents[job]:
                        if not done[ parent_job ]:
                            ready_to_queue = 0
                            break

                if ready_to_queue:
                    if job in pre_script.keys():
                        pre_command = pre_script[ job ]
                        pre_command_log_file = condor_submit_file[job] +'.pre_script.log'
                        if not exists( pre_command_log_file  ):
                            command =  pre_command + ' > '+pre_command_log_file
                            system( command )

                    ( output_files[ job ], actually_queued ) = condor_submit( condor_submit_file[ job ] )

                    queued[ job ] = actually_queued
                    if not actually_queued:
                        done[ job ] = 1

    if not all_done:
        sleep(1)

    ###################################################
    # Check for any jobs that are done
    ###################################################

    for job in jobs:
        if not done[ job ] and queued[ job ]:
            still_running = check_output_files( output_files[ job ] )
            print "Jobs still running: ",output_files[job][-1],still_running

            if not still_running:
                if job in post_script.keys():
                    command = post_script[ job ]
                    print( command )
                    system( command )
                done[ job ] = 1
                queued[ job ] = 0



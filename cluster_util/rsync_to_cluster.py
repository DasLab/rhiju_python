#!/usr/bin/python

from sys import argv,exit
import string
from os import system
from os.path import basename,dirname,abspath,exists
from cluster_info import *

def Help():
    print
    print argv[0]+' <cluster> [<name of files to sync>]'
    print
    exit()

if len(argv)<2:
    Help()

cluster_in = argv[1]
(cluster,remotedir) = cluster_check( cluster_in )

if cluster == 'unknown':
    Help()

args = argv[2:]
dir = ''
extra_args = []
for m in args:
    if len( m ) > 2 and m.find( '--' ) > -1:
        extra_args.append( m )
    else:
        dir += ' '+m

print 'DIR', dir

if len(dir) == 0: dir = '.'

clusterdir = abspath('.').replace('/Users/rhiju/','')
clusterdir = clusterdir.replace('/work/rhiju/','')
clusterdir = clusterdir.replace('/scratch/users/rhiju/','')

clusterdir = remotedir + clusterdir

#if cluster[:3]=='syd':
#    n = cluster[3]
#    cluster = 'syd'
#    clusterdir = 'work'+n+'/'+clusterdir

command = 'ssh ' + cluster + ' mkdir -p '+clusterdir
print(command)
system(command)

cluster_prefix = cluster+':'
if len(cluster) == 0: cluster_prefix = ''

command = 'rsync -avzL '+dir+' '+cluster_prefix+clusterdir+' '+string.join(extra_args)
print(command)
system(command)


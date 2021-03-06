#!/usr/bin/python

#
# Rhiju's first python script.
# Just go through and apply Phil's clustering program to
# all these outfiles generated by Rowan -- what are the
# top five clusters?
#
# August 29, 2005
#

from os.path import exists
from math import floor,log10,log,exp
from operator import add
from os import chdir,system,popen,getcwd
from sys import stderr,argv,exit
import sys
from whrandom import random
from math import sqrt
import re
import string

filelist=sys.argv[1]

filein = open(filelist,'r')

lines = filein.readlines()

for line in lines :
     cols = string.split( line,'.' )
     fileprefix = cols[0]



#Need coordinates of native for Phil's clustering program
     sup_exe = '~pbradley/python/make_coords_file.py'
     pathtopdb = '../xfer/recon/'
     outprefix = 'cluster/'

     #Make a directory to do this crap in
     makedir_cmd = 'mkdir %s%s/' % (outprefix,fileprefix)
     system(makedir_cmd)

     # A little bit of a hack... I didn't have a good pdb file for co1pm4,
     # So I always look at the sj one.
     makecoords_cmd = '%s %ssj%s%s %s%s %s%s/%s.coords'% ( sup_exe,pathtopdb,
                               fileprefix[-4:],'.sup.pdb _ ',
                               fileprefix,'.out > ',outprefix,fileprefix,fileprefix)

     print makecoords_cmd
     system(makecoords_cmd)

# Run Phil's clustering program. Top cluster should have at least
#  25 members, at most 100 members, and ideally 75.
# Minimum cluster size is 5. No a priori info on RMSD.
#
     cluster_exe = '~pbradley/C/cluster_info_silent.out'

     cluster_cmd = '%s %s%s %s%s/%s%s %s%s/%s 5,10,25,40 0,10' % (cluster_exe,
             fileprefix,'.out', outprefix,fileprefix,fileprefix,'.coords',
             outprefix,fileprefix,fileprefix)

     print cluster_cmd
     system(cluster_cmd)     


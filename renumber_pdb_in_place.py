#!/usr/bin/python

import string
from sys import argv,stderr,stdout
from os import popen,system
from os.path import exists
from amino_acids import longer_names
from parse_options import parse_options

retain_atom_num = parse_options( argv, "retain_atom_num", 0 )

assert( len(argv)>1)

# Look for integers... perhaps we are specifying particular residue numbers
pdbnames = []
new_numbers = []
for i in range(1, len( argv ) ):
	try:
		new_numbers.append( int( argv[i] ) )
	except:
		pdbnames.append( argv[i] )

for pdbname in pdbnames:
	lines = open(pdbname,'r').readlines()

	oldresnum = '   '
	count = 0;

	outid  = open( 'temp.txt','w')

	atomnum  = 0
	for line in lines:
		line_edit = line
		if line[0:3] == 'TER':
		    continue

		if line_edit[0:4] == 'ATOM' or line_edit[0:6] == 'HETATM':

		    if not (line[16]==' ' or line[16]=='A'): continue

		    atomnum += 1

		    resnum = line_edit[23:26]
		    if not resnum == oldresnum:
			count = count + 1
		    oldresnum = resnum

		    if ( count <= len( new_numbers ) ):
			    newnum = '%4d' % new_numbers[ count-1 ]
		    else:
			    newnum = '%4d' % count

		    if retain_atom_num:
			    line_edit = '%s%s%s' % (line_edit[0:22], newnum, line_edit[26:] )
		    else:
			    line_edit = '%s%5d%s%s%s' % (line_edit[0:6],atomnum,line[11:22], newnum, line_edit[26:] )

		    outid.write(line_edit)

	outid.close()

	system( 'mv temp.txt '+pdbname )

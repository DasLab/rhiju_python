#!/usr/bin/python

from parse_options import parse_options
from sys import argv
import string

dist_cutoff = parse_options( argv, 'dist_cutoff', 6.5 )
dist_fade   = parse_options( argv, 'dist_fade', 2.0 )
penalty     = parse_options( argv, 'penalty', 2.0 )
allow_hairpin = parse_options( argv, 'allow_hairpin', [-1] )

assert( len( argv ) == 2 )

strand_def_file = argv[1]

# Read in strand definitions.
strands = []
lines = open( strand_def_file ).readlines()
for line in lines:
    cols = string.split( line )
    strands.append( (int(cols[ 0 ]), int( cols[1] ) ) )

#print strands

ok_hairpins = []
for n in range( len(allow_hairpin)/2 ):
    ok_hairpins.append( allow_hairpin[2*n : 2*n+2] )

numstrands = len( strands )

print '[ atompairs ]'

###################
# Kill self-strands
###################
for n in range( numstrands  ):

    for i in range( strands[n][0], strands[n][1]+1 ):
        for j in range( strands[n][0], strands[n][1]+1 ):
            if ( i >= j ): continue
            print '%s %d %s %d   FADE %8.3f %8.3f %8.3f %8.3f' % \
                ( 'CA',i,'CA',j, -1 * dist_cutoff, dist_cutoff, dist_fade, penalty )



###################
# Kill hairpins.
###################
for n in range( numstrands  - 1 ):

    allow_it = 0
    for hairpin in ok_hairpins:
        if ( n+1 == hairpin[0] and n+2 == hairpin[1] ): allow_it = 1
        if ( n+2 == hairpin[0] and n+1 == hairpin[1] ): allow_it = 1
    if allow_it: continue


    for i in range( strands[n][0], strands[n][1]+1 ):
        for j in range( strands[n+1][0], strands[n+1][1]+1 ):

            print '%s %d %s %d   FADE %8.3f %8.3f %8.3f %8.3f' % \
                ( 'CA',i,'CA',j, -1 * dist_cutoff, dist_cutoff, dist_fade, penalty )

###################
# Kill paperclips
###################
for n in range( numstrands  - 2 ):
    for i in range( strands[n][0], strands[n][1]+1 ):
        for j in range( strands[n+2][0], strands[n+2][1]+1 ):
            print '%s %d %s %d   FADE %8.3f %8.3f %8.3f %8.3f' % \
                ( 'CA',i,'CA',j, -1 * dist_cutoff, dist_cutoff, dist_fade, penalty )



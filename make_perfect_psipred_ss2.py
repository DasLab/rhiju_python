#!/usr/bin/python

import string
import sys
from os import popen,system
import pdb
from blast import NBAlign

if len(sys.argv) != 4:
    print '\n'+'-'*75
    print 'Usage: %s <pdb> <chain> <silent_file> > <coords_file>'
    print '-'*75+'\n\n'
    assert 0==1

pdb_file = sys.argv[1]
chain = sys.argv[2]
silent_file = sys.argv[3]

if chain == '_' or chain == '-':
    chain = ' '


lines = popen('~rhiju/dssp '+pdb_file+' | grep "RESIDUE AA" -A10000 | '+\
              ' grep "^.[ 0-9][ 0-9][ 0-9][ 0-9]......'+\
              chain+'"').readlines()

#print string.join(lines,'')

lowercase = list('abcdefghijklmnopqrstuvwxyz')

seq = map(lambda x:x[13],lines)

for i in range(len(seq)):
    if seq[i] in lowercase:
        seq[i] = 'C'
seq = string.join(seq,'')

ss = string.join(map(lambda x:x[16],lines),'')

ss3 = ''
for a in ss:
    if a not in [' ','E','B','H','G','I','S','T']:
        sys.stderr.write('undefined ss character? '+a+'\n')
        ss3 = ss3+'L'
    elif a in ['E','B']:
        ss3 = ss3+'E'
    elif a in ['H','G']:
        ss3 = ss3+'H'
    else:
        ss3 = ss3+'L'

assert len(ss3) == len(seq)

if silent_file == '-':
    silent_seq = seq
else:
    line = open(silent_file,'r').readline()
    if line[0] == ">": ## fasta file
        silent_seq = string.join(map(lambda x:string.split(x)[0],
                                     open(silent_file,'r').readlines()[1:]),'')
    elif string.split(line)[0] == 'SEQUENCE:':
        silent_seq = string.split(line)[1]
    else:
        print 'bad silent file type'
        sys.exit()

#al = NBAlign(silent_seq,seq)
#TEMPORARY HACK!!
al = NBAlign(seq,seq)

sys.stderr.write('found dssp secondary structure for %d percent of sequence\n' \
                 %( (len(al.keys())*100)/len(silent_seq)))

coords = pdb.Get_full_coords(pdb_file,silent_seq,chain,0,0)
ca = {}
for pos in coords.keys():
    for a in coords[pos].keys():
        if string.split(a)[0] == 'CA':
            ca[pos] = coords[pos][a]
            break

sys.stderr.write('found coordinates for %d percent of sequence\n' \
                 %( (len(ca.keys())*100)/len(silent_seq)))


print "# PSIPRED VFORMAT (PSIPRED V2.5 by David Jones)"
print
for i in range(len(silent_seq)):
    sschar = "C"
    ssprob = [1.00, 0.00, 0.00]

    if i in al.keys():
        if ss3[al[i]] == "H":
            sschar = "H"
            ssprob = [0.00, 1.00, 0.00]
        elif ss3[al[i]] == "E":
            sschar = "E"
            ssprob = [0.00, 0.00, 1.00]

    print "%4d %s %s   %5.3f  %5.3f  %5.3f" % ( i+1, silent_seq[i], sschar, ssprob[0],ssprob[1],ssprob[2])

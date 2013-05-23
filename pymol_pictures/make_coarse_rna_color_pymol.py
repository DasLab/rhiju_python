#!/usr/bin/python

from sys import argv,stdout
from os import system,popen

inputfiles = argv[1:]


pdbfiles = []
highlight_residues = []
for i in range( len(inputfiles) ):
    inputfile = inputfiles[i]
    try:
        highlight_residues.append( int( inputfile) )
    except:
        if (not inputfile.find("superposition") > 0):
            pdbfiles.append( inputfile)

#pdbfiles.reverse()
#superimpose first!

prefix = pdbfiles[0].replace('.pdb','')

if len(pdbfiles) > 1:
    command = "python ~rhiju/python/superimpose.py "
    for pdbfile in pdbfiles: command += " "+pdbfile


    command += " -R 20.0 > "+ prefix+"_superposition.pdb"
#    command += " > "+ prefix+"_superposition.pdb"

    print( command )
    system(command)

#Extract models
    command = "python ~rhiju/python/parse_NMR_models.py "+prefix+"_superposition.pdb"
    system(command)
else:
    command = "cp "+pdbfiles[0]+" "+prefix+"_superposition_001.pdb"
    system(command)

fid = open( 'TEST.pml','w')
#fid = stdout


fid.write('reinitialize\n')
count = 0
for pdbfile in pdbfiles:
    count += 1
    fid.write('load %s_superposition_%03d.pdb,model%d\n' %
              (prefix,count, count))


fid.write('\n')
fid.write('hide everything,all\n')
fid.write('show lines,all\n')
fid.write('\n')
fid.write('select a, resn rA\n')
fid.write('select c, resn rC\n')
fid.write('select g, resn rG\n')
fid.write('select u, resn rU\n')
fid.write('\n')
fid.write('select bases, name CEN+X+Y\n')
fid.write('select backbone, name S+P+OVL1+OVL2+OVU1\n')
#fid.write('select backbone, name c4*')
fid.write('select sugar, name S\n')
fid.write('\n')

#fid.write('set line_width=3.0\n')
#fid.write('show lines, bases\n')

fid.write('color lightblue,g\n')
fid.write('color palegreen,c\n')
fid.write('color lightorange,a\n')
fid.write('color salmon,u\n')
fid.write('\n')
fid.write('select highlight, resi ')

#for res in highlight_residues: fid.write('%d+' % res)
fid.write('1-1000')
fid.write('\n')

fid.write('select asel, resn rA and highlight and bases\n')
fid.write('select csel, resn rC and highlight and bases\n')
fid.write('select gsel, resn rG and highlight and bases\n')
fid.write('select usel, resn rU and highlight and bases\n')

fid.write('color blue,gsel\n')
fid.write('color green,csel\n')
fid.write('color orange,asel\n')
fid.write('color red,usel\n')
fid.write('show sticks, backbone\n')
fid.write('\n')
fid.write('set stick_radius=1.0\n')
#fid.write('show cartoon, backbone\n')
#fid.write('cartoon rect, backbone\n')
fid.write('bg_color white\n')
fid.write('\n')

count = 0
for pdbfile in pdbfiles:
    count += 1
    fid.write('select model%d_backbone, model%d and backbone\n' % (count,count))
    fid.write('cmd.spectrum(selection = "model%d_backbone")\n' % count)

fid.write('\n')
fid.close()


######################################
#Output graphics
fid = open( 'TEST2.pml','w')

count = 0
for pdbfile in pdbfiles:
    count += 1
    fid.write('disable all\n')
    fid.write('enable model%d\n' % count)
    fid.write('ray 800,800\n')
#    fid.write('ray 1200,1200\n')
    fid.write('save '+pdbfile+'.png\n')

fid.close()


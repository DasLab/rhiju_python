#!/usr/bin/python

import sys
import string

if len( sys.argv ) < 1:
    print sys.argv[0] + " <infile> <column> <binwidth> <minval> <maxval> "
    exit( 0 )

infile = sys.argv[1]
thecolumn =int( sys.argv[2] )

lines = open(infile).readlines()
thedata = []
for line in lines:
    try:
        cols = string.split(line)
        thedata.append( float(cols[thecolumn-1]))
    except:
        continue

FIGURE_OUT_BINWIDTH = 0
try:
    binwidth = float(sys.argv[3])
    del( sys.argv[3] )
except:
    FIGURE_OUT_BINWIDTH = 1

try:
    mindata = float( sys.argv[3] )
    maxdata = float( sys.argv[4] )
except:
    mindata = min(thedata)
    maxdata = max(thedata)

if FIGURE_OUT_BINWIDTH:
    binwidth = (maxdata - mindata) / 50.0;


histogram = []
bincenter = []
currentbincenter = mindata + binwidth/2.0;

numbins =  int((maxdata-mindata)/binwidth)
print numbins
if (numbins == 0): numbins = 1
for bin in range(numbins):
    histogram.append( 0.0 )
    bincenter.append( currentbincenter )
    currentbincenter += binwidth

total = 0
for datum in thedata:
    bin = int( (datum - mindata)/binwidth )
    if bin<-1 or bin>numbins: continue
    if bin<0       : bin = 0
    if bin>=numbins: bin = numbins - 1
    histogram[bin] += 1
    total += 1

for bin in range(numbins):
    print bincenter[bin], histogram[bin]/total

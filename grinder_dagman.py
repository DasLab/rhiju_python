#!/usr/bin/python

from os import system,popen
from os.path import exists,dirname,basename,expanduser
from sys import exit, argv
from glob import glob
import string
from time import sleep
from parse_options import parse_options
from get_sequence import get_sequence

fasta_file = parse_options( argv, "fasta", "1shf.fasta" )
assert( exists( fasta_file ) )
sequence_lines = open( fasta_file  ).readlines()[1:]
sequence = string.join(  map( lambda x : x[:-1], sequence_lines) ,  '' )
NRES = len( sequence )

MIN_RES = parse_options( argv, "min_res", 1 )
MAX_RES = parse_options( argv, "max_res", NRES )
ZIGZAG = parse_options( argv, "zigzag", 0 )
N_SAMPLE = parse_options( argv, "n_sample", 18 )
FINAL_NUMBER = parse_options( argv, "final_number", 100 )
SCORE_WEIGHTS = parse_options( argv, "weights", "score12_no_hb_env_dep.wts" )
PACK_WEIGHTS = parse_options( argv, "pack_weights", "pack_no_hb_env_dep.wts" )
NSTRUCT = parse_options( argv, "nstruct", 100 )
FILTER_RMSD = parse_options( argv, "filter_rmsd", -1.0 )
CLUSTER_RADIUS = parse_options( argv, "cluster_radius", 0.25 )
CLUSTER_RADIUS_SAMPLE = parse_options( argv, "cluster_radius_sample", 0.1 )
AUTO_TUNE = parse_options( argv, "auto_tune", 0 )
filter_native_big_bins = parse_options( argv, "filter_native_big_bins", 0 )
score_diff_cut = parse_options( argv, "score_diff_cut", 10.0 )
max_res_to_add_denovo = parse_options( argv, "denovo", 0 )
USE_MINI_TEMP = parse_options( argv, "use_mini_TEMP", 0 )

native_pdb = parse_options( argv, "native", "" )
template_pdbs = parse_options( argv, "s", [""] )
cst_file = parse_options( argv, "cst_file", "" )
pathway_file = parse_options( argv, "pathway_file", "" )
cluster_by_all_atom_rmsd = parse_options( argv, "cluster_by_all_atom_rmsd", 0 )
add_peptide_plane = parse_options( argv, "add_peptide_plane", 0 ) #Now defunct!
no_peptide_plane = parse_options( argv, "no_peptide_plane", 0 )
BUILD_BOTH_TERMINI = parse_options( argv, "build_both_termini", 0 )
MAX_ADDED_SEGMENT = parse_options( argv, "max_added_segment", 16 )
min_length = parse_options( argv, "min_length", 2 )
max_length = parse_options( argv, "max_length", 0 )
superimpose_res = parse_options( argv, "superimpose_res", [ -1 ] )
virtual_res = parse_options( argv, "virtual_res", [ -1 ] )
align_pdb = parse_options( argv, "align_pdb", "" )
template_mapping_files = parse_options( argv, "mapping", [""] )
frag_files = parse_options( argv, "frag_files", [""] )
frag_lengths = parse_options( argv, "frag_lengths", [ -1 ] )
MAX_FRAGMENT_OVERLAP = parse_options( argv, "max_fragment_overlap", 2 )
swa_frag_lengths = parse_options( argv, "swa_frag_lengths", [-1] )
swa_silent_file_dir = parse_options( argv, "swa_silent_file_dir", "" )
loop_res = parse_options( argv, "loop_res", [-1] )
fixed_res = parse_options( argv, "fixed_res", [-1] )
no_fixed_res = parse_options( argv, "no_fixed_res", 0 )
calc_rms_res = parse_options( argv, "calc_rms_res", [-1] )
loop_start_pdb = parse_options( argv, "loop_start_pdb", "" )
loop_force_Nsquared = parse_options( argv, "loop_force_Nsquared", 0 )


if ( len( argv ) > 1 ): # Should remain with just the first element, the name of this script.
    print " Unrecognized flags?"
    print "   ",string.join(argv[1:] )
    exit( 0 )

DENOVO = ( max_res_to_add_denovo > 0 )
TEMPLATE = len( template_pdbs ) > 0
FRAGMENT_LIBRARY = len( frag_files ) > 0
SWA_FRAGS = len( swa_frag_lengths ) > 0
LOOP = len( loop_res ) > 0

for template_pdb in template_pdbs: assert( exists( template_pdb ) )
for frag_file in frag_files: assert( exists( frag_file ) )
if add_peptide_plane:
    print " -add_peptide_plane defunct -- its on by default! "
    print " If you want to disable peptide_plane, use no_peptide_plane."
    exit( 0 )
add_peptide_plane = not no_peptide_plane
if FRAGMENT_LIBRARY: assert( add_peptide_plane )   # Should peptide plane also be required for template runs?

###############################################################
# Where's the executable?
###############################################################
HOMEDIR = expanduser('~rhiju')

MINI = "mini"
if USE_MINI_TEMP: MINI = "mini_TEMP"
EXE = HOMEDIR+'/src/'+MINI+'/bin/stepwise_protein_test.macosgccrelease'
if not( exists( EXE )):
    EXE = HOMEDIR+'/src/'+MINI+'/bin/stepwise_protein_test.linuxgccrelease'
assert( exists( EXE ) )

DB = HOMEDIR+'/minirosetta_database'
assert( exists( DB ) )

PYDIR = HOMEDIR+'/python'
assert( exists( PYDIR ) )

PRE_PROCESS_SETUP_SCRIPT = PYDIR+"/stepwise_pre_process_setup_dirs.py"
assert( exists( PRE_PROCESS_SETUP_SCRIPT ) )

POST_PROCESS_FILTER_SCRIPT = PYDIR+"/stepwise_post_process_combine_and_filter_outfiles.py"
assert( exists( POST_PROCESS_FILTER_SCRIPT ) )

POST_PROCESS_CLUSTER_SCRIPT = PYDIR+"/stepwise_post_process_cluster.py"
assert( exists( POST_PROCESS_CLUSTER_SCRIPT ) )

assert( exists( SCORE_WEIGHTS ) or exists( DB + "/scoring/weights/"+SCORE_WEIGHTS) )
assert( exists( PACK_WEIGHTS ) or exists( DB + "/scoring/weights/"+PACK_WEIGHTS) )

fid_dag = open( "protein_build.dag", 'w' )
fid_dag.write("DOT dag.dot\n")

if not exists( 'CONDOR/' ):
    system( 'mkdir -p CONDOR' )


#########################################################
# list of jobs...
all_job_tags = []
real_compute_job_tags = []
jobs_done = []

#########################################################
# Some useful functions (move somewhere else?)
#########################################################
def make_condor_submit_file( condor_submit_file, arguments, queue_number, universe="vanilla" ):

    fid = open( condor_submit_file, 'w' )
    fid.write('+TGProject = TG-MCB090153\n')
    fid.write('universe = %s\n' % universe)
    fid.write('executable = %s\n' % EXE )
    fid.write('arguments = %s\n' % arguments)

    sub_job_tag = basename( condor_submit_file ).replace('.condor','')
    job_dir = dirname( condor_submit_file )
    sub_job_dir = job_dir + '/' + sub_job_tag

    assert( exists( job_dir ) )
    if not exists( sub_job_dir ): system( 'mkdir -p '+sub_job_dir )

    fid.write('output = %s/$(Process).out\n' % sub_job_dir )
    fid.write('log = %s/%s.log\n' % ( job_dir,sub_job_tag) )
    fid.write('error = %s/$(Process).err\n' % sub_job_dir )
    fid.write('notification = never\n')
    fid.write('Queue %d\n' % queue_number )
    fid.close()

def setup_dirs_and_condor_file_and_tags( overall_job_tag, sub_job_tag, prev_job_tags, args2, decoy_tag,\
                                         fid_dag, job_tags, all_job_tags, jobs_done, real_compute_job_tags, combine_files):
    newdir = overall_job_tag+'/'+sub_job_tag
    if len( decoy_tag ) > 0:
        newdir += '_' + decoy_tag
    outfile = newdir + '/' + overall_job_tag.lower() + '_sample.out'

    args2 += ' -out:file:silent %s ' % outfile

    condor_file_dir =  "CONDOR/%s/" % overall_job_tag
    if not exists( condor_file_dir ): system( 'mkdir -p '+condor_file_dir )
    condor_submit_file = '%s/%s.condor' %  (condor_file_dir,sub_job_tag)

    job_tag = overall_job_tag+"_"+sub_job_tag
    fid_dag.write('\nJOB %s %s\n' % (job_tag, condor_submit_file) )

    if not exists( condor_submit_file ):
        make_condor_submit_file( condor_submit_file, args2, 1 )

    if (len( prev_job_tags ) > 0):
        for prev_job_tag in prev_job_tags:
            assert( prev_job_tag in all_job_tags )
            #Note previous job may have been accomplished in a prior run -- not in the current DAG.
            if (prev_job_tag not in jobs_done):
                fid_dag.write('PARENT %s  CHILD %s\n' % (prev_job_tag, job_tag) )

    # The pre process script finds out how many jobs there actually are...
    if len( decoy_tag ) > 0:
        assert( len( prev_job_tags ) > 0 )
        fid_dag.write('SCRIPT PRE %s   %s %s %s %s %s\n' % (job_tag, PRE_PROCESS_SETUP_SCRIPT,overall_job_tag,prev_job_tags[0],condor_submit_file,sub_job_tag) )
    else:
        if not exists( newdir ): system( 'mkdir -p '+newdir )

    fid_dag.write('SCRIPT POST %s %s %s/%s\n' % (job_tag, POST_PROCESS_FILTER_SCRIPT,overall_job_tag,sub_job_tag ) )

    # In python, lists are passed by reference... these should get updated for the outside world.
    job_tags.append( job_tag )
    real_compute_job_tags.append( job_tag )
    combine_files.append( '%s/%s_sample.low4000.out' % ( overall_job_tag, sub_job_tag.lower() ) )


#####################################################
# Pathway setup
#####################################################
follow_path = 0
if len(pathway_file) > 0:
    follow_path = 1
    lines = open( pathway_file ).readlines()
    pathway_regions = []

    for line in lines:
        # don't yet know how to handle "merges" (i.e., inter-domain docking)
        if len( line ) > 5  and line[:5] == 'MERGE': break
        assert( line[:4] == 'PATH' )

        cols = map( lambda x:int(x), string.split( line )[1:] )
        i = cols[0]
        j = cols[0]
        cols = cols[1:]
        for m in cols:
            if ( m == i-1 ):
                i = m
            else:
                assert( m == j+1 )
                j = m
            pathway_regions.append( [i, j] )

#####################################################
# Template mapping files
#####################################################
if len( template_pdbs ) > 0:
    template_mappings = {}
    if len( template_mapping_files ) == 0:
        # Asssume that sequences correspond perfectly.
        template_mapping = {}
        for m in range( 1, NRES+1 ): template_mapping[ m ] = m
        for n in range( len( template_pdbs) ):
            template_mappings[ template_pdbs[n] ] =  template_mapping
    else:
        assert( len( template_mapping_files ) == len( template_pdbs ) )
        for n in range( len( template_pdbs ) ):
            lines = open( template_mapping_files[n] ).readlines()
            # First line better be our target sequence
            mapping_seq1 = lines[0][:-1]
            #print mapping_seq1.replace('-','')
            #print sequence
            assert(  mapping_seq1.replace('-','') == sequence )

            # Second line better be our template sequence
            template_sequence = popen( "python "+PYDIR+"/pdb2fasta.py "+template_pdbs[n] ).readlines()[1][:-1]
            mapping_seq2 = lines[1][:-1]
            #print mapping_seq2.replace('-','')
            #print sequence
            assert( mapping_seq2.replace('-','') == template_sequence )
            assert( len( mapping_seq1 ) == len( mapping_seq2 ) )

            count1 = 0
            count2 = 0
            template_mapping = {}
            for i in range( len( mapping_seq1 ) ):
                seq1_OK = ( not mapping_seq1[i]  == '-' )
                seq2_OK = ( not mapping_seq2[i]  == '-' )
                if seq1_OK: count1 += 1
                if seq2_OK: count2 += 1
                if seq1_OK and seq2_OK: template_mapping[ count1 ] = count2
            template_mappings[ template_pdbs[n] ] = template_mapping

def template_continuous( i, j, template_mapping ):
    for k in range( i, j+1 ):
        if not ( k in template_mapping.keys() ): return 0
        if ( k > i ) and ( not template_mapping[k] == template_mapping[k-1]+1 ): return 0
    return 1

##########################
# Fragments
##########################

if len( frag_lengths ) == 0:
    for frag_file in frag_files:
        pos = frag_file.find("_05.200_v1_3" )
        assert( pos > 0 )
        frag_length = int( frag_file[pos-2 : pos] )
        frag_lengths.append( frag_length )
assert( len( frag_lengths ) == len( frag_files ) )


def check_frag_overlap( i, j, i_prev, j_prev, frag_length ):

    input_res1 =  wrap_range( i_prev, j_prev+1 )

    if ( i == i_prev ):
        assert( not j == j_prev )
        num_extra_residues = j - j_prev
        startpos = j - frag_length + 1
    elif ( j == j_prev ):
        num_extra_residues = i_prev - i
        startpos = i
    else:
        # Some craziness
        return (0,0,0)

    num_overlap_residues = frag_length - num_extra_residues

    endpos = startpos + frag_length - 1

    return ( startpos, endpos, num_overlap_residues )

####################################################################
# input silent files from some other directory (e.g., SWA frags)
####################################################################
if SWA_FRAGS:
    glob_files = glob( swa_silent_file_dir+"/region*sample.cluster.out" )
    silent_files_in = map( lambda x: basename(x),  glob_files )

#####################################
# Setup for loop building jobs
#####################################
def wrap_range( i, j, total_residues = NRES ):
    # Kind of like range(i,j).
    # But if i > j-1, gives residues not in j ... i-1.
    # Useful for loop stuff
    if ( i < j ):
        return range(i,j)
    else:
        x = range(1,j)
        for m in range( i, total_residues+1 ): x.append( m )
        return x

min_loop_gap = 4
if LOOP:
    loop_res.sort()
    assert( len( loop_res ) >= min_loop_gap)
    for m in range( len(loop_res)-1): assert( loop_res[m]+1 == loop_res[m+1] )

    assert( len(loop_start_pdb) > 0 )
    assert( exists( loop_start_pdb ) )

    assumed_start_sequence = ''
    loop_start = loop_res[ 0 ]
    loop_end = loop_res[ -1 ]
    for m in wrap_range( loop_end+1, loop_start, NRES ):
        assumed_start_sequence += sequence[m-1]

    actual_start_sequence = get_sequence( loop_start_pdb )
    assert( assumed_start_sequence == actual_start_sequence )

    if len( superimpose_res ) == 0:
        superimpose_res = wrap_range( loop_end+1, loop_start, NRES )
    if len( fixed_res ) == 0 and not no_fixed_res:
        fixed_res = wrap_range( loop_end+1, loop_start, NRES )
    if len( calc_rms_res ) == 0:
        calc_rms_res = range( loop_start, loop_end+1 )

##########################
# BASIC COMMAND
##########################

args = ' -database %s  -rebuild -out:file:silent_struct_type binary  -fasta %s -n_sample %d -nstruct %d -cluster:radius %8.3f' % ( DB, fasta_file, N_SAMPLE, NSTRUCT, CLUSTER_RADIUS_SAMPLE )

args += ' -extrachi_cutoff 0 -ex1 -ex2' # These may be redundant actually.

args += ' -score:weights %s -pack_weights %s' % (SCORE_WEIGHTS, PACK_WEIGHTS )

if ( FILTER_RMSD > 0.0 ):
    args += ' -filter_rmsd %8.3f' % FILTER_RMSD

if add_peptide_plane: args += ' -add_peptide_plane'
if filter_native_big_bins:  args+= ' -filter_native_big_bins' # this is defunct now, I think

if len( cst_file ) > 0:
    assert( exists( cst_file ) )
    args += ' -cst_file %s' % cst_file
if len( align_pdb ) > 0:
    assert( exists( align_pdb ) )
    args += ' -align_pdb %s' % align_pdb
if len( native_pdb ) > 0:
    assert( exists( native_pdb ) )
    args += ' -native %s' % native_pdb
if len( superimpose_res ) > 0:
    args += ' -superimpose_res '
    for k in superimpose_res: args += '%d ' % k
if len( virtual_res ) > 0:
    args += ' -virtual_res '
    for k in virtual_res: args += '%d ' % k
if len( fixed_res ) > 0:
    args += ' -fixed_res '
    for k in fixed_res: args += '%d ' % k
if len( calc_rms_res ) > 0:
    args += ' -calc_rms_res '
    for k in calc_rms_res: args += '%d ' % k

args_START = args

if AUTO_TUNE:
    cluster_tag = ' -auto_tune '
else:
    cluster_tag = ' -cluster:radius %s ' % CLUSTER_RADIUS

cluster_by_all_atom_rmsd_tag = ''
if cluster_by_all_atom_rmsd: cluster_by_all_atom_rmsd_tag = ' -cluster_by_all_atom_rmsd '


################################
# MAIN LOOP
################################
# Loop over fragment lengths.

if (max_length == 0): max_length = NRES
for L in range( min_length, max_length + 1 ):

    chunk_length = L;
    #num_chunks = ( len( sequence) - chunk_length) + 1

    for k in range( 1, NRES + 1 ) :
        i = k
        j = i + chunk_length - 1
        if ( j > NRES ): j -= NRES

        if ( not LOOP and ( i < MIN_RES or j > MAX_RES ) ): continue

        if LOOP:
            if ( i > (loop_end+1)   or i < loop_start ): continue
            #if ( j < (loop_start-1) or j > (loop_end-min_loop_gap ) ): continue
            if ( j < (loop_start-1) or j > (loop_end-2 ) ): continue
            #if not( ( i == j+1 and j < (loop_end-min_loop_gap+1) )   or ( i - j >= min_loop_gap): continue
            if not( ( i == j+1 and j < (loop_end-1) )   or ( (i - j) >= 2 ) ): continue
            if (not loop_force_Nsquared) and  ( i != j+1 ) and not ( i == loop_end+1 or j == loop_start-1): continue


        #ZIGZAG!! special case for beta hairpins.
        if ( ZIGZAG and abs( ( i - MIN_RES ) - ( MAX_RES - j ) ) > 1 ) : continue

        if follow_path and ( [i,j] not in pathway_regions ): continue

        if ( i in virtual_res or j in virtual_res ): continue

        overall_job_tag = 'REGION_%d_%d' % (i,j)

        print 'Do region ==> ',i,j,

        # This job is maybe already done...
        outfile_cluster = overall_job_tag.lower()+'_sample.cluster.out'
        if exists( outfile_cluster ):
            all_job_tags.append(  overall_job_tag )
            jobs_done.append( overall_job_tag   )
            print 'DONE'
            continue
        else:
            print

        # OUTPUT DIRECTORY
        if not( exists( overall_job_tag) ):
            system( 'mkdir -p ' + overall_job_tag )

        termini_tag = ""
        if ( i == 1 ): termini_tag += " -n_terminus"
        if ( j == NRES ): termini_tag += " -c_terminus"
        args = args_START + termini_tag


        ###########################################
        # DO THE JOBS
        ###########################################
        start_regions = []

        for k in range( 1, MAX_ADDED_SEGMENT):
            i_prev = i
            j_prev = j - k
            prev_job_tag = 'REGION_%d_%d' % (i_prev,j_prev)
            if prev_job_tag in all_job_tags:   start_regions.append( [i_prev, j_prev ] )

        for k in range( 1, MAX_ADDED_SEGMENT):
            i_prev = i + k
            j_prev = j
            prev_job_tag = 'REGION_%d_%d' % (i_prev,j_prev)
            if prev_job_tag in all_job_tags:   start_regions.append( [i_prev, j_prev ] )

        if BUILD_BOTH_TERMINI:
            i_prev = i + 1
            j_prev = j - 1
            prev_job_tag = 'REGION_%d_%d' % (i_prev,j_prev)
            if prev_job_tag in all_job_tags:   start_regions.append( [i_prev, j_prev ] )

        # One more possibility -- if we contain a long segment of virtual residues.
        virtual_sub_segment = []
        for m in wrap_range(i,j+1):
            if m in virtual_res: virtual_sub_segment.append( m )
        if len( virtual_sub_segment ) > 0 :
            virtual_start = virtual_sub_segment[0]
            virtual_end   = virtual_sub_segment[-1]
            if ( j - virtual_end ) <= MAX_FRAGMENT_OVERLAP:
                i_prev = i
                for j_prev in wrap_range( virtual_start - MAX_FRAGMENT_OVERLAP, virtual_start+1 ):
                    if ( [i_prev, j_prev ] in start_regions ): continue
                    prev_job_tag = 'REGION_%d_%d' % (i_prev,j_prev)
                    if prev_job_tag in all_job_tags: start_regions.append( [i_prev, j_prev ] )
                    print ' -- long frag to bridge over virtual segment. start from:  %d-%d' % (i_prev,j_prev)
            if ( virtual_start-i ) <= MAX_FRAGMENT_OVERLAP:
                j_prev = j
                for i_prev in wrap_range( virtual_end+1, virtual_end+MAX_FRAGMENT_OVERLAP+1):
                    if ( [i_prev, j_prev ] in start_regions ): continue
                    prev_job_tag = 'REGION_%d_%d' % (i_prev,j_prev)
                    if prev_job_tag in all_job_tags: start_regions.append( [i_prev, j_prev ] )
                    print ' -- long frag to bridge over virtual segment. start from:  %d-%d' % (i_prev,j_prev)


        job_tags = []
        combine_files = []

        ########################################################
        # Several "modes" -- different stuff for the grinder!
        #
        #  currently have: DENOVO, TEMPLATE, FRAGMENT_LIBRARY
        ########################################################

        prev_job_tags = []
        if LOOP:

            if ( j == loop_start-1 and i == loop_end+1 ):
                sub_job_tag = "START_FROM_LOOP_START_PDB"

                args2 = args
                args2 += ' -s1 ' + loop_start_pdb
                args2 += ' -input_res1 '
                for k in wrap_range(i, j+1): args2 += ' %d' % k
                args2 += ' -use_packer_instead_of_rotamer_trials'

                setup_dirs_and_condor_file_and_tags( overall_job_tag, sub_job_tag, prev_job_tags, args2, '', \
                                                     fid_dag, job_tags, all_job_tags, jobs_done, real_compute_job_tags, combine_files)

        else:

            if TEMPLATE:

                for n in range( len( template_pdbs ) ):
                    # Good to just build the whole thing off template.
                    template_pdb = template_pdbs[ n ]
                    template_mapping = template_mappings[ template_pdb ]

                    if ( not template_continuous( i,j,template_mapping ) ): continue

                    sub_job_tag = "START_FROM_TEMPLATE_%d" % n

                    args2 = args
                    args2 += ' -s1 ' + template_pdb
                    args2 += ' -input_res1 '
                    for k in wrap_range(i,j+1): args2 += ' %d' % k
                    args2 += ' -slice_res1 '
                    for k in wrap_range(i,j+1): args2 += ' %d' % template_mapping[ k ]
                    args2 += ' -backbone_only1'
                    args2 += ' -use_packer_instead_of_rotamer_trials'

                    setup_dirs_and_condor_file_and_tags( overall_job_tag, sub_job_tag, prev_job_tags, args2, '', \
                                                         fid_dag, job_tags, all_job_tags, jobs_done, real_compute_job_tags, combine_files)

            if FRAGMENT_LIBRARY:
                for n in range( len( frag_files ) ):
                    # We might be at a length where we match a fragment...
                    frag_length = frag_lengths[ n ]
                    frag_file = frag_files[ n ]

                    if not ( frag_length  == L ): continue

                    sub_job_tag = "START_FROM_FRAGMENT_LIBRARY_%dMER" % frag_length

                    args2 = args
                    args2 += ' -in:file:frag_files ' + frag_file
                    args2 += ' -use_packer_instead_of_rotamer_trials'

                    args2 += ' -sample_res'
                    for m in wrap_range(i,j+1): args2 += ' %d' % m

                    setup_dirs_and_condor_file_and_tags( overall_job_tag, sub_job_tag, prev_job_tags, args2, '', \
                                                         fid_dag, job_tags, all_job_tags, jobs_done, real_compute_job_tags, combine_files)

            if SWA_FRAGS and (outfile_cluster in silent_files_in ) and ( L in swa_frag_lengths ) :

                sub_job_tag = "SWA_REPACK_%dMER" % L

                args2 = "%s -silent1 %s/%s" % ( args, swa_silent_file_dir, outfile_cluster )
                args2 += ' -use_packer_instead_of_rotamer_trials'
                args2 += ' -input_res1 '
                for k in wrap_range(i,j+1): args2 += ' %d' % k
                setup_dirs_and_condor_file_and_tags( overall_job_tag, sub_job_tag, prev_job_tags, args2, '', \
                                                     fid_dag, job_tags, all_job_tags, jobs_done, real_compute_job_tags, combine_files)



            if (L <= 2) and DENOVO: # This happens for two-residue fragments.

                sub_job_tag = "START_FROM_SCRATCH"

                args2 = args
                args2 += ' -sample_res %d %d ' % (i,j)

                setup_dirs_and_condor_file_and_tags( overall_job_tag, sub_job_tag, prev_job_tags, args2, '', \
                                                     fid_dag, job_tags, all_job_tags, jobs_done, real_compute_job_tags, combine_files)


        ########################################################
        # Chain closure #1 -- assume j, j+2 are sampled already,
        #  then solve for j,j+1,j+2. Also (important!), this
        #  assumes that the backbone outside the loop is fixed.
        # This is meant for O(N) loop modeling -- build forward,
        #  build backward and meet in the middle.
        ########################################################
        if LOOP and ( i == j+1 ) and (not no_fixed_res) and ( j >= loop_start and i <= loop_end) : # special, chain closure!
            # old-style: close the loop
            job_tag1 = "REGION_%d_%d" % ( i+1,     loop_start-1 )
            job_tag2 = "REGION_%d_%d" % ( loop_end+1, j       )

            if ( job_tag1 in all_job_tags ) and ( job_tag2 in all_job_tags ):

                sub_job_tag = 'START_FROM_%s_%s_CLOSE_LOOP' % ( job_tag1, job_tag2 )

                decoy_tag = 'S_$(Process)'

                infile1 =  job_tag1.lower()+"_sample.cluster.out"
                args2 = '%s  -silent1 %s -tags1 %s' % (args, infile1, decoy_tag )
                args2 += " -input_res1 "
                for m in wrap_range( i+1, loop_start ): args2 += ' %d' % m

                infile2 =  job_tag2.lower()+"_sample.cluster.out"
                args2 += ' -silent2 %s ' % ( infile2 )
                args2 += " -input_res2 "
                for m in wrap_range( loop_end+1, j+1 ): args2 += ' %d' % m

                args2 += " -bridge_res %d %d %d" % (j,j+1,j+2)
                args2 += " -cutpoint_closed %d " % (j+1)

                args2 += " -sample_res"
                for m in range( 1, NRES+1): args2 += " %d" % m

                prev_job_tags = [ job_tag1, job_tag2 ]
                setup_dirs_and_condor_file_and_tags( overall_job_tag, sub_job_tag, prev_job_tags, args2, decoy_tag, \
                                                     fid_dag, job_tags, all_job_tags, jobs_done, real_compute_job_tags, combine_files)



        ###########################################################
        # APPEND OR PREPEND TO PREVIOUS PDB
        #  [I wonder if this could just be unified with above?]
        ###########################################################
        for start_region in start_regions:

            i_prev = start_region[0]
            j_prev = start_region[1]
            prev_job_tags = [ 'REGION_%d_%d' % (i_prev,j_prev) ]
            infile = 'region_%d_%d_sample.cluster.out' % (i_prev,j_prev)
            input_res1 =  wrap_range( i_prev, j_prev+1 )

            if ( i == j+1 and LOOP ):
                if ( j == j_prev ) and (i_prev == (j + min_loop_gap) ): # close the loop
                    #  sample j, j+1;  bridge_res j+2, j+3, j+4.  Note that  j+4 was previously sampled, so we can hopefully
                    #  believe its psi, omega.
                    sub_job_tag = 'START_FROM_REGION_%d_%d_CLOSE_LOOP' % ( i_prev, j_prev )

                    decoy_tag = 'S_$(Process)'

                    args2 = '%s  -silent1 %s -tags1 %s' % (args, infile, decoy_tag )
                    args2 += " -input_res1 "
                    for m in input_res1: args2 += ' %d' % m

                    args2 += " -sample_res"
                    if ( j not in fixed_res ): args2 += " %d" % j
                    args2 +=" %d" % (j+1)
                    args2 += " -bridge_res %d %d %d" % (j+2,j+3,j+4)
                    args2 += " -cutpoint_closed %d " % (j+1)

                    setup_dirs_and_condor_file_and_tags( overall_job_tag, sub_job_tag, prev_job_tags, args2, decoy_tag, \
                                                         fid_dag, job_tags, all_job_tags, jobs_done, real_compute_job_tags, combine_files)

            else:
                if TEMPLATE:
                    for n in range( len( template_pdbs ) ):
                        template_pdb = template_pdbs[ n ]
                        template_mapping = template_mappings[ template_pdb ]

                        input_res2 = []
                        for m in wrap_range( i, j+1 ):
                            if m not in input_res1:
                                input_res2.append( m )
                        if ( not template_continuous( input_res2[0],input_res2[-1],template_mapping ) ): continue


                        sub_job_tag = 'START_FROM_REGION_%d_%d_TEMPLATE_%d' % ( i_prev, j_prev, n )

                        args2 = "%s  -silent1 %s " % (args, infile )
                        args2 += " -input_res1 "
                        for m in input_res1: args2 += ' %d' % m

                        args2 += " -s2 %s" % template_pdb

                        args2 += " -input_res2 "
                        for k in input_res2: args2 += ' %d' % k

                        args2 += " -slice_res2 "
                        for k in input_res2: args2 += ' %d' % template_mapping[ k ]

                        args2 += ' -backbone_only2'

                        args2 += ' -sample_res '
                        for m in wrap_range( i, j+1 ): args2 += ' %d' % m


                        setup_dirs_and_condor_file_and_tags( overall_job_tag, sub_job_tag, prev_job_tags, args2, '', \
                                                             fid_dag, job_tags, all_job_tags, jobs_done, real_compute_job_tags, combine_files)


                if FRAGMENT_LIBRARY:
                    for frag_length in frag_lengths:

                        ( startpos, endpos, num_overlap_residues ) = check_frag_overlap( i, j, i_prev, j_prev, frag_length )
                        if ( num_overlap_residues < 0 or num_overlap_residues > MAX_FRAGMENT_OVERLAP ): continue

                        sub_job_tag = 'START_FROM_REGION_%d_%d_FRAGMENT_LIBRARY_%dMER' % ( i_prev, j_prev, frag_length )

                        decoy_tag = 'S_$(Process)'

                        args2 = '%s  -silent1 %s -tags1 %s' % (args, infile, decoy_tag )
                        args2 += " -input_res1 "
                        for m in input_res1: args2 += ' %d' % m

                        frag_file = frag_files[  frag_lengths.index( frag_length) ]
                        args2 += " -in:file:frag_files %s" % frag_file

                        args2 += ' -sample_res '
                        for m in wrap_range( startpos, endpos+1 ): args2 += ' %d' % m

                        setup_dirs_and_condor_file_and_tags( overall_job_tag, sub_job_tag, prev_job_tags, args2, decoy_tag, \
                                                             fid_dag, job_tags, all_job_tags, jobs_done, real_compute_job_tags, combine_files)



                if SWA_FRAGS:

                    for frag_length in swa_frag_lengths:

                        ( startpos, endpos, num_overlap_residues ) = check_frag_overlap( i, j, i_prev, j_prev, frag_length )
                        if ( num_overlap_residues < 0 or num_overlap_residues > MAX_FRAGMENT_OVERLAP ): continue

                        infile_swa = "region_%d_%d_sample.cluster.out" % (startpos, endpos)
                        if infile_swa not in silent_files_in: continue

                        sub_job_tag = 'START_FROM_REGION_%d_%d_SWA_FRAGMENTS_%dMER' % ( i_prev, j_prev, frag_length )

                        decoy_tag = 'S_$(Process)'

                        args2 = '%s  -silent1 %s -tags1 %s' % (args, infile, decoy_tag )
                        args2 += " -input_res1 "
                        for m in input_res1: args2 += ' %d' % m

                        args2 += " -silent2 %s/%s" % (swa_silent_file_dir, infile_swa )
                        args2 += " -input_res2 "
                        for m in wrap_range( startpos, endpos+1 ): args2 += ' %d' % m

                        args2 += ' -sample_res '
                        for m in wrap_range( startpos, endpos+1 ): args2 += ' %d' % m

                        setup_dirs_and_condor_file_and_tags( overall_job_tag, sub_job_tag, prev_job_tags, args2, decoy_tag, \
                                                             fid_dag, job_tags, all_job_tags, jobs_done, real_compute_job_tags, combine_files)



        do_denovo = DENOVO
        if not DENOVO and len( combine_files ) == 0:
            print "No template_jobs for ", overall_job_tag,
            print " ... rescuing the run with denovo!"
            do_denovo = 1
            max_res_to_add_denovo = 1

        for start_region in start_regions:

            i_prev = start_region[0]
            j_prev = start_region[1]
            prev_job_tags = [ 'REGION_%d_%d' % (i_prev,j_prev) ]
            infile = 'region_%d_%d_sample.cluster.out' % (i_prev,j_prev)

            if ( abs(i - i_prev ) <= max_res_to_add_denovo and \
                 abs(j - j_prev ) <= max_res_to_add_denovo and
                 do_denovo ) :

                sub_job_tag = 'START_FROM_REGION_%d_%d_DENOVO' % ( i_prev, j_prev )

                decoy_tag = 'S_$(Process)'
                args2 = '%s  -silent1 %s -tags1 %s' % (args, infile, decoy_tag )

                args2 += ' -input_res1 '
                for m in wrap_range(i_prev,j_prev+1): args2 += ' %d' % m

                args2 += ' -sample_res '
                if ( i < i_prev and j == j_prev):
                    for m in range(i,i_prev+1):
                        if m not in fixed_res: args2 += ' %d' % m
                elif ( i == i_prev and j > j_prev ):
                    for m in range(j_prev,j+1):
                        if m not in fixed_res: args2 += ' %d' % m
                else:
                    for m in [i,j]:
                        if m not in fixed_res: args2 += ' %d' % m

                setup_dirs_and_condor_file_and_tags( overall_job_tag, sub_job_tag, prev_job_tags, args2, decoy_tag, \
                                                     fid_dag, job_tags, all_job_tags, jobs_done, real_compute_job_tags, combine_files)



        if len( combine_files ) == 0:
            print "PROBLEM: template_jobs for ", overall_job_tag
            print " Possible solution: in fragment library run, specify -min_length (the smallest region modeled) to be the frag size"
            exit( 0 )

        ################################################################
        # CLUSTER! And keep a small number of representatives (400)
        ################################################################

        outfile_cluster = overall_job_tag.lower()+'_sample.cluster.out'
        args_cluster = ' -cluster_test -in:file:silent %s  -in:file:silent_struct_type binary  -database %s  %s -out:file:silent %s -nstruct %d %s -score_diff_cut %8.3f' % (string.join( combine_files ), DB,  cluster_tag, outfile_cluster, FINAL_NUMBER, cluster_by_all_atom_rmsd_tag, score_diff_cut )

        condor_submit_cluster_file = 'CONDOR/REGION_%d_%d/cluster.condor' % (i,j)

        make_condor_submit_file( condor_submit_cluster_file, args_cluster, 1, "scheduler" )

        fid_dag.write('\nJOB %s %s\n' % (overall_job_tag,condor_submit_cluster_file) )
        fid_dag.write('PARENT %s CHILD %s\n' % (string.join(job_tags),overall_job_tag) )
        fid_dag.write('SCRIPT POST %s %s %s %s\n' % (overall_job_tag, POST_PROCESS_CLUSTER_SCRIPT, outfile_cluster, overall_job_tag ) )

        all_job_tags.append(  overall_job_tag )



#####################################################################################
if LOOP:
    final_outfile = "region_FINAL.out"
    if not exists( final_outfile ):

        last_outfiles = []
        last_jobs = []
        for i in range( NRES-1 ):
            job_tag = 'REGION_%d_%d' % (i+1,i)
            if job_tag in all_job_tags:
                last_jobs.append( job_tag )
                last_outfiles.append( job_tag.lower()+'_sample.cluster.out' )
        assert( len(last_outfiles) > 0 )

        args_cluster = ' -cluster_test -in:file:silent %s  -in:file:silent_struct_type binary  -database %s  %s -out:file:silent %s  %s -score_diff_cut %8.3f -silent_read_through_errors  -nstruct %d ' % (string.join( last_outfiles ), DB,  cluster_tag, final_outfile, cluster_by_all_atom_rmsd_tag, 2 * score_diff_cut, 10000 )

        condor_submit_cluster_file = 'CONDOR/REGION_FINAL_cluster.condor'
        make_condor_submit_file( condor_submit_cluster_file, args_cluster, 1 )

        final_job_tag = "REGION_FINAL"
        fid_dag.write('\nJOB %s %s\n' % ( final_job_tag,condor_submit_cluster_file) )
        for prev_job_tag in last_jobs:
            if ( prev_job_tag not in jobs_done ):
                fid_dag.write('PARENT %s  CHILD %s\n' % (prev_job_tag, final_job_tag) )



print
print "Total number of jobs to run (not counting clustering):", len( real_compute_job_tags )
print "Total number of final outfiles (and clustering jobs):", len( all_job_tags )

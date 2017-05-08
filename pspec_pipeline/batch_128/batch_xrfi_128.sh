#$ -S /bin/bash
#$ -V
#$ -cwd
#$ -o grid_output
#$ -e grid_output
#$ -l h_vmem=12G
#$ -N FLAG_128

# hand this script one pol e.g. *xx*O

source activate PAPER
ARGS=`pull_args.py $*`
CALFILE='psa6622_v003'
PATH2CAPO=/home/saulkohn/ReposForCanopy/capo/
OMNIPATH=/data4/paper/2013EoR/Analysis/ProcessedData/epoch2/omni_v5_xtalk_4pol/
CHANFLAGS="101,102,148,149,150,151,152,153,154,169"
for f in ${ARGS}; do
    fpath=`cut -d "z" -f 1 <<< "$f"`
    fQ=z`cut -d "z" -f 2 <<< "$f"`
    p=${fQ:18:2}
    
    echo ${PATH2CAPO}/omni/omni_xrfi.py --boxside=16 $fpath${fQ::18}npz 
    ${PATH2CAPO}/omni/omni_xrfi.py --boxside=16 $fpath${fQ::18}npz
    
    for pp in xx xy yx yy; do
        fP=${f/$p/$pp}
        echo ${PATH2CAPO}/omni/omni_xrfi_apply.py --omnipath=${OMNIPATH}/%s.chisqflag.npz --multipol ${fP}
        ${PATH2CAPO}/omni/omni_xrfi_apply.py --omnipath=${OMNIPATH}/%s.chisqflag.npz --multipol ${fP}
        echo xrfi_simple.py -n 1000 -c ${CHANFLAGS} ${fP}R
        xrfi_simple.py -n 1000 -c ${CHANFLAGS} ${fP}R
        echo rm -rf ${fP}R
        rm -rf ${fP}R
    done
    #echo ${PATH2CAPO}/pspec_pipeline/pspec_prep.py -C ${CALFILE} -a cross --window=blackman-harris --nogain --nophs --clean=1e-9 --horizon=15 ${f}RR
    #${PATH2CAPO}/pspec_pipeline/pspec_prep.py -C ${CALFILE} -a cross --window=blackman-harris --nogain --nophs --clean=1e-9 --horizon=15 ${f}RR
    #echo xrfi_simple.py -n 4 ${f}RRB 
    #xrfi_simple.py -n 4 ${f}RRB 
done

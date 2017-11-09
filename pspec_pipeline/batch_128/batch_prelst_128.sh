#$ -S /bin/bash
#$ -V
#$ -cwd
#$ -o grid_output
#$ -j y
#$ -l h_vmem=5G
#$ -N fg_sub

source activate PAPER #HERA
ARGS=`pull_args.py $*`
CALFILE=psa6622_v003
PATH2CAPO='/home/saulkohn/ReposForCanopy/capo'

for FILE in $ARGS; do
    echo ${PATH2CAPO}/pspec_pipeline/pspec_prep.py -C ${CALFILE} -a cross --window=blackman-harris --nogain --nophs --clean=1e-12 --horizon=15 ${FILE}
    ${PATH2CAPO}/pspec_pipeline/pspec_prep.py -C ${CALFILE} -a cross --window=blackman-harris --nogain --nophs --clean=1e-12 --horizon=15 ${FILE}

    echo xrfi_simple.py -n 4 ${FILE}B
    xrfi_simple.py -n 4 ${FILE}B #&& rm ${FILE}B/* && rmdir ${FILE}B
done

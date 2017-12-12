#$ -S /bin/bash
#$ -V
#$ -cwd
#$ -o grid_output
#$ -j y
#$ -l h_vmem=5G
#$ -N fg_flag_sub_linclean

source activate PAPER #HERA
ARGS=`pull_args.py $*`
CALFILE=psa6622_v003
PATH2CAPO='/home/saulkohn/ReposForCanopy/capo'

for FILE in $ARGS; do
    #echo ${PATH2CAPO}/pspec_pipeline/pspec_prep.py -C ${CALFILE} -a cross --window=blackman-harris --nogain --nophs --clean=1e-12 --horizon=15 ${FILE}
    #${PATH2CAPO}/pspec_pipeline/pspec_prep.py -C ${CALFILE} -a cross --window=blackman-harris --nogain --nophs --clean=1e-12 --horizon=15 ${FILE}
    echo xrfi_simple.py -n 1000 -c 0_42,50_51,64_65,72_78,100_103,151_154,166_170,175,178_202 ${FILE}
    xrfi_simple.py -n 1000 -c 0_42,50_51,64_65,72_78,100_103,151_154,166_170,175,178_202 ${FILE}
    echo python ${PATH2CAPO}/sak/scripts/linclean.py -C ${CALFILE} --horizon=15 ${FILE}R
    python ${PATH2CAPO}/sak/scripts/linclean.py -C ${CALFILE} --horizon=15 ${FILE}R
    echo xrfi_simple.py -n 4 ${FILE}RB
    xrfi_simple.py -n 4 ${FILE}RB #&& rm ${FILE}B/* && rmdir ${FILE}B
done

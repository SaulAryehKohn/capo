#$ -S /bin/bash
#$ -V
#$ -cwd
#$ -o grid_output
#$ -e grid_output
#$ -l h_vmem=10G
#$ -N CALIB_128_4POL

source activate HERA
# hand this script a SINGLE POL of files and it will get the others
ARGS=`pull_args.py $*`

PATH2CAPO='/home/saulkohn/ReposForCanopy/capo'
PATH2HERACAL='/home/saulkohn/githubs/hera_cal'
CALPATH='/data4/paper/2013EoR/Analysis/ProcessedData'
abscal_yy_e1='/home/saulkohn/psa128gainSolutions/cal.2456620.49401.yy.sgains.npz'
abscal_xx_e1='/home/saulkohn/psa128gainSolutions/cal.2456620.49401.xx.sgains.npz'
abscal_yy_e2='/home/saulkohn/psa128gainSolutions/cal.2456680.33389.yy.sgains.npz'
abscal_xx_e2='/home/saulkohn/psa128gainSolutions/cal.2456680.33389.xx.sgains.npz'

for f in ${ARGS}; do
    # h-h-h-hacky
    fQ=z`cut -d "z" -f 2 <<< "$f"`
    p=${fQ:18:2}
    
    fxx=${f/$p/xx}
    fxy=${f/$p/xy}
    fyx=${f/$p/yx}
    fyy=${f/$p/yy}
    
    fQxx=${fQ/$p/xx}
    fQxy=${fQ/$p/xy}
    fQyx=${fQ/$p/yx}
    fQyy=${fQ/$p/yy}    

    if ((${fQ:4:7} < 2456679 )); then
        abscal_y=${abscal_yy_e1}
        abscal_x=${abscal_xx_e1}
        calpath=${CALPATH}/epoch1/omni_v6_4pol/
    else
        abscal_y=${abscal_yy_e2}
        abscal_x=${abscal_xx_e2}
        calpath=${CALPATH}/epoch2/omni_v6_4pol/
    fi
    
    echo python ${PATH2CAPO}/sak/scripts/create_abscal_calfits.py -p xx --miriad=${fxx} --abscal_list=${abscal_x} --cal_scheme='divide' --calpath=${calpath}
    python ${PATH2CAPO}/sak/scripts/create_abscal_calfits.py -p xx --miriad=${fxx} --abscal_list=${abscal_x} --cal_scheme='divide' --calpath=${calpath}
    omnipath=${calpath}${fQxx}.calfits
    echo ${PATH2HERACAL}/scripts/omni_apply.py -p xx --omnipath=${omnipath} --extension="K" --outpath=${calpath} ${fxx}
    ${PATH2HERACAL}/scripts/omni_apply.py -p xx --omnipath=${omnipath} --extension="K" --outpath=${calpath} ${fxx}    

    echo python ${PATH2CAPO}/sak/scripts/create_abscal_calfits.py -p yy --miriad=${fyy} --abscal_list=${abscal_y} --cal_scheme='divide' --calpath=${calpath}
    python ${PATH2CAPO}/sak/scripts/create_abscal_calfits.py -p yy --miriad=${fyy} --abscal_list=${abscal_y} --cal_scheme='divide' --calpath=${calpath}
    omnipath=${calpath}${fQyy}.calfits
    echo ${PATH2HERACAL}/scripts/omni_apply.py -p yy --omnipath=${omnipath} --extension="K" --outpath=${calpath} ${fyy}
    ${PATH2HERACAL}/scripts/omni_apply.py -p yy --omnipath=${omnipath} --extension="K" --outpath=${calpath} ${fyy}
    
    echo python ${PATH2CAPO}/sak/scripts/create_abscal_calfits.py -p xy --miriad=${fxy} --abscal_list=${abscal_x},${abscal_y} --cal_scheme='divide' --calpath=${calpath}
    python ${PATH2CAPO}/sak/scripts/create_abscal_calfits.py -p xy --miriad=${fxy} --abscal_list=${abscal_x},${abscal_y} --cal_scheme='divide' --calpath=${calpath}
    omnipath=${calpath}${fQxy}.calfits
    echo ${PATH2HERACAL}/scripts/omni_apply.py -p xy --omnipath=${omnipath} --extension="K" --outpath=${calpath} ${fxy}
    ${PATH2HERACAL}/scripts/omni_apply.py -p xy --omnipath=${omnipath} --extension="K" --outpath=${calpath} ${fxy}    

    echo python ${PATH2CAPO}/sak/scripts/create_abscal_calfits.py -p yx --miriad=${fyx} --abscal_list=${abscal_x},${abscal_y} --cal_scheme='divide' --calpath=${calpath}
    python ${PATH2CAPO}/sak/scripts/create_abscal_calfits.py -p yx --miriad=${fyx} --abscal_list=${abscal_x},${abscal_y} --cal_scheme='divide' --calpath=${calpath}
    omnipath=${calpath}${fQyx}.calfits
    echo ${PATH2HERACAL}/scripts/omni_apply.py -p yx --omnipath=${omnipath} --extension="K" --outpath=${calpath} ${fyx}
    ${PATH2HERACAL}/scripts/omni_apply.py -p yx --omnipath=${omnipath} --extension="K" --outpath=${calpath} ${fyx}            

done


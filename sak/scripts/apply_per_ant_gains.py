import numpy as np
import aipy
import sys, os
import optparse

o = optparse.OptionParser()
o.add_option('-p','--pol',dest='pol',help='polarization to calibrate')
o.add_option('--nants',dest='nants',default=128,help='number of antennae')
o.add_option('--xcal',dest='xcal',default=None,help='path to X gain npz')
o.add_option('--ycal',dest='ycal',default=None,help='path to Y gain npz')
o.add_option('--verbose',dest='verbose',default=False,action='store_true',help='Toggle verbosity')

opts,args = o.parse_args(sys.argv[1:])
opts.nants = int(opts.nants)
# check inputs
assert opts.pol
if opts.pol=='xx':
    assert opts.xcal
    dxx = np.load(opts.xcal)
elif opts.pol=='yy':
    assert opts.ycal
    dyy = np.load(opts.ycal)
else:
    assert opts.xcal
    assert opts.ycal
    dxx = np.load(opts.xcal)
    dyy = np.load(opts.ycal)

# cleanse calibrations
no_soln_ants=[]
for ant in range(opts.nants):
    antstr = str(ant)
    if opts.pol != 'yy':
        if all([x == 0.+0j for x in dxx[antstr]]):
            no_soln_ants.append(ant)
    if opts.pol != 'xx':
        if all([x == 0.+0j for x in dyy[antstr]]):
            no_soln_ants.append(ant)

no_soln_ants = list(set(no_soln_ants))
if opts.verbose:
    print('NOTE: No gain solutions for these antennae:')
    print(no_soln_ants)    

def mfunc(uv,p,d):
    uvw,t,(i,j) = p
    if opts.pol == 'xx':
        gi,gj = dxx[str(i)],dxx[str(j)]
    elif opts.pol == 'yy':
        gi,gj = dyy[str(i)],dyy[str(j)]
    elif opts.pol == 'xy':
        gi,gj = dxx[str(i)],dyy[str(j)]
    else:
        gi,gj = dyy[str(i)],dxx[str(j)]
    #XXX
    gi = np.conjugate(gi)
    factor = gi*gj
    d /= factor
    return p,d

for f in args:
    uvi = aipy.miriad.UV(f)
    uvo = aipy.miriad.UV(f+'K',status='new')
    print f,'->',f+'K'
    uvo.init_from_uv(uvi)
    uvo.pipe(uvi,mfunc=mfunc,append2hist=' '.join(sys.argv))
    del(uvi);del(uvo)


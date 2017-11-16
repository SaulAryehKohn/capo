#!/usr/bin/env python
"""
Wedge-filter by modelling visibilities with Fourier modes in delay space.
*** Only to use on files containing a single separation type ***
"""
import numpy as np
import sys, os
from astropy import units as u
from astropy import constants as c
import aipy, optparse

o = optparse.OptionParser()
o.add_option('--bl_length',default=30,help='Baseline length *in meters*')
o.add_option('--horizon',default=15,help='supra-horizon allowance *in nanoseconds*')
o.add_option('--model',action='store_true',help='return model instead of residual')
opts,args = o.parse_args(sys.argv[1:])

# functions
def tau_select(tau, tau_max):
    """
    tau: ndarray
    tau_max: float
    """
    imax = np.where((tau>0)*(tau<=tau_max))[0].max()
    taus = tau[1:imax+1]
    return taus,imax

def buildA(taus, freqs):
    nfreq = len(freqs)
    arg = 2*np.pi*np.outer(freqs,taus)
    A = np.concatenate((np.ones([nfreq,1]),np.cos(arg),np.sin(arg)),axis=1)
    return A

def linCLEAN(vis, flag_idx, tau_max, A=None, A_all=None, return_As=False):
    """
    vis: ndarray (complex128)
    flag_idx: ndarray (int)
    tau_max: float
    A: ndarray; fit matrix for unflagged channels
    A_all: ndarray; fit matrix for all channels
    return_As: bool; toggle return of A matrices
    """
    nfreq = vis.shape[0]
    f,df = np.linspace(0.1,0.2,num=nfreq,retstep=True)
    tau = np.fft.fftfreq(nfreq,d=df)
    taus,imax = tau_select(tau,tau_max)
    whf = [c for c in range(nfreq) if not c in flag_idx]
    f_tofit = f[whf]
    if not A:
        A = buildA(taus,f_tofit)
    if not A_all:
        A_all = buildA(taus,f)
    xreal,residuals,rank,singular = np.linalg.lstsq(A,vis[whf].real)
    ximag,residuals,rank,singular = np.linalg.lstsq(A,vis[whf].imag)
    model = np.dot(A_all,xreal) + 1j*np.dot(A_all,ximag)
    resid = vis - model
    if return_As:
        return resid, model, A, A_all
    return resid, model

global curtime
curtime=0.

b_len = opts.bl_length*u.m
tau_max = ((b_len/c.c).to(u.ns) + opts.horizon*u.ns).value

### there must be a better way than two different functions
def mfunc_resid(uv,p,d,f):
    uvw,t,(i,j) = p
    """
    TODO: don't regenerate A all the time
    if not t == curtime:
        curtime = t
        rtn = True
    """
    vis = d
    flag_idx = np.where(f)[0]
    resid,_ = linCLEAN(vis,flag_idx,tau_max)
    return p,resid,f

def mfunc_model(uv,p,d,f):
    uvw,t,(i,j) = p
    """
    TODO: don't regenerate A all the time
    if not t == curtime:
        curtime = t
        rtn = True
    """
    vis = d
    flag_idx = np.where(f)[0]
    _,model = linCLEAN(vis,flag_idx,tau_max)
    return p,model,f

for infile in args:
    if opts.model:
        outfile = infile+'F'
    else:
        outfile = infile+'B'
    if os.path.exists(outfile):
        print('%s exists. Skipping...'%outfile)
        continue
    print('%s --> %s'%(infile,outfile))
    
    uvi = aipy.miriad.UV(infile)
    uvo = aipy.miriad.UV(outfile,status='new')
    uvo.init_from_uv(uvi)
    
    if opts.model:
        uvo.pipe(uvi,mfunc_model,raw=True,append2hist='LINCLEAN: '+' '.join(sys.argv)+'\n')
    else:
        uvo.pipe(uvi,mfunc_resid,raw=True,append2hist='LINCLEAN: '+' '.join(sys.argv)+'\n')
    
    del(uvo)


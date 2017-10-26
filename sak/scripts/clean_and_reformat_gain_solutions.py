#!/usr/bin/env python

import numpy as np, matplotlib.pyplot as plt
import sys, os
from astropy import units as u
from astropy import constants as c

# Constants
b_len = 30.*u.m

# functions
def tau_select(tau,b_len,tau_pad=10.):
    """ Select taus to fit given a baseline length """
    tau_max = (b_len/c.c).to(u.ns).value
    imax = np.where((tau>0)*(tau<=tau_max+tau_pad))[0].max()
    taus = tau[1:imax+1]
    return taus,imax

def buildA(taus,freqs):
    """Build A matrix for CLEAN"""
    nfreq = len(freqs)
    arg = 2.*np.pi*np.outer(freqs,taus)
    A = np.concatenate((np.ones([nfreq,1]),np.cos(arg),np.sin(arg)),axis=1)
    return A

def linCLEAN(wf,ifl,b_len,tau_pad=10.):
    model = np.zeros_like(wf)
    nant,nfreq = wf.shape
    f,df = np.linspace(0.1,0.2,num=nfreq,retstep=True) #GHz
    tau = np.fft.fftfreq(nfreq,d=df)
    taus,imax = tau_select(tau,b_len,tau_pad)
    for i in np.arange(nant):
        #print(i)
        whf = np.where(ifl[i,:])[0]
        not_whf = np.where(np.logical_not(ifl[i,:]))[0]
        if len(whf)==0:
            continue
        f_tofit = f[whf]
        A = buildA(taus,f_tofit)
        A_all = buildA(taus,f)
        xreal,residuals,rank,singular = np.linalg.lstsq(A,wf[i,whf].real)
        ximag,residuals,rank,singular = np.linalg.lstsq(A,wf[i,whf].imag)
        model[i,:] = np.dot(A_all,xreal) + 1j*np.dot(A_all,ximag)
        resid = wf - model
    return model,resid

# file handling
for fname in sys.argv[1:]:
    wf = np.load(fname)['gains']
    ifl = np.isnan(wf)
    
    # run function
    model, resid = linCLEAN(wf,np.logical_not(ifl),b_len,tau_pad=15.)
    
    # save results
    fout = os.path.dirname(fname)+'/cal.'+os.path.basename(fname)
    out = {}
    for ant in range(model.shape[0]):
        out[str(ant)] = model[ant,:]
    print('    Saving %s...'%fout)
    np.savez(fout,**out)


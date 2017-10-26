#!/usr/bin/env python
"""
This script reformats a Nant x Nfreq array in the 
'gains' key of an AbsCal npz file into the dict
required by the hera_cal AbsCal object.
"""

import sys, numpy as np, os

for fname in sys.argv[1:]:
    dout = {}
    fout = os.path.dirname(fname)+'/cal.'+os.path.basename(fname)
    g = np.load(fname)['gains']
    ng = np.isnan(g)
    g[ng] = 1.+0j
    for i in range(g.shape[0]):
        dout[str(i)] = g[i,:]
    print('   Saving %s...'%fout)
    np.savez(fout,**dout)
        

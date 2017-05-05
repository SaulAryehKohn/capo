import numpy as np, matplotlib.pyplot as plt
import sys

omni_npzs = sys.argv[2:]
dest = sys.argv[1]
chisq_stor = np.zeros((len(omni_npzs)*19,203),dtype='float32')

for i,f in enumerate(omni_npzs):
    print '    reading %s'%f
    d = np.load(f)
    try:
        if d['chisq'].shape[0]!=19:
            pad = np.zeros((19-d['chisq'].shape[0],203))
            csq = np.vstack((d['chisq'],pad))
        else:
            csq = d['chisq']
        chisq_stor[i*19:(i+1)*19,:] = csq
    except ValueError:
        print 'file %s has shape %s'%(f,str(d['chisq'].shape))
outname = dest+'/omnichisq.npz'
print 'Saving %s'%outname
np.savez(outname,chisq=chisq_stor)

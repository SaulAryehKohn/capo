import capo, numpy as np, matplotlib.pyplot as plt, sys, os, glob
import aipy

antstr = sys.argv[1]
a1,a2 = map(int,antstr.split('_'))
Ifiles = sorted(glob.glob('*.I.*O'))
Qfiles = sorted(glob.glob('*.Q.*O'))
Ufiles = sorted(glob.glob('*.U.*O'))
Vfiles = sorted(glob.glob('*.V.*O'))

vI,vQ,vU,vV = np.ma.zeros((19*len(Ifiles),203),dtype='complex128'),np.ma.zeros((19*len(Ifiles),203),dtype='complex128'),np.ma.zeros((19*len(Ifiles),203),dtype='complex128'),np.ma.zeros((19*len(Ifiles),203),dtype='complex128')
fI,fQ,fU,fV = np.ma.zeros((19*len(Ifiles),203)),np.ma.zeros((19*len(Ifiles),203)),np.ma.zeros((19*len(Ifiles),203)),np.ma.zeros((19*len(Ifiles),203))

for i,f in enumerate(Ifiles):
    t0,t1=i*19,(i+1)*19
    print '    Reading %s'%f 
    try:
        _,dI,f = capo.arp.get_dict_of_uv_data([f],antstr=antstr,polstr='I')
        vI[t0:t1,:] = dI[(a1,a2)]['I'][:,:]
        fI[t0:t1,:] = np.logical_not(f[(a1,a2)]['I'][:,:]).astype(np.float)
        _,dQ,f = capo.arp.get_dict_of_uv_data([Qfiles[i]],antstr=antstr,polstr='Q')
        vQ[t0:t1,:] = dQ[(a1,a2)]['Q'][:,:]
        fQ[t0:t1,:] = np.logical_not(f[(a1,a2)]['Q'][:,:]).astype(np.float)
        _,dU,f = capo.arp.get_dict_of_uv_data([Ufiles[i]],antstr=antstr,polstr='U')
        vU[t0:t1,:] = dU[(a1,a2)]['U'][:,:]
        fU[t0:t1,:] = np.logical_not(f[(a1,a2)]['U'][:,:]).astype(np.float)
        _,dV,f = capo.arp.get_dict_of_uv_data([Vfiles[i]],antstr=antstr,polstr='V')
        vV[t0:t1,:] = dV[(a1,a2)]['V'][:,:]
        fV[t0:t1,:] = np.logical_not(f[(a1,a2)]['V'][:,:]).astype(np.float)
    except ValueError:
        continue

f,axarr = plt.subplots(1,4,sharex=True,sharey=True)
mx,mn = 0, -4
axarr[0].imshow(np.log10(np.abs(vI)),aspect='auto',interpolation='None',vmax=mx,vmin=mn)
axarr[1].imshow(np.log10(np.abs(vQ)),aspect='auto',interpolation='None',vmax=mx,vmin=mn)
axarr[2].imshow(np.log10(np.abs(vU)),aspect='auto',interpolation='None',vmax=mx,vmin=mn)
axarr[3].imshow(np.log10(np.abs(vV)),aspect='auto',interpolation='None',vmax=mx,vmin=mn)

for i in range(4): axarr[i].set_xlabel('Frequency Bin')
axarr[0].set_ylabel('Integration')
#plt.show()
plt.close()

def delay_transform(d,f,clean=1e-9):
    d = d.filled(0)
    w = aipy.dsp.gen_window(d.shape[-1],window='blackman-harris')
    _dw = np.fft.ifft(d*w)
    _ker= np.fft.ifft(f*w)
    gain = aipy.img.beam_gain(_ker)
    for time in range(_dw.shape[0]):
        _dw[time,:],info = aipy.deconv.clean(_dw[time,:], _ker[time,:], tol=clean)    
        _dw[time,:] += info['res']/gain
    dd = np.fft.fftshift(np.ma.array(_dw),axes=1)
    dd = np.ma.array(dd)
    dd = np.ma.absolute(dd.filled(0))
    dd = np.log10(np.ma.masked_less_equal(dd,0))
    return dd

import matplotlib
f,axarr = plt.subplots(1,4,sharex=True,sharey=True)
mx,mn = 0, -4
axarr[0].imshow(delay_transform(vI,fI),aspect='auto',interpolation='None',vmax=mx,vmin=mn,cmap=matplotlib.cm.get_cmap('jet'))
axarr[1].imshow(delay_transform(vQ,fQ),aspect='auto',interpolation='None',vmax=mx,vmin=mn,cmap=matplotlib.cm.get_cmap('jet'))
axarr[2].imshow(delay_transform(vU,fU),aspect='auto',interpolation='None',vmax=mx,vmin=mn,cmap=matplotlib.cm.get_cmap('jet'))
axarr[3].imshow(delay_transform(vV,fV),aspect='auto',interpolation='None',vmax=mx,vmin=mn,cmap=matplotlib.cm.get_cmap('jet'))

for i in range(4): axarr[i].set_xlabel('Delay Bin')
axarr[0].set_ylabel('Integration')
plt.show()

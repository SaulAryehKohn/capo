#! /usr/bin/env python
"""Compute 2-Dimensional power spectrum from uv files.

Computes the (k// vs t) power spectrum from uv files.
Bootstraps computed over subsets of Baselines in UV files.
"""

import aipy as a
import numpy as n
import pylab as p
import glob
import optparse
import sys
import random
from capo import zsa, oqe, cosmo_units, frf_conv as fringe
import capo

o = optparse.OptionParser()
a.scripting.add_standard_options(o, ant=True, pol=True, chan=True, cal=True)
o.add_option('-b', '--nboot', type='int', default=20,
             help='Number of bootstraps.  Default is 20.')
o.add_option('--plot', action='store_true',
             help='Generate plots')
o.add_option('--window', dest='window', default='blackman-harris',
             help=('Windowing function to use in delay transform. '
                   'Default is blackman-harris. '
                   'Options are: ' + ', '.join(a.dsp.WINDOW_FUNC.keys())))
o.add_option('--sep', default='sep0,1', action='store',
             help='Which separation directory to use for signal loss data.')
o.add_option('-i', '--inject', type='float', default=0.,
             help='EOR injection level.')
o.add_option('--frfeor', action='store_true',
             help='FRF injected eor.')
o.add_option('--doublefrf', action='store_true',
             help='Double FRF injected eor.')
o.add_option('--frf_inttime', type='float', default=1.0,
             help='Noise equivalent bandwidth of fringe rate filter.')
o.add_option('--output', type='string', default='',
             help='Output directory for pspec_boot files (default "")')
o.add_option('--weight', type='string', default='L^-1',
             help=('Choice for MC normalization '
                   'Options available L^-1 F^-1/2 I F^-1'))
o.add_option('--rmbls', dest='rmbls', type='string',
             help=('List of baselines (ex:1_4,2_33) '
                   'to remove from the power spectrum analysis.'))
opts, args = o.parse_args(sys.argv[1:])

# Basic parameters
random.seed(0)
POL = opts.pol
LST_STATS = False
DELAY = False
NGPS = 5  # number of groups to break the random sampled bls into
PLOT = opts.plot
INJECT_SIG = opts.inject

try:
    rmbls = []
    rmbls_list = opts.rmbls.split(',')
    for bl in rmbls_list:
        i, j = bl.split('_')
        rmbls.append(a.miriad.ij2bl(int(i), int(j)))
    print 'Removing baselines:', rmbls
    # rmbls = map(int, opts.rmbls.split(','))
except:
    rmbls = []


# FUNCTIONS #


def frf(shape):  # FRF NOISE
    """Generate White Noise and Apply FRF."""
    shape = shape[1]*2, shape[0]  # (2*times,freqs)
    dij = oqe.noise(size=shape)
    wij = n.ones(shape, dtype=bool)  # XXX flags are all true (times,freqs)
    # dij and wij are (times,freqs)
    _d, _w, _, _ = fringe.apply_frf(aa, dij, wij, ij[0], ij[1],
                                    pol=POL, bins=bins, firs=fir)
    if opts.doublefrf == True:
        _d, _w, _, _ = fringe.apply_frf(aa, _d, wij, ij[0], ij[1],
                                            pol=POL, bins=bins, firs=fir)
    _d = n.transpose(_d)
    _d = _d[:, shape[0]/4:shape[0]/2+shape[0]/4]
    return _d


def make_PS(keys,ds,grouping=True): 
    """Use OQE formalism to generate power spectrum 
        using covariance and identity weightings."""
    if grouping == True:
        newkeys, dsC = ds.group_data(keys, gps)
        newkeys, dsI = ds.group_data(keys, gps, use_cov=False)
    else:  # no groups (slower)
        newkeys = [random.choice(keys) for key in keys]
        # sample w/replacement for bootstrapping
        dsI, dsC = ds, ds  # identity and covariance case dataset is the same
    FI = n.zeros((nchan, nchan), dtype=n.complex)
    FC = n.zeros((nchan, nchan), dtype=n.complex)
    qI = n.zeros((nchan, nlst), dtype=n.complex)
    qC = n.zeros((nchan, nlst), dtype=n.complex)
    for k, key1 in enumerate(newkeys):
        # print '   ',k+1,'/',len(keys)
        for key2 in newkeys[k:]:
            if key1[0] == key2[0] or key1[1] == key2[1]:
                continue  # don't do even w/even or bl w/same bl
            else:
                FC += dsC.get_F(key1, key2, cov_flagging=False)
                FI += dsI.get_F(key1, key2, use_cov=False, cov_flagging=False)
                qC += dsC.q_hat(key1, key2, cov_flagging=False)
                qI += dsI.q_hat(key1, key2, use_cov=False, cov_flagging=False)
    MC, WC = dsC.get_MW(FC, mode=opts.weight)  # Cholesky decomposition
    MI, WI = dsI.get_MW(FI, mode='I')
    pC = dsC.p_hat(MC, qC, scalar=scalar)
    pI = dsI.p_hat(MI, qI, scalar=scalar)
    if PLOT:
        p.subplot(121)
        capo.arp.waterfall(FC, drng=4)
        p.title('FC')
        p.subplot(122)
        capo.arp.waterfall(FI, drng=4)
        p.title('FI')
        p.show()
    if PLOT:
        p.subplot(411)
        capo.arp.waterfall(qC, mode='real')
        p.colorbar(shrink=.5)
        p.title('qC')
        p.subplot(412)
        capo.arp.waterfall(pC, mode='real')
        p.colorbar(shrink=.5)
        p.title('pC')
        p.subplot(413)
        capo.arp.waterfall(qI, mode='real')
        p.colorbar(shrink=.5)
        p.title('qI')
        p.subplot(414)
        capo.arp.waterfall(pI, mode='real')
        p.colorbar(shrink=.5)
        p.title('pI')
        p.show()
    if PLOT:
        p.plot(kpl, n.average(pC.real, axis=1), 'b.-', label='pC')
        p.plot(kpl, n.average(pI.real, axis=1), 'k.-', label='pI')
        p.legend()
        p.show()
    return pC,pI


def cov(m):
    """Compute Complex Covariance.

    Because numpy.cov is stupid and casts as float.
    """
    X = n.array(m, ndmin=2, dtype=n.complex)
    X -= X.mean(axis=1)[(slice(None), n.newaxis)]
    N = X.shape[1]
    fact = float(N - 1)  # normalization
    return (n.dot(X, X.T.conj()) / fact).squeeze()


def get_Q(mode, n_k):
    """Generate Fourier Transform Matrix.

    Encodes the fourier transform from freq to delay
    """
    if not DELAY:
        _m = n.zeros((n_k,), dtype=n.complex)
        _m[mode] = 1.  # delta function at specific delay mode
        m = n.fft.fft(n.fft.ifftshift(_m)) * a.dsp.gen_window(nchan, WINDOW)
        # FFT it to go to freq
        Q = n.einsum('i,j', m, m.conj())  # dot it with its conjugate
        return Q
    else:
        # XXX need to have this depend on window
        Q = n.zeros_like(C)
        Q[mode, mode] = 1
        return Q


# Read even&odd data
if 'even' in args[0] or 'odd' in args[0]:
    dsets = {
            'even': [x for x in args if 'even' in x],
            'odd': [x for x in args if 'odd' in x]
            }
else:
    dsets = {'even': args, 'odd': args}
print dsets

# Get uv file info
WINDOW = opts.window
uv = a.miriad.UV(dsets.values()[0][0])
freqs = a.cal.get_freqs(uv['sdf'], uv['sfreq'], uv['nchan'])
sdf = uv['sdf']
chans = a.scripting.parse_chans(opts.chan, uv['nchan'])
inttime = uv['inttime']
# try to take the frf_inttime from the file
# for old filtered files, need to use parameter still
try:
    frf_inttime = uv['FRF_NEBW']
except:
    frf_inttime = opts.frf_inttime
print 'inttime:', inttime
print 'frf_inttime:', frf_inttime
afreqs = freqs.take(chans)
nchan = chans.size
fq = n.average(afreqs)
z = capo.pspec.f2z(fq)
aa = a.cal.get_aa(opts.cal, afreqs)
bls, conj = capo.red.group_redundant_bls(aa.ant_layout)
sep2ij, blconj, bl2sep = capo.zsa.grid2ij(aa.ant_layout)
jy2T = capo.pspec.jy2T(afreqs)
window = a.dsp.gen_window(nchan, WINDOW)
if not WINDOW == 'none':
    window.shape = (nchan, 1)

# B = sdf * afreqs.size / capo.pfb.NOISE_EQUIV_BW[WINDOW]
# this is wrong if we aren't inverting
# the window post delay transform
# (or at least dividing out by the gain of the window)
# For windowed data, the FFT divides out by the full bandwidth, B, which is
# then squared. Proper normalization is to multiply by
# B**2 / (B / NoiseEqBand) = B * NoiseEqBand
# XXX NEED TO FIGURE OUT BW NORMALIZATION
B = sdf * afreqs.size * capo.pfb.NOISE_EQUIV_BW[WINDOW]  # proper normalization
etas = n.fft.fftshift(capo.pspec.f2eta(afreqs))
# create etas (fourier dual to frequency)
kpl = etas * capo.pspec.dk_deta(z)
if True:
    bm = n.polyval(capo.pspec.DEFAULT_BEAM_POLY, fq) * 2.35
    # correction for beam^2
    scalar = capo.pspec.X2Y(z) * bm * B
else:
    scalar = 1
if not DELAY:
    # XXX this is a hack
    if WINDOW == 'hamming':
        scalar /= 3.67
    elif WINDOW == 'blackman-harris':
        scalar /= 5.72
print 'Freq:', fq
print 'z:', z
print 'B:', B
print 'scalar:', scalar
sys.stdout.flush()

# Acquire data
data_dict_v = {}
flg_dict = {}
conj_dict = {}
antstr = 'cross'
_, blconj, _ = zsa.grid2ij(aa.ant_layout)
days = dsets.keys()
lsts, data, flgs = {}, {}, {}
for k in days:
    lsts[k], data[k], flgs[k] = capo.miriad.read_files(dsets[k],
                                                       antstr=antstr,
                                                       polstr=POL,
                                                       verbose=True)
    lsts[k] = n.array(lsts[k]['lsts'])
    if rmbls:
        print "Removing baselines:",
    for bl in rmbls:
        data[k].pop(a.miriad.bl2ij(bl), None)
        flgs[k].pop(a.miriad.bl2ij(bl), None)
        print bl,
    print ''
    for bl in data[k]:
        d = n.array(data[k][bl][POL])[:, chans] * jy2T
        # extract frequency range
        flg = n.array(flgs[k][bl][POL])[:, chans]
        key = (k, bl, POL)
        data_dict_v[key] = d
        flg_dict[key] = n.logical_not(flg)
        conj_dict[key[1]] = conj[bl]
keys = data_dict_v.keys()
bls_master = []
for key in keys:  # populate list of baselines
    if key[0] == keys[0][0]:
        bls_master.append(key[1])
print 'Baselines:', len(bls_master)

# Align dataset
inds = oqe.lst_align(lsts)
data_dict_v, flg_dict, lsts = oqe.lst_align_data(inds, dsets=data_dict_v,
                                               wgts=flg_dict, lsts=lsts)
# the lsts given is a dictionary with 'even','odd', etc.
# but the lsts returned is one array

# Prep FRF Stuff
nlst = data_dict_v[keys[0]].shape[0]
ij = bls_master[0]  # ij = (1,4)
if blconj[a.miriad.ij2bl(ij[0], ij[1])]:
    # makes sure FRP will be the same whether bl is a conjugated one or not
    if ij[0] < ij[1]:
        temp = (ij[1], ij[0])
        ij = temp
sep_type = bl2sep[a.miriad.ij2bl(ij[0], ij[1])]
# convert uvw in light-nanoseconds to m, (cosmo_units.c in m/s)
uvw = aa.get_baseline(ij[0], ij[1], src='z') * cosmo_units.c * 1e-9
bins = fringe.gen_frbins(inttime)
frp, bins = fringe.aa_to_fr_profile(aa, ij, len(afreqs)/2, bins=bins)
timebins, firs = fringe.frp_to_firs(frp, bins, aa.get_freqs(),
                                    fq0=aa.get_freqs()[len(afreqs)/2])
fir = {(ij[0], ij[1], POL): firs}

# Make noise dataset
data_dict_n = {}
for key in data_dict_v:
    data_dict_n[key] = frf((len(chans),nlst)).T

# Set data
dsv = oqe.DataSet() # just data
dsv.set_data(dsets=data_dict_v, conj=conj_dict, wgts=flg_dict)
dsn = oqe.DataSet() #just noise
dsn.set_data(dsets=data_dict_n, conj=conj_dict, wgts=flg_dict)

# Get some statistics
if LST_STATS:
    # collect some metadata from the lst binning process
    cnt, var = {}, {}
    for filename in dsets.values()[0]:
        print 'Reading', filename
        uv = a.miriad.UV(filename)
        a.scripting.uv_selector(uv, '64_49', POL)  # XXX
        for (uvw, t, (i, j)), d, f in uv.all(raw=True):
            bl = '%d,%d,%d' % (i, j, uv['pol'])
            cnt[bl] = cnt.get(bl, []) + [uv['cnt']]
            var[bl] = var.get(bl, []) + [uv['var']]
    cnt = n.array(cnt.values()[0])  # all baselines should be the same
    var = n.array(var.values()[0])  # all baselines should be the same
else:
    cnt, var = n.ones_like(lsts), n.ones_like(lsts)

if PLOT and False:
    for key in keys:
        p.subplot(311)
        capo.arp.waterfall(dsv.x[key], mode='real')
        p.colorbar()
        p.title('Data x')
        p.subplot(323)
        capo.arp.waterfall(dsv.C(key))
        p.colorbar()
        p.title('C')
        # p.subplot(324); p.plot(n.einsum('ij,jk',n.diag(S),V).T.real)
        p.subplot(313)
        capo.arp.waterfall(n.dot(dsv.iC(key), dsv.x[key]),
                           mode='real')  # ,drng=6000,mx=3000)
        p.colorbar()
        p.title('C^-1 x')
        p.suptitle(key)
        p.tight_layout()
        p.show()

# Bootstrapping
for boot in xrange(opts.nboot):
    print 'Bootstrap %d / %d' % (boot+1, opts.nboot) 

    # Make groups 
    gps = dsv.gen_gps(bls_master, ngps=NGPS)

    # Only data
    print '   Getting pCv, pIv'
    pCv, pIv = make_PS(keys,dsv,grouping=True)
      
    # Only noise
    print '   Getting pCn, pIn'
    pCn, pIn = make_PS(keys,dsn,grouping=True)

    # Loop to calculate pCr & pIr (data+eor), and pCe & pIe (eor) #
    if INJECT_SIG > 0.:  # Create a fake EoR signal to inject
        print '     INJECTING SIMULATED SIGNAL @ LEVEL', INJECT_SIG
        if opts.frfeor:
            eor = (frf((nchan, nlst)) * INJECT_SIG).T
            # create FRF-ered noise
        else:
            eor = (oqe.noise((nchan, nlst)) * INJECT_SIG).T
        data_dict_r = {}
        data_dict_e = {}
        for key in data_dict_v:
            if conj_dict[key[1]] is True:
                eorinject = n.conj(eor.copy())
                # conjugate eor for certain baselines
            else:
                eorinject = eor.copy()
            data_dict_r[key] = data_dict_v[key].copy() + eorinject
            # add injected signal to data
            data_dict_e[key] = eorinject

    # Set data
    dsr = oqe.DataSet()  # data + eor
    dsr.set_data(dsets=data_dict_r, conj=conj_dict, wgts=flg_dict)
    dse = oqe.DataSet()  # just eor
    dse.set_data(dsets=data_dict_e, conj=conj_dict, wgts=flg_dict)
    
    print '   Getting pCr, pIr'
    pCr,pIr = make_PS(keys,dsr,grouping=True)
    print '   Getting pCe, pIe'
    pCe,pIe = make_PS(keys,dse,grouping=True)
   
    print '   pCv=', n.median(pCv.real), 'pIv=', n.median(pIv.real)
    print '   pIe=', n.median(pIe.real), 'pCr=', n.median(pCr.real),
    print ' pIe/pCr=', n.median(pIe.real)/n.median(pCr.real)
    print '   pCn=', n.median(pCn.real), 'pIn=', n.median(pIn.real)
    
    if PLOT:
        p.plot(kpl, n.average(pCr.real, axis=1), 'b.-')
        p.plot(kpl, n.average(pIr.real, axis=1), 'k.-')
        p.title('Data + EoR')
        p.show()

    # Save Output
    if len(opts.output) > 0:
        outpath = opts.output + '/pspec_bootsigloss%04d.npz' % boot
    else:
        outpath = 'pspec_bootsigloss%04d.npz' % boot
    print '   Writing ' + outpath
    n.savez(outpath, kpl=kpl, scalar=scalar, lsts=lsts,
            pCr=pCr, pIr=pIr, pCv=pCv, pIv=pIv, pCe=pCe, pIe=pIe,
            err=1./cnt, var=var, sep=sep_type, uvw=uvw,
            frf_inttime=frf_inttime, inttime=inttime,
            inject_level=INJECT_SIG, freq=fq, afreqs=afreqs,
            cmd=' '.join(sys.argv))

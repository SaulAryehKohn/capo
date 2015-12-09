#! /usr/bin/env python
import aipy as a, numpy as n, capo as C, pylab as p

#@p.ion()
#fqs = n.linspace(.1,.2,203)
fq = .15
bl1, bl2 = (0,26),(0,26)
N = 2
#Peakheight = {26_26: 0.192, 26_38: 0.082}

aa = a.cal.get_aa('psa6240_v003', n.array([fq]))
#h = a.healpix.HealpixMap(nside=128)
h = a.healpix.HealpixMap(nside=64)
tx,ty,tz = h.px2crd(n.arange(h.map.size), ncrd=3)
bl1x, bl1y, bl1z = aa.get_baseline(bl1[0],bl1[1],'z')
bl2x, bl2y, bl2z = aa.get_baseline(bl2[0],bl2[1],'z')
bl1_prj = tx*bl1x + ty*bl1y + tz*bl1z
bl2_prj = tx*bl2x + ty*bl2y + tz*bl2z
fng1 = n.exp(-2j*n.pi*bl1_prj*fq)
fng2 = n.exp(-2j*n.pi*bl2_prj*fq)
bm = aa[0].bm_response((tx,ty,tz),pol='x')[0]**2
bm = n.where(tz > 0, bm, 0); bm /= bm.sum()
bm_fng1 = bm * fng1
bm_fng2 = bm * fng2

#if True:
#    img = a.img.Img(200,.5)
#    tx,ty,tz = img.get_top((200,200))
#    SH = tx.shape
top = n.array([tx,ty,tz], dtype=tx.dtype)
#top.shape = (3,-1)
#import IPython; IPython.embed()
#for lst in n.arange(0,2*n.pi,2*n.pi/a.const.sidereal_day*42.9):
#plt = None
corr = []
TT = n.arange(2455700,2455701,1/a.const.sidereal_day*42.9*2) #*5 for speed
NORM = float(TT.size)/1000.
for i in xrange(N):
    print i
    sky = n.random.normal(size=h.map.size)
    h.map = sky # assume sky is in eq coord
    vis1,vis2 = [],[]
    #aa.set_jultime(2455701)
    #m = n.linalg.inv(aa.eq2top_m)
    #ex,ey,ez = n.dot(m, top)
    #ky_prj1 = h[ex,ey,ez]
    for jd in TT:
        # convert tx,ty,tz to ex,ey,ez (time dependent)
        #print jd
        aa.set_jultime(jd)
        m = n.linalg.inv(aa.eq2top_m)
        ex,ey,ez = n.dot(m, top)
        sky_prj = h[ex,ey,ez]
        #sky_prj.shape = SH
        #if plt is None: plt = p.imshow(sky_prj, vmax=2, vmin=-2)
        #else:
        #    plt.set_data(sky_prj)
        #    p.draw()
        vis1.append(n.sum(sky_prj * bm_fng1))
        vis2.append(n.sum(sky_prj * bm_fng2))
        #note top is a dome already, so no need for the jacobian factor
    #just built data for the tw
    # da2
    vis1,vis2 = n.array(vis1), n.array(vis2)

    _vis1,_vis2 = n.fft.fft(vis1), n.fft.fft(vis2)
    #print _vis1.shape
    corr.append(n.fft.ifftshift(n.fft.ifft(_vis2*n.conj(_vis1))))
    #p.plot(n.abs(corr[i]))
corr = n.array(corr)
print corr.shape
#p.show()

corr = corr/NORM
#cuedict = {'26_23':0.125, '26_38': 0.042, '26_50': 0.083,'26_26':0., '50_57':0.122}
cuedict = {'26_26':0.,'26_38': 0.032557,'26_50':0.073557,'13_32':0.030557,'13_14':0.066557,'50_59':0.071557}
try: ver = cuedict[str(bl1[1])+'_'+str(bl2[1])]
except(KeyError): ver = 0.
print "Peak height: ", n.max(n.abs(n.mean(corr,axis=0)))
p.figure()
p.subplot(211)
#p.plot(TT-2455700.5,n.abs(n.mean(corr,axis=0)))
p.plot(TT-2455700.5,n.real(n.mean(corr,axis=0)))
p.plot(TT-2455700.5,n.imag(n.mean(corr,axis=0)))
p.axvline(ver,color='k',alpha=0.5,linewidth=3)
p.grid()
p.subplot(212)
#p.plot(TT-2455700.5,n.abs(n.mean(corr,axis=0)))
p.plot(TT-2455700.5,n.abs(n.mean(corr,axis=0)))
p.axvline(ver,color='k',alpha=0.5,linewidth=3)
p.grid()
p.show()

#import IPython; IPython.embed()

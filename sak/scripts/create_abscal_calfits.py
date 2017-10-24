#!/usr/bin/env python
"""
Create a calfits file for absolute calibration of a given MIRIAD file.
"""

import sys,os,optparse
from hera_cal.cal_formats import AbsCal

o = optparse.OptionParser()
o.add_option('-p',dest='pol',default=None,help='polarization to calibrate')
o.add_option('--miriad',dest='miriad_file',default=None,help='miriad file to calibrate')
o.add_option('--abscal_list',dest='abscal_list',default=None,help='comma-separated list of abscal npzs')
o.add_option('--cal_scheme',dest='cal_scheme',default='divide',help='multiply/divide by gains in abscal npzs')
o.add_option('--calpath',dest='calpath',default=None,help='path to save calibraiton solutions to. Will save to /calpath/miriad_filename.calfits')
opts,args = o.parse_args(sys.argv[1:])
print opts
assert opts.pol != None
assert opts.miriad_file != None
assert opts.abscal_list != None
assert opts.calpath !=None
abscal_list = opts.abscal_list.split(',')
assert len(set(opts.pol)) == len(abscal_list)

ac = AbsCal(opts.miriad_file, abscal_list, opts.pol, opts.cal_scheme, append2hist=' '.join(sys.argv))
outname=opts.calpath+'/'+os.path.basename(opts.miriad_file)+'.calfits'
print('   Writing %s...'%outname)
ac.write_calfits(outname) #XXX NB not clobbering

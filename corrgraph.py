#!/usr/bin/env python

# Fiddling with correlation to find the q60 fiducial
# davep 4-Dec-2013

import sys
import os
import numpy as np
import matplotlib.pyplot as plt
import scipy.signal

import fiducial
import imtools

image_files = [ 
    "br_q60_rgb.tif",
    "img002.tif",
    "j4580-q60.tif",
    "lp_300rgb_q60.jpg",
    "q60-tsu-27sep2009.png",
    "q60_epson_4490.tiff",
#    "q60_mid.tif",
    "q60_rgb_hp_officejet_3680.tiff",
#    "q60_s3_nopie_rgb.tif",
#    "q60_s3_rgb.tif",
    "q60_s3_rgb_ccw.tif",
    "q60_s3_rgb_straight.tif",
    "q60_top.tif",
    "q60br_rgb.tif",
    "tsu_q60_26jan2010.tiff",
#    "tsu_q60_nopie.png",
#    "tsu_q60_nopie.tif",
    "wh_q60_smooth.png",
]

def plot_fid(ndata,label): 
    fidlist = fiducial.find_fiducials_correlate(ndata)

    corr = [ fid["corr_score"] for fid in fidlist ]
    plt.plot(corr)
    plt.plot(np.ones(len(corr))*np.mean(corr))
    corr_filt = scipy.signal.wiener(np.asarray(corr,dtype="float"),55)
    plt.plot(corr_filt)

    z = corr_filt - np.mean(corr)
    plt.plot(np.clip(z,0,np.max(z)),label=label)

def plot_fid_file(infilename):
    ndata = imtools.load_image(infilename,mode="L")
    plot_fid(ndata,infilename)

def main(): 
    plt.clf()
    plt.grid()

    if len(sys.argv) > 0 : 
        files = sys.argv[1:]
    else :
        files = [ os.path.join("images",f) for f in image_files ]

    for infilename in files : 
        plot_fid_file(infilename)

    plt.legend()

    plt.show()

if __name__=="__main__":
    main()


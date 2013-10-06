#!python

# 
# Split from q60.py on 15-Jun
#
# davep 15-Jun-2013

import sys
import numpy as np

import peaks
import imtools
import filenames

mkoutfilename = None

def find_gray_midpoint( ndata ) : 

    # The incoming data is grayscale.  Other than white, the gray background of
    # the q60 is the majority color. Because the gray level might be different
    # depending in how the q60 was scanned (PIE, noPIE, different sensors,
    # different IQ settings, etc), find the majority gray value. That 
    #

    peaks_list, pixel_counts = peaks.find_histogram_peaks(ndata)
    print "peaks=",peaks_list
    print "counts=",pixel_counts

    # highest should be white
    # 2nd highest should be the q60's background gray
    white_idx = np.argmax(pixel_counts)
    print "white_idx=",white_idx

    pixel_counts.pop(white_idx)
    gray_idx = np.argmax(pixel_counts)
    print "gray_idx=",gray_idx

    return peaks_list[gray_idx]

def calc_gray_boundaries(ndata) :

    gray_midpoint = find_gray_midpoint( ndata )

    gray_low = gray_midpoint - 10
    gray_high = gray_midpoint + 10

    print "gray_low={0} gray_high={1}".format(gray_low,gray_high)

    return gray_low, gray_high

def gray_boundaries( ndata, gray_low, gray_high ) :

    gray1 = np.where(ndata>gray_low,ndata,0)

    gray2 = np.where(gray1<gray_high,gray1,0)

    if mkoutfilename : 
        imtools.clip_and_save( gray1, mkoutfilename("gray1") )
        imtools.clip_and_save( gray2, mkoutfilename("gray2") )

    nz = np.nonzero( gray2 )
    return nz

def main() : 
    infilename = sys.argv[1]

    global mkoutfilename
    mkoutfilename = filenames.get_outfilename_maker( infilename )

    # tell peaks.py how to make test/debug output filenames
    peaks.mkoutfilename = mkoutfilename

    ndata = imtools.load_image( infilename, mode="L", dtype="uint8" )

    gray_low, gray_high = calc_gray_boundaries( ndata )
    gray_bounds = gray_boundaries( ndata, gray_low, gray_high )

if __name__ == '__main__' : 
    main()


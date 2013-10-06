#!python

# Convert an RGB to gray with a few different formulas
# davep 05-June-2013

import sys
import numpy as np

# 1/3, 1/3, 1/3
#rgb_to_gray = ( .33, .33, .33 )

# http://stackoverflow.com/questions/687261/converting-rgb-to-grayscale-intensity 

# https://en.wikipedia.org/wiki/Grayscale
# "In the YUV and YIQ models used by PAL and NTSC, the luma (Y') component
# is computed as"
rgb_to_gray = ( .299, .587, .114 )

# https://en.wikipedia.org/wiki/Grayscale
# "The model used for HDTV developed by the ATSC uses different color
# coefficients, computing the luma component as"
#rgb_to_gray = (.2126, .7152, .0722 )
    
def togray(ndata): 
    # assumes incoming is color
    gray = ndata[:,:,0] * rgb_to_gray[0] +\
           ndata[:,:,1] * rgb_to_gray[1] +\
           ndata[:,:,2] * rgb_to_gray[2] 

    return gray

def main(): 
    import imtools
    from basename import get_basename

    infilename = sys.argv[1]
    basename = get_basename(infilename)
    outfilename = "{0}_gray.tif".format(basename)

    ndata = imtools.load_image(infilename,dtype="uint8")

    gray = togray(ndata)

    imtools.clip_and_save(gray,outfilename)

if __name__=='__main__' :
    main()


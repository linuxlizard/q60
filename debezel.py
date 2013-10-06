#!python

import sys
import numpy as np
#import matplotlib.pyplot as plt
import scipy.ndimage.filters

import imtools
from basename import get_basename
import rgbtogray

def find_bezel( ndata ):
    gray = rgbtogray.togray(ndata)[0:50,0:50]
    gray = scipy.ndimage.filters.median_filter( gray, size=(5,5) )
    imtools.save_image(gray,"gray.tif")

    print ndata.shape
    numrows = ndata.shape[0]
    numcols = ndata.shape[1]

    print "rows={0} cols={1}".format(numrows,numcols)

    # Do we have a narrow band of black followed by white?
    #
    # look for bezel along the top
    col = 50

    pixel_diff = 10

    # search for bezel vertically
    diffs = np.diff( gray[:,-1] )
    print diffs
    print diffs.min(), diffs.max(), np.mean(diffs), np.median(diffs)

    bezel_row = 0
    for row,d in enumerate(diffs) : 
        if d > pixel_diff :
            bezel_row = row

    # search for bezel horizonstally
    diffs = np.diff( gray[-1,:] )
    print diffs
    print diffs.min(), diffs.max(), np.mean(diffs), np.median(diffs)

    bezel_col = 0
    for col,d in enumerate(diffs) : 
        if d > 10 :
            bezel_col = col

#    plt.gray()
#    plt.grid()
#    plt.plot(d)
#    plt.show()

    # best guess, no bezel found
    return bezel_row, bezel_col 
    
def debezel( infilename, outfilename ) : 
    
    ndata = imtools.load_image(infilename,dtype="uint8")
    print ndata.shape

    bezel_edges = find_bezel( ndata )

    if bezel_edges is None : 
        # no bezel edges found
        return False

    bezel_row,bezel_col = bezel_edges

    print "row={0} col={1}".format(bezel_row,bezel_col)

    ndata2 = ndata[bezel_row:,bezel_col:,:]

    imtools.clip_and_save(ndata2,outfilename)
    
    return True

def main() :
    infilename = sys.argv[1]
    basename = get_basename(infilename)
    outfilename = "{0}_debezel.tif".format(basename)

    debezel_done = debezel( infilename, outfilename ) 

if __name__=='__main__' :
    main()


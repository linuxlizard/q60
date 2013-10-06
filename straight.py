#!python

import sys
import numpy as np
import scipy.ndimage.filters
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg

import imtools
from basename import get_basename

mkoutfilename = None

def test_corner_samples( upper_left, upper_right, lower_left, lower_right ) : 
    pass

def make_montage( upper_left, upper_right, lower_left, lower_right ) : 
    sample_size = upper_left.shape[0]

    # Make a big image with all four samples. Image has a boundary of black
    # around the samples.
    montage = np.zeros( (sample_size*2+6,sample_size*2+6) )

    # ugly, ugly, ugly
    montage[ 2:sample_size+2, 2:sample_size+2 ] = upper_left
    montage[ 2+sample_size+2:2+sample_size+2+sample_size, 2:sample_size+2 ] = lower_left
    montage[ 2:sample_size+2 , 2+sample_size+2:2+sample_size+2+sample_size] = upper_right
    montage[ 2+sample_size+2:2+sample_size+2+sample_size, 2+sample_size+2:2+sample_size+2+sample_size ] = lower_right

    if mkoutfilename:
        imtools.clip_and_save(montage,mkoutfilename("mont"))

    fig = Figure()

    # make four histograms on single plot to match our montage image
    for pos,sample in zip((221,222,223,224),(upper_left,upper_right,lower_left,lower_right)):
        ax = fig.add_subplot(pos)
        hist,bins = np.histogram(sample,bins=256,range=(0,255))
        ax.grid()
        ax.plot(hist)
    
    if mkoutfilename:
        outfilename = mkoutfilename( "mont_hist" ).replace(".tif",".png")
        canvas = FigureCanvasAgg(fig)
        canvas.print_figure(outfilename)
        print "wrote", outfilename

def straightness_test( ndata, gray_low, gray_high, sample_size=60 ) :
    
    # Is the ratio of the image about what the q60 card should be? If we're way
    # off, no reason to go any further.
    print ndata.shape
    # q60 ~= 3x5 ?? 
    aspect_ratio = float(ndata.shape[0])/ndata.shape[1]
    print "aspect_ratio={0}".format(aspect_ratio)
    int_aspect_ratio = int(round(aspect_ratio*100))
    print int_aspect_ratio
    if int_aspect_ratio < 70 or int_aspect_ratio > 75 :
        errmsg = "aspect_ratio={0} out of range".format(aspect_ratio)
        print >>sys.stderr, errmsg
        assert 0
        return False

    # Grab a square sample from all four edges. If those samples look pretty
    # close to the Q60's corners, then let's call it straight enough.
#    sample_size = 20
    upper_left = ndata[ 0:sample_size, 0:sample_size ]
    lower_left  = ndata[ -sample_size:, 0:sample_size ]
    upper_right = ndata[ 0:sample_size, -sample_size: ]
    lower_right = ndata[ -sample_size:, -sample_size: ]

    # save all the slices to an image
    make_montage( upper_left, upper_right, lower_left, lower_right ) 

    count = 0

    for name,sample in zip(("ul","ur","lr","ll"),(upper_left,upper_right,lower_left,lower_right)):
        print "{0} min={1} max={2} median={3} stddev={4}".format(
            name,np.min(sample),np.max(sample),np.median(sample),np.std(sample))

        # if 3 of the four corners are 90(ish)% gray, call it good
        grayish_mask = np.logical_and( np.less( sample, gray_high ), np.greater( sample, gray_low ) )
        grayish = np.extract( grayish_mask, sample )

        percent_gray = (float(grayish.size)/sample.size)*100

        print "pixels={0} grayish={1} {2}".format( sample.size, grayish.size, percent_gray )

        if percent_gray >= 90 : 
            count += 1
        
        # save the samples while test/debugging
        np.save(name+".npy",sample)

    return count >= 3
 
def main() : 
    infilename = sys.argv[1]
    ndata = imtools.load_image(infilename,dtype="uint8",mode="L")

    # aggressive median filter to smooth out as much noise as possible
    fdata = scipy.ndimage.filters.median_filter( ndata, size=(5,5) )

    basename = get_basename(infilename)
    global mkoutfilename
    mkoutfilename = lambda s : "{0}_{1}.tif".format(basename,s)

    is_straight = straightness_test( fdata, 126, 146, 60 )
    if is_straight : 
        print "is straight enough"
    else :
        print "is NOT straight enough"

if __name__=='__main__' :
    main()


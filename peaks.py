#!python

# Originally part of my auto white point code. Moved to own module.
# Find peaks in histogram. 
#
# davep 03-June-2013

import sys
import numpy as np
import scipy.ndimage.filters
import Image
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
import savitzky_golay

import imtools
#import histo

mkoutfilename = None

def win_less( window, value ) : 
    # all values in window are less than value
    for p in window : 
        if p > value :
            return False
    return True

def win_greater( window, value ) : 
    # all values in window are greater than value
    for p in window : 
        if p < value :
            return False
    return True

def find_peaks( data ) : 
    ndata = np.asarray( data ) 
    
    diffs = np.diff( ndata )

    # look for zero crossings in a window
    peaks = []
    window_size = 21
    mid = 10
    cnt = window_size/2
    while cnt < len(data)-window_size/2 : 
        window = data[cnt-window_size/2 : cnt+window_size/2]

#        print "window=",window
#        print "mid=",window[mid]

        # left size of the window < midpoint?
        if not win_less(window[:mid],window[mid]) :
            cnt += 1
#            print "no match <"
#            print window
            continue
            
        # right side of the window > midpoint?
        if not win_less(window[mid+1:],window[mid]) :
            cnt += 1
#            print "no match >"
#            print window
            continue

        peaks.append(cnt)
        cnt += 1

#        sys.exit(0)

    return peaks


def save_gray_histogram_img( hist, ndata, zeros_list) : 
    if not mkoutfilename : 
        return

    fig = Figure()
    ax = fig.add_subplot(111)
    ax.grid()

    # plot the original histogram
    ax.plot(hist,".-")
    
    # plot the SG smoothed derivative if passed (this same function used with
    # other peak finding code that doesn't pass the SVG)
    if ndata is not None: 
        ax.plot(ndata,".-")

    # plot the peaks
    x = zeros_list
#    y = [ smoothed[p] for p in zeros_list ]
    y = [ hist[p] for p in zeros_list ]
    ax.plot( x, y, 'rx' )

    # my mkoutfilename lambda defaults to .tif extension 
    outfilename = mkoutfilename( "hist" ).replace(".tif",".pdf")
    canvas = FigureCanvasAgg(fig)
    canvas.print_figure(outfilename)
    print "wrote", outfilename

def find_zeros( ndata ) :
    # find locations where data crosses zero
    zeros_list = []
    for i in range(len(ndata)-1):
        if ndata[i]==0 or (ndata[i] < 0 and ndata[i+1] > 0) \
                       or (ndata[i] > 0 and ndata[i+1] < 0) :
            zeros_list.append( i )

    return zeros_list

def find_highest_peaks( zeros_list, ndata, num=10 ) : 
    # Find all the peaks. Sort. Take 'n' highest.
    peaks = []
    for z in zeros_list : 
        peaks.append( (z,ndata[z]) )

    peaks.sort( lambda a,b : cmp( a[1],b[1] ) )
#    print peaks
#    print peaks[-num:]

    # return the indices with the highest values 
    highest_peaks = [ p[0] for p in peaks[-num:] ]

#    print highest_peaks 

    # We could be on either side of the peak or at the peak.  Adjust our
    # location to exactly the highest peak
    for i in range(len(highest_peaks)):
        p = highest_peaks[i]
        if ndata[p-1] > ndata[p] :
            highest_peaks[i] = p-1
        elif ndata[p+1] > ndata[p] : 
            highest_peaks[i] = p+1
    
#    print highest_peaks 

    return highest_peaks
        
def simple_highest_peaks( ndata, hist, num_peaks ) : 
    argsorted = np.argsort(hist)

    print hist
    print argsorted
    print hist[argsorted]
    peaks_list = []

    riter = reversed(argsorted)
    for n in riter : 
        print n
        if hist[n] < hist[n+1] or hist[n] < hist[n-1] : 
            continue
        print "keep",n
        peaks_list.append(n)
        if len(peaks_list) >= num_peaks : 
            break

    print peaks_list
    return peaks_list
           
#    peaks = argsorted[-num_peaks:]


def find_histogram_peaks( ndata, num_peaks=5 ) : 

    hist,bins = np.histogram(ndata,bins=256)
    np.save("hist.npy",hist)

    # zero pad the end so clipped white will show up as a peak
    tmp = np.zeros(257)
    tmp[0:256] = hist
    hist = tmp
    del tmp

    if 1 : 
        # smoothed 1st derivative of the signal
        svg = savitzky_golay.savitzky_golay( hist, 21, 5, 1 )
        np.save("svg.npy",svg)

        peaks_list = find_peaks( svg )

        # look for zero crossing
        zeros_list = find_zeros( svg )
        print "zeros_list=",zeros_list

        highest_peaks = find_highest_peaks( zeros_list, hist, num_peaks )
        print "highest_peaks=",highest_peaks
    else : 
        # nothing fancy; just use argmax repeatedly
        highest_peaks = simple_highest_peaks( ndata, hist, num_peaks )
        svg = None
#        svg = np.diff(hist)
        # 2nd derivative
#        svg = np.diff(np.diff(hist))
#        highest_peaks = np.argsort(svg)[0:num_peaks]
#        highest_peaks = np.argsort(svg)[-num_peaks:]

    print highest_peaks

    save_gray_histogram_img( hist, svg, highest_peaks )

    sorted_peaks = sorted(highest_peaks)
    histo_values = [ hist[p] for p in sorted_peaks ]

    # return the pixel values of the peaks and the histogram counts
    return sorted_peaks, histo_values

def main() : 
    from basename import get_basename

    infilename = sys.argv[1]

    ndata = imtools.load_image( infilename, mode="L", dtype="uint8" )
    print ndata.shape

    # aggressive median filter to smooth out as much noise as possible
    if 1 : 
        print "filtering..."
        fdata = scipy.ndimage.filters.median_filter( ndata, size=(5,5) )
    else : 
        fdata = np.copy(ndata) # no smoothing

    basename = get_basename(infilename)
    global mkoutfilename
    mkoutfilename = lambda s : "{0}_{1}.tif".format(basename,s)

    imtools.clip_and_save( fdata, mkoutfilename("gray"))
    np.save("gray.npy",fdata)

    peaks_list, pixel_counts = find_histogram_peaks( fdata ) 
    print "peaks=",peaks_list
    print "counts=",pixel_counts

if __name__ == '__main__' : 
    main()


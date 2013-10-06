#!python

# Automatic find white clipping point. 
#
# Calculate histogram then find the peaks.
#
# davep 31-Mar-2013

import sys
import numpy as np
import Image
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
#import peakdetect2
import savitzky_golay

import imtools
import peaks

def mkhisto( ndata ) : 

    hist = np.zeros( 256, dtype="uint32" ) 

    for p in ndata.flatten() : 
        hist[p] += 1

    return hist

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


def plots( ndata, peaks ) : 
    n,bins = np.histogram(ndata,256)

    fig = Figure(figsize=(8.5,11))

    # plot the histogram
    ax = fig.add_subplot(211)
    ax.grid()
    # don't plot min/max (avoid the clipped pixels)
#    ax.plot(n[1:255])
    ax.plot(n)

    # plot the peaks
    x = peaks
    y = [ n[p] for p in peaks ]
    ax.plot( x, y, 'rx' )

    ax = fig.add_subplot(212)
    ax.grid()
    ax.plot( np.diff(n) )

    # plot the row avg down the page
#    ax = fig.add_subplot(313)
#    ax.grid()
#    ax.plot([ np.mean(row) for row in ndata[:,]])

    outfilename = "out.png"
    canvas = FigureCanvasAgg(fig)
    canvas.print_figure(outfilename)
    print "wrote",outfilename

def xyplot( ndata ) :
    fig = Figure(figsize=(8.5,11))

    # plot the row avg down the page
    ax = fig.add_subplot(211)
    ax.grid()
    ax.plot([ np.mean(row) for row in ndata[:,]])
 
    ax = fig.add_subplot(212)
    ax.grid()
    ax.plot([ np.mean(col) for col in ndata.T[:,]])

    outfilename = "xy.png"
    canvas = FigureCanvasAgg(fig)
    canvas.print_figure(outfilename)
    print "wrote",outfilename

def line_equation( x1, y1, x2, y2, debug=0 ) : 
    line_slope = float(y2-y1)/float(x2-x1)
    line_b = y1 - x1 * line_slope

    eq = lambda x : line_slope * x + line_b
    return eq, line_slope, line_b

def runcontrast( ndata, black_clip, white_clip, outfilename ) : 
    eq,m,b = line_equation( black_clip, 0, white_clip, 255 )
#    print white_clip,black_clip
#    print eq
#    print m,b

    lin = np.linspace(0,255,256)
    lut = np.asarray( [ int(round(eq(l))) for l in lin ] )
#    print len(lut)
    assert len(lut)==256,len(lut)
    lut[ np.where(lut<0) ] = 0
    lut[ np.where(lut>255) ] =255

    lut8 = lut.astype(np.uint8)
    output = lut8[ndata]
    lut8 = lut.astype(np.uint8)

#    outfilename = "{0}_gray.tif".format(basename)
#    outfilename = "clipped.tif"
    img = Image.fromarray(output)

    img2 = img.resize( (img.size[0]/2,img.size[1]/2), Image.BICUBIC )

    img2.save(outfilename)
#    img.save(outfilename)
    print "wrote",outfilename

def plot_savitzky_golay( ndata ) : 
    # kill the clipped-to-white pixels
#    ndata = ndata[:-1]

    smoothed = savitzky_golay.savitzky_golay( ndata, 21, 5, 1 )
#    print "smoothed=", smoothed

    fig = Figure()

    ax = fig.add_subplot(111)
    ax.grid()
    ax.plot(ndata)

#    ax = fig.add_subplot(212)
#    ax.grid()
    ax.plot(smoothed)

    outfilename = "svgy.pdf"
    canvas = FigureCanvasAgg(fig)
    canvas.print_figure(outfilename)
    print "wrote",outfilename

    return smoothed
def old_autowhite( imgfilename ) : 

    ndata = imtools.load_image(imgfilename,dtype="uint8")
    print ndata.shape

#    hist = mkhisto( ndata ) 
#    print hist

    n,bins = np.histogram(ndata,256)
#    n,bins = np.histogram(ndata,256)
    print n

#    nz = np.where(ndata==0)
#    print nz
#    print len(nz[0]),len(nz[1])

#    row_means = [ np.mean(row) for row in ndata[:,]]
#    row_std = [ np.std(row) for row in ndata[:,]]

#    print n
#    peaks = peakdetect.peakdetect_zero_crossing( n[1:255] )
#    peaks = find_peaks(n)
#    print peaks

#    last_peak = peaks[-1]
#    print n[last_peak-10:last_peak+10]
#    print n[last_peak]

#    plots( ndata, peaks )
#    xyplot( ndata )

    smoothed = plot_savitzky_golay( n )
    peaks = find_peaks(smoothed)
    print "peaks=",peaks
    last_peak = peaks[-1]
    print "last_peak=",last_peak
#    print "

    plots( ndata, peaks )

    basename = imtools.get_basename(imgfilename)
    outfilename = "{0}_out.png".format(basename)
    white_clip = last_peak
    ndata2 = np.copy(ndata)
    runcontrast( ndata, 20, white_clip, outfilename )


def autowhite( imgfilename ) : 
    # get the data as grayscale
    ndata = imtools.load_image(imgfilename,dtype="uint8",mode="L")

    basename = imtools.get_basename(imgfilename)
    peaks.mkoutfilename = lambda s : "{0}_{1}.tif".format(basename,s)

    peaks_list, = peaks.find_histogram_peaks(ndata)
    print "peaks_list=",peaks_list
    white_peak = peaks_list[-1]
    black_peak = peaks_list[0]
    print "white_peak={0} black_peak={1}".format(white_peak, black_peak)

    # get the data from the original image
    ndata = imtools.load_image(imgfilename,dtype="uint8")

    outfilename = "{0}_autowhite.png".format(basename)
    white_clip = white_peak
    black_clip = black_peak

    runcontrast( ndata, black_clip, white_clip, outfilename )

def main() : 
    imgfilename = sys.argv[1]
    autowhite( imgfilename )

if __name__=='__main__':
    main()


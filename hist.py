#!/usr/bin/python

# Draw a multiple histogram on same plt. Great for comparing before/after image
# manipulations.
# davep 10-Nov-2011

import sys
import numpy as np
import Image
import matplotlib.pyplot as plt

def multiple_histograms( infilename_list ) : 

    if len(infilename_list)==1 :
        histtype="bar"
    else : 
        # draw transparent histograms so we can see everything
        histtype="step"

    plt.clf()

    plt.title( "Histogram" )
#    plt.suptitle( "Histogram" )

    for infilename in infilename_list : 
        img = Image.open( infilename )
        data = np.asarray( img )

        plt.hist( data.flatten(), range=(0,255), bins=256, 
                        histtype=histtype, label=infilename ) 

    # expand the Y by 10% so the legend (hopefully) won't sit on top of any
    # histogram peaks
    ymin,ymax = plt.ylim()
    ymax += ymax/10
    plt.ylim( (ymin,ymax) )

    # thanks to 
    # http://stackoverflow.com/questions/7802366/matplotlib-window-layout-questions
    mng = plt.get_current_fig_manager()
    mng.resize( 1280, 1024)

    mng.set_window_title( "Happy Histograms" )

    plt.legend()
    plt.grid()
    plt.show()

if __name__ =='__main__' : 
    multiple_histograms( sys.argv[1:] )


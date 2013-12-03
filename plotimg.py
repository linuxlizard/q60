#!/usr/bin/env python

# Draw a matplotlib animation of pixel row deltas.
# Adapted from a simple animation script I found somewhere.
#
# davep 02-Dec-2013

import sys
import matplotlib.pyplot as plt
import numpy as np
import time
   
import imtools

is_paused = False

# http://matplotlib.org/users/event_handling.html
def onclick(event):
    global is_paused
       
    is_paused = not is_paused
    
def main(): 
    infilename = sys.argv[1]
    ndata = imtools.load_image(infilename,mode="L")

    fig, ax = plt.subplots()

    cid = fig.canvas.mpl_connect('button_press_event', onclick)

    tstart = time.time()
    num_plots = 0
    #while time.time()-tstart < 1:
    while 1:
        rowidx = 0
        for row in ndata: 
            ax.clear()
            ax.grid()
            ax.set_title("{0}".format(rowidx))
            ax.plot(np.diff(row))
            ax.set_ylim((-250,250))
            
            plt.pause(0.01)
            while is_paused : 
                plt.pause(0.10)

            num_plots += 1
            rowidx += 1

    print(num_plots)

if __name__=="__main__":
    main()


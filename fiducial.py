#!/usr/bin/env python

# Find fiducials in Q60
#
# davep 30-oct-2013

import sys
import numpy as np
import logging
import pickle
import math
import itertools
from scipy.cluster.vq import kmeans,vq
#import matplotlib.pyplot as plt

import imtools

STATE_INIT=0
STATE_SEEK_NEGATIVE_EDGE=1  # large negative difference
STATE_SEEK_POSITIVE_EDGE=2  # large positive difference
STATE_SEEK_FLAT=3           # small or no difference
STATE_SEEK_POSITIVE_EDGE_2=4  # large positive difference
STATE_SEEK_NEGATIVE_EDGE_2=5  # large negative difference

#STATE_SEEK_BLACK=10  # search for black line of fiducial
#STATE_SEEK_WHITE=11  # search for white line of fiducial

edge_threshold = 20
flat_threshold = 2

def find_fiducials(ndata):

    pixel_diffs = np.diff(ndata)

    fiducial_list = []

    for row_idx,row in enumerate(pixel_diffs) : 
        state = STATE_SEEK_NEGATIVE_EDGE

        # for testing, stop here
#        if row_idx > 1000 : 
#            break

        debug = []

        logging.debug("row_idx={0}".format(row_idx))
        # process pixel by pixel; only search the first half of the image. If
        # we haven't found it by 4", we're not going to find it.
        for col_idx in range(len(row)/2):

            # XXX debug specific row
            if row_idx==14 : 
                logging.debug("row={2} col_idx={0} pixel={1}".format(
                            col_idx,row[col_idx],row_idx))

            if state==STATE_SEEK_NEGATIVE_EDGE :
                if row[col_idx] < -edge_threshold : 
                    # edge falling to lower color (gray to black?)
                    state = STATE_SEEK_POSITIVE_EDGE
                    distance = 0
                    max_distance = 4
                    debug.append((col_idx,row[col_idx],state))
                    logging.debug(
                        "found negative edge at row={0} col={1} pixel={2}".format(
                            row_idx,col_idx,row[col_idx]))

            elif state==STATE_SEEK_POSITIVE_EDGE : 
                distance += 1
                if distance > max_distance : 
                    # didn't find edge within distance; restart search
                    distance = 0
                    logging.debug("restart at state={0} col={1}".format(
                            state,col_idx))
                    state = STATE_SEEK_NEGATIVE_EDGE
                elif row[col_idx] > edge_threshold : 
                    distance = 0
                    max_distance = 5
                    # return to zero derivative to indicate return to
                    # background
                    state = STATE_SEEK_FLAT
                    logging.debug("found positive edge at row={0} col={1}".format(
                         row_idx,col_idx))
                    debug.append((col_idx,row[col_idx],state))

            elif state==STATE_SEEK_FLAT : 
                distance += 1
                if distance > max_distance : 
                    # didn't find what we wanted within distance; restart search
                    logging.debug("fail distance={0} > max_distance={1}".format(
                            distance, max_distance ) )
                    distance = 0
                    logging.debug("restart at state={0} col={1}".format(
                            state,col_idx))
                    state = STATE_SEEK_NEGATIVE_EDGE
                elif row[col_idx]>-flat_threshold and row[col_idx]<flat_threshold :
                    distance = 0
                    max_distance = 50
                    state = STATE_SEEK_POSITIVE_EDGE_2
                    logging.debug("found intrafiducial flat area at row={0} col={1}".format(
                         row_idx,col_idx))
                    debug.append((col_idx,row[col_idx],state))

            elif state==STATE_SEEK_POSITIVE_EDGE_2 : 
                distance += 1
                if distance > max_distance : 
                    # didn't find what we wanted within distance; restart search
                    logging.debug("fail distance={0} > max_distance={1}".format(
                            distance, max_distance ) )
                    distance = 0
                    logging.debug("restart at state={0} col={1}".format(
                            state,col_idx))
                    state = STATE_SEEK_NEGATIVE_EDGE
                elif row[col_idx] < -edge_threshold : 
                    # oops ; found an edge in the wrong direction
                    # so restart
                    logging.debug("fail distance={0} > max_distance={1}".format(
                            distance, max_distance ) )
                    distance = 0
                    logging.debug("restart at state={0} col={1}".format(
                            state,col_idx))
                    state = STATE_SEEK_NEGATIVE_EDGE
                elif row[col_idx] > edge_threshold : 
                    distance = 0
                    state = STATE_SEEK_NEGATIVE_EDGE_2
                    debug.append((col_idx,row[col_idx],state))

            elif state==STATE_SEEK_NEGATIVE_EDGE_2 : 
                distance += 1
                if distance > max_distance : 
                    # didn't find what we wanted within distance; restart search
                    distance = 0
                    logging.debug("restart at state={0} col={1}".format(
                            state,col_idx))
                    state = STATE_SEEK_NEGATIVE_EDGE
                elif row[col_idx] < -edge_threshold : 
                    distance = 0
                    print "found fiducial at row={0} col={1}".format(row_idx,col_idx)
                    fiducial_list.append({"row":row_idx,"col":col_idx})
                    break
            else : 
                pass

    # filter_fiducials() removes the outliers
    return filter_fiducials( fiducial_list )

def euclidian(p1,p2):
    # calculate euclidian distance
    return math.sqrt( (p1[0]-p2[0])**2 + (p1[1]-p2[1])**2 )

def filter_fiducials( fiducial_list ) : 
    # Calculate north,south distance for each point. Remove any points with no
    # neighbor within some distance.

    # fiducial_list is an array of tuples
    # [0] is row
    # [1] is col

#    filtered_fiducial_list = fiducial_list
#    return filtered_fiducial_list

    # calculate distance to next fiducial
    for i in range(len(fiducial_list)-1):
        fiducial_list[i]["dist_next"] = euclidian( 
            (fiducial_list[i]["row"],fiducial_list[i]["col"]),
            (fiducial_list[i+1]["row"],fiducial_list[i+1]["col"]) )
    fiducial_list[-1]["dist_next"] = 1e9

    # calculate distance to previous fiducial
    fiducial_list[0]["dist_prev"] = 1e9
    for i in range(1,len(fiducial_list)):
        fiducial_list[i]["dist_prev"] = euclidian( 
            (fiducial_list[i]["row"],fiducial_list[i]["col"]),
            (fiducial_list[i-1]["row"],fiducial_list[i-1]["col"]) )

    filtered_fiducial_list = [ fid for fid in fiducial_list if  
                                fid["dist_next"] < 5 or fid["dist_prev"] < 5 ]

    return filtered_fiducial_list

def make_clusters( fiducial_list ) : 
    # everyone starts outside a group
    for fid in fiducial_list : 
        fid["group"] = 0

    # Sort-of a connected compontents algorithm. The data has a number of
    # restrictions that make it easier. There is only one point per row. The
    # points are sparsely distributed (can do stupid iterative searches without
    # much speed penalty).
    #
    # Iterate through the list.
    #
    # If node not already in a group, create a new group. 
    #
    # Check if next neighbor (next row) is close enough to belong to the same
    # group.
    #
    group_id = itertools.count(1)
    for i in range(len(fiducial_list)-1):
        if fiducial_list[i]["group"]==0 :
            # start a new group
            fiducial_list[i]["group"] = group_id.next()

        # is my neighbor close enough to belong to my group?
        if fiducial_list[i+1]["group"] == 0 and fiducial_list[i]["dist_next"] < 5 :
            fiducial_list[i+1]["group"] = fiducial_list[i]["group"]

    # last node
    if fiducial_list[-1]["group"]==0 :
        # start a new group
        fiducial_list[-1]["group"] = group_id.next()


def write_fiducial_image( infilename, fiducial_list ) :
    # load the mono image, convert to color, write red dots on the image where
    # we think we found the fiducial

    ndata = imtools.load_image(infilename,mode="L",dtype="uint8")
    # make into an RGB image
    rgbdata = np.zeros((ndata.shape[0],ndata.shape[1],3))
    rgbdata[:,:,0] = ndata
    rgbdata[:,:,1] = ndata
    rgbdata[:,:,2] = ndata

    for fiducial in fiducial_list:
        row = fiducial["row"]
        col = fiducial["col"]
        rgbdata[row,col,0] = 255
        rgbdata[row,col,1] = 0 
        rgbdata[row,col,2] = 0 
    imtools.clip_and_save(rgbdata,"out.tif")

def find_fiducials_in_file(infilename):
    ndata = imtools.load_image(infilename,mode="L")

    # While developing the filter code, save the fiducials list to a pickle.
    # The image processing part is a bit slow.
    if 0 : 
        fiducial_list = find_fiducials(ndata)
        with open("fid.dat","wb") as pfile:
            pickle.dump(fiducial_list,pfile)
    else : 
        with open("fid.dat","rb") as pfile:
            fiducial_list = pickle.load(pfile)

    filtered_fiducial_list = filter_fiducials(fiducial_list)
    print fiducial_list

    write_fiducial_image(infilename,fiducial_list)
#    write_fiducial_image(infilename,filtered_fiducial_list)

    clusters = make_clusters(filtered_fiducial_list)

    for fid in filtered_fiducial_list :
        print fid["row"], fid["col"], fid["dist_prev"],fid["dist_next"],fid["group"]

    data = np.asarray([ (fid["row"],fid["col"]) for fid in filtered_fiducial_list ])

    # http://glowingpython.blogspot.com/2012/04/k-means-clustering-with-scipy.html
    # computing K-Means with K = 2 (2 clusters)
    centroids,_ = kmeans(data,2)
    # assign each sample to a cluster
    idx,_ = vq(data,centroids)

    print centroids

#    plt.plot(data[idx==0,0],data[idx==0,1],'ob',
#     data[idx==1,0],data[idx==1,1],'or',
#     data[idx==2,0],data[idx==2,1],'og') # third cluster points
#    plt.plot(centroids[:,0],centroids[:,1],'sm',markersize=8)
#    plt.show()

def main() : 
    logging.basicConfig(format='%(levelname)s:%(message)s',level=logging.INFO)
#    logging.basicConfig(format='%(levelname)s:%(message)s',level=logging.DEBUG)
    infilename = sys.argv[1]

    find_fiducials_in_file(infilename)

if __name__=='__main__' :
    main()


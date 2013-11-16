#!/usr/bin/env python

# Find fiducials in Q60
#
# davep 30-oct-2013

import sys
import numpy as np
import logging

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
        # process pixel by pixel
        for col_idx in range(len(row)):

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
                    fiducial_list.append((row_idx,col_idx))
                    break
            else : 
                pass

    return fiducial_list

def find_fiducials_in_file(infilename):
    ndata = imtools.load_image(infilename,mode="L")

    fiducial_list = find_fiducials(ndata)

    ndata = imtools.load_image(infilename,mode="L",dtype="uint8")
    # make into an RGB image
    rgbdata = np.zeros((ndata.shape[0],ndata.shape[1],3))
    rgbdata[:,:,0] = ndata
    rgbdata[:,:,1] = ndata
    rgbdata[:,:,2] = ndata

    for fiducial in fiducial_list:
        rgbdata[fiducial[0],fiducial[1],0] = 255
        rgbdata[fiducial[0],fiducial[1],1] = 0 
        rgbdata[fiducial[0],fiducial[1],2] = 0 
    imtools.clip_and_save(rgbdata,"out.tif")

def main() : 
    logging.basicConfig(format='%(levelname)s:%(message)s',level=logging.INFO)
#    logging.basicConfig(format='%(levelname)s:%(message)s',level=logging.DEBUG)
    infilename = sys.argv[1]

    find_fiducials_in_file(infilename)

if __name__=='__main__' :
    main()


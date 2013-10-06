#!/usr/bin/python

# Parse the Q60. Find the colors.
# I've been meaning to do this for years.
# davep 26-May-2013

import sys
import numpy as np
import scipy.ndimage.filters
import scipy.ndimage.interpolation
import Image
import ImageDraw
import os
import math
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
import savitzky_golay

import imtools
import histo
from basename import get_basename
import peaks
import straight

#bezel_row = 20
#bezel_col = 10

# Calculated by find_gray_midpoint(). Used in a few places through the code so
# made a global.
gray_low = 0
gray_high = 0

mkoutfilename = None

ROTATE_COUNTER_CLOCKWISE = "CCW"
ROTATE_CLOCKWISE = "CW"

def find_gray_midpoint( ndata ) : 

    # The incoming data is grayscale.  Other than white, the gray background of
    # the q60 is the majority color. Because the gray level might be different
    # depending in how the q60 was scanned (PIE, noPIE, different sensors,
    # different IQ settings, etc), find the majority gray value. That 
    #

    peaks_list, pixel_counts = peaks.find_histogram_peaks(ndata)
    print "peaks=",peaks_list
    print "counts=",pixel_counts

#    # highest should be white
#    # 2nd highest should be the q60's background gray
#    white_idx = np.argmax(pixel_counts)
#    print "white_idx=",white_idx
#
#    pixel_counts.pop(white_idx)
#    gray_idx = np.argmax(pixel_counts)
#    print "gray_idx=",gray_idx

    # davep 19-Sep-2013 ; let's assume we're running a PIE image so the gray
    # midpoint should be ~128. Look for the point closes to 128.
    for gray_idx in range(len(peaks_list)) : 
        if peaks_list[gray_idx] > 120 and peaks_list[gray_idx] < 130 : 
            return peaks_list[gray_idx]

    raise Exception( "Bad gray midpoint" )

def calc_gray_boundaries(ndata) :

    gray_midpoint = find_gray_midpoint( ndata )

    global gray_low, gray_high
    gray_low = gray_midpoint - 10
    gray_high = gray_midpoint + 10

    print "gray_low={0} gray_high={1}".format(gray_low,gray_high)

def draw_hypotenuse( imgfilename, nz) :
    upper_left = nz[0][0],nz[1][0]
    lower_right = nz[0][-1],nz[1][-1]

    print "upper_left={0} lower_right={1}".format(upper_left,lower_right)

    img = Image.open(imgfilename)
    img.load()
    draw = ImageDraw.Draw(img)

def detect_rotate_direction( gray_bbox ) : 
    # davep 19-Sep-2013 ; new rotation function (see notes this date for cool
    # pictures)

    # detect direction rotation by examining the aspect ration of the black
    # lines on either side of the tip of the triangle formed by the rotated q60
    row0 = gray_bbox[0,:]
    print row0.shape

    # np.where will return tuple of (row,col) indices. We only want the row
    # value so we take [0]
    nonblack_pixels = np.where(row0!=0)[0]
   
    print nonblack_pixels.shape
    left_side_len = nonblack_pixels[0]
    right_side_len = len(row0) - nonblack_pixels[-1]
    
    if left_side_len > right_side_len : 
        # big left side triangle, smaller right side triangle implies we are
        # rotated clockwise
        return ROTATE_COUNTER_CLOCKWISE 

    # otherwise assume we're rotated clockwise
    return ROTATE_CLOCKWISE

def detect_rotation_angle( gray_bbox, rotate_direction) : 
    # davep 19-Sep-2013 ; new rotation function (see notes this date for cool
    # pictures)

    row0 = gray_bbox[0,:]

    if rotate_direction==ROTATE_COUNTER_CLOCKWISE :
        col0 = gray_bbox[:,0]

        longedge_p0 = (0,0)

        # find Q60's right side pixel along the top edge of the scan.
        # np.where returns a tuple of row/col. We only want row so that's the
        # first [0]. We want the first pixel of the edge so that's the second
        # [0]
        p1_col = np.where(row0!=0)[0][0]
        longedge_p1 = (0,p1_col)

        shortedge_p0 = (0,0)
        p1_row = np.where(col0!=0)[0][0]
        shortedge_p1 = (p1_row,0)

        print longedge_p0, longedge_p1
        print shortedge_p0, shortedge_p1

    else : 
        # last (right-most) column
        colN = gray_bbox[:,-1]
        
        # last pixel of Q60's top left edge. np.where returns a tuple of pixel
        # (row,col). We only want row thus [0]. We only want the first non-zero
        # pixel thus the second [0]
        longedge_p0 = (0,np.where(row0!=0)[0][0])
        longedge_p1 = (0,len(row0))

        shortedge_p0 = longedge_p1
        p1_row = np.where(colN!=0)[0][0]
        shortedge_p1 = (p1_row,shortedge_p0[1])

        print longedge_p0, longedge_p1
        print shortedge_p0, shortedge_p1

    # angle is tan(theta) = (opposite / adjacent)
    # tan(theta) = short edge / long edge
    opp = shortedge_p1[0] - shortedge_p0[0]   # row
    adj = longedge_p1[1] - longedge_p0[1] # column

    print "opp={0} adj={1}".format(opp,adj)

    angle = math.atan( float(opp)/float(adj) )
    if rotate_direction==ROTATE_COUNTER_CLOCKWISE :
        angle = -angle

    # calculate the hypotenuse length because it's also the width of the Q60
    hyp_length = int(round(math.sqrt( opp**2 + adj**2 ) ) )

    return angle,hyp_length
    
def main() :
    infilename = sys.argv[1]

    basename = get_basename(infilename)

    global mkoutfilename
    mkoutfilename = lambda s : "{0}_{1}.tif".format(basename,s)

    ndata = imtools.load_image( infilename, mode="L", dtype="uint8" )
    print ndata.dtype, ndata.shape

#        # get rid of the obnoxious bezel shadow in my test image >:-(
#        ndata = ndata[ bezel_row:, bezel_col: ]

    # aggressive median filter to smooth out as much noise as possible
    fdata = scipy.ndimage.filters.median_filter( ndata, size=(5,5) )

    imtools.clip_and_save( fdata, mkoutfilename("gray"))

    # find the optimum gray midpoint 
    calc_gray_boundaries(fdata)
    # XXX temp debug ; leave here while working on gray background discovery
#    return

    gray1 = np.where(fdata>gray_low,fdata,0)
    imtools.clip_and_save( gray1, mkoutfilename("gray1") )
    gray2 = np.where(gray1<gray_high,gray1,0)
    imtools.clip_and_save( gray2, mkoutfilename("gray2") )

    nz = np.nonzero( gray2 )

    np.save("nz.npy",nz)

    # nz[0] is the rows
    # nz[1] is the cols
    min_row = np.min(nz[0])
    max_row = np.max(nz[0])
    min_col = np.min(nz[1])
    max_col = np.max(nz[1])

    print "min_row={0} max_row={1}".format(min_row,max_row)
    print "min_col={0} max_col={1}".format(min_col,max_col)

    # reload the original image
    ndata = imtools.load_image(infilename,dtype="uint8")

    # clip original image to bounding box
    bbox = ndata[min_row:max_row, min_col:max_col]
    imtools.clip_and_save(bbox,mkoutfilename("bbox"))

    # clip gray2 to bbox
    gray_bbox = gray2[min_row:max_row, min_col:max_col]
    np.save("gray.npy",gray_bbox)
    imtools.clip_and_save(gray_bbox,mkoutfilename("gray_bbox"))

    # XXX temp debug ; stop here while working on skew 
#    draw_hypotenuse(infilename,nz)
#    sys.exit(0)

    # The q60 may not be heavily skewed. Sample the four corners of the
    # bounding box. If the areas at the corners are mostly gray, call it good.
    # Solves the problem of very, very small skew and the ragged edge of the
    # Q60 causing the edges to land halfway down the target.
    #
    # Note we run the straightness test on the filtered (smoothed) data
    is_straight = straight.straightness_test( fdata[min_row:max_row, min_col:max_col], 
                                                gray_low, gray_high )
    if is_straight : 
        # close enough!
        print "close enough!"
        imtools.clip_and_save(bbox,mkoutfilename("q60"))
        return

    assert 0
    print "is not straight enough so lets rotate"

    # davep 19-Sep-2013 ;  new de-skew
    rotate_direction = detect_rotate_direction( gray_bbox )
    print "rotate={0}".format(rotate_direction)
    
    rotation_angle, hyp_length = detect_rotation_angle( gray_bbox, rotate_direction ) 
    print "angle={0}={1} hyp={2}".format(
            rotation_angle,math.degrees(rotation_angle),hyp_length)

    rot = scipy.ndimage.interpolation.rotate( bbox, math.degrees(rotation_angle) )
    print "rot=",rot.shape
    imtools.clip_and_save(rot,mkoutfilename("rot"))

    q60_width = hyp_length
    # use the known aspect ratio to deduce height
    q60_height = int(round((q60_width*5.0)/7.0))
    print "q60 width={0} height={1}".format(q60_width,q60_height)
    col_pad = (rot.shape[1]-q60_width)/2
    row_pad = (rot.shape[0]-q60_height)/2
    print "row_pad={0} col_pad={1}".format(row_pad,col_pad)
    q60 = rot[ row_pad:q60_height, col_pad:q60_width ]
    print "q60=",q60.shape
    imtools.clip_and_save(q60,mkoutfilename("q60"))

#    # XXX temp debug ; leave here while working on new de-skew straightness test
    sys.exit(0)

    # make a triangle so we can de-skew. 
    # p1 is the upper right of Q60
    # p2 is the upper left
    # p3 is the lower left
    #
    #  Counter-clockwise rotated
    #
    #                   p1
    #      p2
    #
    #
    #       p3
    #
    #
    #  Clockwise rotate
    #
    #      p2 
    #
    #                   p1
    #    p3  
    #
    #
    # Right Triangles
    #
    #    .--------------p1
    #    |
    #    |
    #    |
    #    p2
    #
    #
    #    p2-------------.
    #                   |
    #                   |
    #                   |
    #                   p1

    # if the target is pushed against a scanner edge, there will be multiple
    # locations at the min/max
    rows_at_min = np.where(nz[0]==min_row)[0]
    rows_at_max = np.where(nz[0]==max_row)[0]
    cols_at_min = np.where(nz[1]==min_col)[0]
    cols_at_max = np.where(nz[1]==max_col)[0]
    
    # Euclidean distance
    dist = lambda P,Q : math.sqrt( (P[0]-Q[0])**2 + (P[1]-Q[1])**2 )

    A = min_row, nz[1][rows_at_min[-1]]
#    A = min_row, nz[1][np.argmin(nz[0])]
    B = nz[0][cols_at_max[-1]], max_col
#    B = nz[0][np.argmax(nz[1])], max_col
    C = max_row, nz[1][np.argmax(nz[0])]
    
    print "A={0} B={1} C={2}".format(A,B,C)

    if dist(A,B) > dist(B,C) :
        clockwise = False
        p1 = B
        p2 = A
        p3 = nz[0][np.argmin(nz[1])],min_col
    else : 
        clockwise = True 
        p1 = A
        p2 = nz[0][np.argmin(nz[1])],min_col
        p3 = C

    print "p1=",p1
    print "p2=",p2
    print "p3=",p3

    if clockwise : 
        print "rotate clockwise"
        triangle = ndata[p1[0]:p2[0], p2[1]:p1[1]]
    else : 
        print "rotate counter-clockwise"
        triangle = ndata[p2[0]:p1[0], p2[1]:p1[1]]

    imtools.clip_and_save(triangle,mkoutfilename("triangle"))

    tri_width = abs(p1[1] - p2[1])
    tri_height = abs(p2[0] - p1[0])
    print "tri_width={0} tri_height={1}".format(tri_width,tri_height)

    # length of upper edge (hypotenuse) is Euclidean distance between the two
    # points
    hyp_len = math.sqrt( (p1[0]-p2[0])**2 + (p1[1]-p2[1])**2 )
    print "hyp_len=",hyp_len

    if clockwise : 
        theta = math.acos( float(tri_width)/hyp_len )
        theta_degrees = -math.degrees(theta)
    else :
        theta = math.acos( float(tri_height)/hyp_len )
        theta_degrees = 90 - math.degrees(theta)

    print "theta=",theta,theta_degrees

    rot = scipy.ndimage.interpolation.rotate( bbox, theta_degrees)
    print rot.shape
    imtools.clip_and_save(rot,mkoutfilename("rot"))

    q60_height = math.sqrt( (p3[0]-p2[0])**2 + (p3[1]-p2[1])**2 )
    q60_width = math.sqrt( (p2[0]-p1[0])**2 + (p2[1]-p1[1])**2 )
    print "q60_width={0} q60_height={1}".format(q60_width,q60_height)

    center = rot.shape[0]/2,rot.shape[1]/2
    print "center=",center

    q60 = rot[ center[0]-q60_height/2 : center[0]+q60_height/2 ,
                center[1]-q60_width/2 : center[1]+q60_width/2 ]

    imtools.clip_and_save(q60,mkoutfilename("q60"))

if __name__=='__main__' :
    main()


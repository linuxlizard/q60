#!/usr/bin/env python

# playing with OpenCV findCountours
# davep 21-Oct-2013

import sys
import cv2
import numpy as np

def find_contours_file(infilename):
    img = cv2.imread(infilename)
#    print img

    grayimg = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    cv2.imwrite("gray.tif",grayimg)

    blurimg = cv2.blur(grayimg,(3,3))
    cv2.imwrite("blur.tif",blurimg)

    cannyimg = cv2.Canny(blurimg,100,200,None,3)
    cv2.imwrite("canny.tif",cannyimg)

    contours = cv2.findContours(cannyimg,cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE)
    np.save("contours.npy",contours)
#    print contours
#    for c in contours : 
#        print c

def main() : 
    infilename = sys.argv[1]
    find_contours_file( infilename )

if __name__=='__main__' :
    main()


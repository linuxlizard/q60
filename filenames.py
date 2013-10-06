#!python

import os

def get_basename( filename ) : 
    return os.path.splitext( os.path.split( filename )[1] )[0]

def get_outfilename_maker(filename,ext=".tif"):
    # create a lambda that will make an output filename using the original name
    # davep 15-Jun-2013
    basename = get_basename( filename )
    mkoutfilename = lambda s : "{0}_{1}{2}".format(basename,s,ext)
    return mkoutfilename


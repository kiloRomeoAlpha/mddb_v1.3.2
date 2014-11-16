#!/usr/bin/env python
#
#                                                           CyberSKA DQS Project
#
#                                                     mddb.convert.converters.py
#                                                      Kenneth Anderson, 2012-06
#                                                            ken.anderson@ubc.ca
# ------------------------------------------------------------------------------

# $Id$
# ------------------------------------------------------------------------------
__version__      = '$Revision$'[11:-3]
__version_date__ = '$Date$'[7:-3]
__author__       = "k.r. anderson, <ken.anderson@ubc.ca>"
# ------------------------------------------------------------------------------

"""Conversion functions"""
#-------------------------------------------------------------------------------


from math    import sqrt, sin, cos
from keymaps import ctypeMap, projectionMap


def llh(lines):
    """Function receives a list of CASA Image header lines and calculates
    the transformation of telescope position coordinates of lat,lon, height
    into the ITRF X,Y,Z parameters.

    paramaters: <list>,  list of image header lines
    return:     <tuple>, 3-tuple of floats
    """
    obsX = 'OBSGEO-X'
    obsY = 'OBSGEO-Y'
    obsZ = 'OBSGEO-Z'
    err = "Telscope position parameters not found."
    lat = lon = hgt = posIndex = None

    for idx in range(len(lines)):
        lvals = lines[idx].split('\t')
        if lvals[0] == 'TELESCOP_LAT':
            lat = lvals[2]
            continue
        if lvals[0] == 'TELESCOP_LON':
            lon = lvals[2]
            continue
        if lvals[0] == 'TELESCOP_HGT':
            hgt = lvals[2]
            posIndex = idx
            continue
        if hgt and lon and lat: break
    print "postion parameters found at index::", posIndex
    X,Y,Z = llh2XYZ(float(lat), float(lon), float(hgt))
    print obsX+'\t\t'+str(X),"(m)"
    print obsY+'\t\t'+str(Y),"(m)"
    print obsZ+'\t\t'+str(Z),"(m)"
    return X,Y,Z


def llh2XYZ(lat, lon, h):
    """Converts a geodetic latitude, longitude and height into a 
    ITRF geocentric X,Y,Z tuple (m), the standard measure for keyword
    values,
    
    OBSGEO-X
    OBSGEO-Y
    OBSGEO-Z

    Currently, the WGS84 geodetic model is the basis for this
    conversion where,
    
    A  is the semi-major axis of the model ellipse
    FL is the "flattening" parameter

    A   = 6378137.0 (m)
    FL  = 0.00335281066475    # 1/298.257223563

    latitude, longitude are radians, h in metres (m).
    latitude, radians east of Greenwich.

    Equations implemented here are adapted from the National 
    Geodetic Survey (NGS) package XYZWIN - Version 2.0, the source for 
    which can found at http://www.ngs.noaa.gov/PC_PROD/XYZWIN/

    parameters: <float>, <float>, <float>, lat (rad), lon(rad), height(m)
    return:     <float>, <float>, <float>, X, Y, Z (m)
    """

    # lat = plh[0]
    # lon = plh[1]
    # alt = plh[2]
    
    # GRS80 parameters, A == semi-major axis, FL == flattening 
    # A  = 6378137.0
    # FL = 0.00335281068118    1/298.257222101
    
    # WGS84 parameters, A == semi-major axis, FL == flattening 
    A   = 6378137.0
    FL  = 0.00335281066475    # 1/298.257223563
    ONE = 1.00
    TWO = 2.00

    flatfn = (TWO - FL)*FL
    funsq  = (ONE - FL)*(ONE - FL)

    #lat_rad= deg_to_rad * plh[0]
    #lon_rad= deg_to_rad * plh[1]

    sin_lat= sin(lat)

    g1= A / sqrt( ONE - flatfn * sin_lat*sin_lat )
    g2= g1 * funsq + h
    g1= g1 + h

    X = g1 * cos(lat)
    Y = X  * sin(lon)
    X = X  * cos(lon)
    Z = g2 * sin_lat

    return X,Y,Z


def revertFrequency(fval, unit):
    """Revert a frequency value in 'unit' measure to pure
    Hz value, where 'unit' may be one of

    Hz, KHz, MHz, GHz
    
    parameters: <float>, <string>, a freq value, unit
    return:     <float>, reverted freq value in Hz.
    """
    engunits = {  'Hz': 1,
                 'kHz': 1000,
                 'MHz': 1.0E6,
                 'GHz': 1.0E9
                 }
    
    hzValue = fval * engunits[unit]
    return hzValue


def decimalize(deltaString):
    """Convert the passed string value in [+-]deg.min.sec format
    to decimal degrees.
    
    eg.,
    >>> decimalize('+0.1.1.0')
    0.0002777777777777778
    >>> decimalize('-0.0.1.0')
    -0.0002777777777777778
    
    parameters:  <string>  increment string
    return:      <float>,  float value of the measure, decimal degrees.
    """
    errstr = 'Unrecognized increment value.'
    
    deltaVals = deltaString.split('.')
    sign = deltaString[0]
    sdeg = abs(float(deltaVals[0]))
    smin = float(deltaVals[1])
    ssec = float(deltaVals[2]+'.'+deltaVals[3].strip(','))
    dmin = smin + ssec/60
    ddeg = sdeg + dmin/60
    if   sign == '-': ddeg *= -1.0
    elif sign == '+': pass
    else: raise ValueError, errstr
    return ddeg


def formatRA(raval):
    """Reformat a passed RA value of HH:MM:SS.sss into [d]dd.mm.ss.sss

    parameters: <string>, of the form 'HH:MM:SS.sss'
    return:     <string>, of the form '[d]dd.mm.ss.sss'
    """
    ravals = raval.split(":")
    h2deg  = ravals[0]
    if h2deg < 0: sign='-'
    else: sign = '+'
    newRA  = sign+str(h2deg)+'.'+ravals[1]+'.'+ravals[2]
    return newRA


def fitsify(coord, i, projection=None):
    """Convert a CASA Image header coordinate type/name into FITS 
    compliant keyword-value pairs. A non-direction CASA coordinate
    returns a 2-tuple, a CASA direction coordinate, a 4-tuple.
    The passed index i will determine a CTYPE[i] value for returned
    keywords.
    
    eg.,
    >>> coord1 = 'COORDINATE0-TYPE_NAME:Frequency'
    >>> coord2 = 'COORDINATE2-TYPE_NAME:Declination & Right Ascension'
    >>> proj   = 'SIN'
    >>>
    >>>fitsifyCoord(coord1, 1)
    ('CTYPE1', 'FREQ')
    >>>
    >>>fitsifyCoord(coord2, 2 ,proj)
    ('CTYPE3','DEC--SIN','CTYPE4','RA---SIN')

    An unrecognized coordinate will raise a TypeError:

    >>> coord1 = "KAAAAAHN!"
    >>> fitsify(coord1,1)
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "converters.py", line 208, in fitsify
    
    TypeError: Cannot interpret coordinate, KAAAAAAHN!

    parameters: <string>, <int>, <string> 
    return:     <tuple>,  n-tuple of strings.
    """
    ctype1Key  = 'CTYPE'+str(i)
    ctype2Key  = 'CTYPE'+str(i+1)
    casa1      = None
    casa2      = None
    fitsCtype1 = None
    fitsCtype2 = None

    try:
        axes = coord.split(':')[1]
    except IndexError:
        raise TypeError, 'Cannot interpret coordinate, '+coord

    if '&' in axes:
        ax1,ax2 = axes.split('&')
        casa1 = ax1.strip()
        casa2 = ax2.strip()
    else:
        casa1 = axes.strip()
    if casa1 and casa2:
        try:
            fitsCtype1 = ctypeMap[casa1]+projectionMap[projection]
            fitsCtype2 = ctypeMap[casa2]+projectionMap[projection]
            return ctype1Key, fitsCtype1, ctype2Key, fitsCtype2
        except KeyError:
            raise TypeError, 'Cannot interpret coordinate, '+coord
    elif casa1 and not casa2:
        try:
            fitsCtype1 = ctypeMap[casa1]
            return ctype1Key, fitsCtype1
        except KeyError:
            raise TypeError, 'Cannot interpret coordinate, '+coord
    return


def referencePixels(refPixLine):
    """Function recieves a line containing the reference pixel list (or array)
    for a CASA Image direction coordinate, and returns a 2-tuple of reference pixel
    values. These are left as strings for the convenience of file writing.

    Eg., a typical reference pixel header line is passed:
    >>> line = 'REFERENCE2-PIXEL	32.0, 32.0'
    >>> convertRefPix(line)
    ('32.0', '32.0')

    parameters:   <string>, a 'REFERENCE[i]-PIXEL' header line
    return:       <tuple>,  pixel1, pixel2
    """
    parts = refPixLine.split()
    return parts[1].strip(), parts[2].strip()


def getValTuple(line):
    val1 = val2 = ''
    vals = line.split()
    if len(vals) == 3:
        val1 = vals[1]
        val2 = vals[2]
    elif len(vals) == 4:
        val1 = vals[1]
        for val in vals[2:]:
            val2 += ' '+val
    else: raise TypeError,"Inappropriate line type for this function."
    return val1.strip(','),val2.strip()

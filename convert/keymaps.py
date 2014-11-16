#
#
#                                                 CyberSKA CASA Metadata Project
#
#                                                        mddb.convert.keymaps.py
#                                                      Kenneth Anderson, 2012-04
#                                                            ken.anderson@ubc.ca
# ------------------------------------------------------------------------------

# $Id$
# ------------------------------------------------------------------------------
__version__      = '$Revision$'[11:-3]
__version_date__ = '$Date$'[7:-3]
__author__       = "k.r. anderson, <ken.anderson@ubc.ca>"
# ------------------------------------------------------------------------------
"""Module provides a key mappings for metadata headers.

velrefMaP: maps VELREF keyword values to SPECSYS values.
           implements Table 8 of Greisen et al, 2002 and casacore VELREF 
           bitmap:
           
           i.e.  Radio 256+  1 LSRK, 2 HELIOCENT, 3 TOPOCENT, 
                             4 LSRD, 5 GEOCENT, 6 SOURCE, 7 GALACTOC

N.B. Some header files have presented VELREF key values as single digit 
values (eg. 2, 3, ... etc) instead of the additive value of 256+. This was causing
a KeyError on lookup. These single digit values have been added to the velrefMap keys.
-- k. anderson, 2012-10-14

(See Greisen et al, Representation of Spectral Coordinates in FITS,
2002, Table 8, p. 14)
"""

velrefMap = {1: 'LSRK',
             2: 'HELIOCENT',
             3: 'TOPOCENT',
             4: 'LSRD',
             5: 'GEOCENT',
             6: 'SOURCE',
             7: 'GALACTIC',
             257: 'LSRK',
             258: 'HELIOCENT',
             259: 'TOPOCENT',
             260: 'LSRD',
             261: 'GEOCENT',
             262: 'SOURCE',
             263: 'GALACTOC'
             }

ctypeMap = {'Frequency'      : 'FREQ',
            'Stokes'         : 'STOKES',
            'Declination'    : 'DEC-',
            'Right Ascension': 'RA--',
            'Longitude'      : 'GLON',
            'Latitude'       : 'GLAT',
            'VELOCITY'       : 'VELO'
            }

projectionMap = { 'SIN': '-SIN',
                  'TAN': '-TAN',
                  'CAR': '-CAR'
                  }

frameValueMap = { 'J2000': '2000',
                  'B1950': '1950',
                  'B1950_VLA': '1950'
                  }

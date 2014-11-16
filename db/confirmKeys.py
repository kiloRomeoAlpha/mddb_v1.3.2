#
#                                                           CyberSKA DQS Project
#
#                                                         mddb.db.confirmKeys.py
#                                                      Kenneth Anderson, 2012-09
#                                                            ken.anderson@ubc.ca
# ------------------------------------------------------------------------------

# $Id$
# ------------------------------------------------------------------------------
__version__      = '$Revision$'[11:-3]
__version_date__ = '$Date$'[7:-3]
__author__       = "k.r. anderson, <ken.anderson@ubc.ca>"
# ------------------------------------------------------------------------------

"""Sets of required header keywords that cannot be defaulted or interpolated."""
# ------------------------------------------------------------------------------

requireFITSKeys = [ 'OBSERVER',
                    'TELESCOP',
                    'INSTRUME',
                    'DATE-OBS',
                    'OBJECT',
                    'BITPIX',
                    'NAXIS',
                    'CTYPE1',
                    'CTYPE2',
                    'CRVAL1',
                    'CRVAL2',
                    'CRPIX1',
                    'CRPIX2'
                    ]

requireCASAKeys = [ 'OBSERVER',
                    'TELESCOPE',
                    #'INSTRUMENT',
                    'MJD-OBS',
                    'TARGET'
                   ] 


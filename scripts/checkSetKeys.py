#!/usr/bin/env python
#
#                                                           CyberSKA DQS Project
#
#                                                        mddb.db.checkSetKeys.py
#                                                      Kenneth Anderson, 2012-03
#                                                            ken.anderson@ubc.ca
# ------------------------------------------------------------------------------

# $Id$
# ------------------------------------------------------------------------------
__version__      = '$Revision$'[11:-3]
__version_date__ = '$Date$'[7:-3]
__author__       = "k.r. anderson, <ken.anderson@ubc.ca>"
#------------------------------------------------------------------------------
checkFitsKeys = [ 'OBJECT', 'INSTRUME', 'TELESCOP', 'OBSERVER' ]

setFitsKeys = {
    'OBJECT'   : 'OBJECT  =               Unknown /mddb insert',
    'OBSERVER' : 'OBSERVER=               Unknown /mddb insert',
    'TELESCOP' : 'TELESCOP=               Unknown /mddb insert',
    'INSTRUME' : 'INSTRUME=               Unknown /mddb insert',
    'TEL_GALFA': 'TELESCOP=               ARECIBO /mddb insert',
    'INS_GALFA': 'INSTRUME=                  ALFA /mddb insert',
    'GMRT_INS' : 'INSTRUME=                  GMRT /mddb insert'
    }

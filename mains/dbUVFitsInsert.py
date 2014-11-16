#!/usr/bin/env python
#
#                                                 CyberSKA CASA Metadata Project
#
#                                                   mddb.mains.dbUVFitsInsert.py
#                                                      Kenneth Anderson, 2012-03
#                                                            ken.anderson@ubc.ca
# ------------------------------------------------------------------------------

# $Id$
# ------------------------------------------------------------------------------
__version__      = '$Revision$'[11:-3]
__version_date__ = '$Date$'[7:-3]
__author__       = "k.r. anderson, <ken.anderson@ubc.ca>"
# ------------------------------------------------------------------------------
"""Module and classes to insert UVFITS metadata into CADC metadata database
(MDDB). Not implemented -- 28-08-2012
"""

from mddb.mains.baseDbInsert import BaseDbInsert

class DbUVFitsInsert(BaseDbInsert):

    def configureOverride(self, hdr, uri, public):
        super(DbUVFitsInsert, self).configureOverride()
        return

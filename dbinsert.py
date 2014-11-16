#!/usr/bin/env python
#
#                                                           CyberSKA DQS Project
#
#                                                               mddb.dbinsert.py
#                                                      Kenneth Anderson, 2012-03
#                                                            ken.anderson@ubc.ca
# ------------------------------------------------------------------------------

# $Id$
# ------------------------------------------------------------------------------
__version__      = '$Revision$'[11:-3]
__version_date__ = '$Date$'[7:-3]
__author__       = "k.r. anderson, <ken.anderson@ubc.ca>"
# ------------------------------------------------------------------------------

"""mddb command line interface."""
# ------------------------------------------------------------------------------

import sys

from mddb.utils import rUtils

# ------------------------------------------------------------------------------

if __name__ == '__main__':

    #-----------------------------------------------------------------#
    #                         Handle Cl Options
    ##----------------------------------------------------------------#

    clArgs = rUtils.handleCLargs(sys.argv)

    #-----------------------------------------------------------------#
    #                       End Handle Cl Options
    ##----------------------------------------------------------------#

    sys.exit(rUtils.run(clArgs))

#!/usr/bin/env python
#
#                                                 CyberSKA CASA Metadata Project
#
#                                                         mddb.config.mddbEnv.py
#                                                      Kenneth Anderson, 2012-03
#                                                            ken.anderson@ubc.ca
# ------------------------------------------------------------------------------

# $Id$
# ------------------------------------------------------------------------------
__version__      = '$Revision$'[11:-3]
__version_date__ = '$Date$'[7:-3]
__author__       = "k.r. anderson, <ken.anderson@ubc.ca>"
# ------------------------------------------------------------------------------

"""Set an environment for metadata database (MDDB) interactions. Default global
mount point is for UBCO Signals Laboratory, /srv partition mounted on 

    signals.siglab.ok.ubc.ca
"""

import os

from ConfigParser import SafeConfigParser as configparser

class MDDBEnv(object):

    def __init__(self):
        
        self.CONFIG   = None
        self.DATASETS = None
        self.HEADERS  = None
        self.OVERRIDE = None
        self.VALIDATE = None
        self.logs     = None
        self.scripts  = None
                          
        self.server     = None
        self.database   = None
        self.schema     = None
        self.collection = None


    def configure(self, configFile):
        """Caller passes a config file.  Method modifies database connection
        and DQS directory attributes values from initial Nones.

        Provides CAOM database configuration ('x.config') and defaults
        ('x.defaults') files, found respectively under DQS/CONFIG, DQS/DEFAULTS.
        Caller picks appropos file.

        parameters: <string>, mddb config file, default 'mddb.cfg'
        return:     <void>,   configured instance attributes
        """

        conf = configparser()
        conf.read(configFile)

        self.configFile = configFile

        self.CONFIG   = conf.get('dqs_dirs','config')
        self.DATASETS = conf.get('dqs_dirs','datasets')
        self.HEADERS  = conf.get('dqs_dirs','header')
        self.OVERRIDE = conf.get('dqs_dirs','override')
        self.VALIDATE = conf.get('dqs_dirs','validate')
        self.logs     = conf.get('dqs_dirs','logs')
        self.scripts  = conf.get('dqs_dirs','scripts')
        
        self.server     = conf.get('database','server')
        self.database   = conf.get('database','database')
        self.schema     = conf.get('database','schema')
        self.collection = conf.get('database','collection')

        self.executable = conf.get('execute','executable')

        # Providing CAOM configuration ('.config') and defaults ('.defaults')
        # files, found respectively under DQS/CONFIG, DQS/DEFAULTS.

        self.cimageDBConfig = conf.get('configs','cimageconfig')
        self.cimage2dDBConfig = conf.get('configs','cimage2dconfig')
        self.cimage3dDBConfig = conf.get('configs','cimage3dconfig')
        self.fitsDBConfig   = conf.get('configs','fitsconfig')
        self.fits2dDBConfig = conf.get('configs','fits2dconfig')
        self.fits3dDBConfig = conf.get('configs','fits3dconfig') 
        self.uvfitsDBConfig = conf.get('configs','uvfitsconfig')
        self.uvmsDBConfig   = conf.get('configs','uvmsconfig')

        self.fitsDBDefault   = conf.get('config_defaults','fitsdefault')
        self.uvfitsDBDefault = conf.get('config_defaults','uvfitsdefault')
        self.cimageDBDefault = conf.get('config_defaults','cimagedefault')
        self.uvmsDBDefault   = conf.get('config_defaults','uvmsdefault')

        return

#!/usr/bin/env python
#
#                                                 CyberSKA CASA Metadata Project
#
#                                                          mddb.utils.f2cArgs.py
#                                                      Kenneth Anderson, 2012-03
#                                                            ken.anderson@ubc.ca
# ------------------------------------------------------------------------------

# $Id$
# ------------------------------------------------------------------------------
__version__      = '$Revision$'[11:-3]
__version_date__ = '$Date$'[7:-3]
__author__       = "k.r. anderson, <ken.anderson@ubc.ca>"
# ------------------------------------------------------------------------------
"""Module and class provides an argument set for executing fits2caom under the
a calling class method. Insertion of respective metadata into CADC database 
(MDDB).
"""

# /////////////////////////////////////////////////////////////////////////////#
# Default DQS at Signals Lab, UBCO
# siglab_dqs = '/srv/cyberska/DQS'
# executable = 'fits2caom'
#
# Deprecated. Replaced by config file.
# nominally mddb.cfg in the mddb package
# -kra 23-03-2012
# /////////////////////////////////////////////////////////////////////////////#

from os.path import join
from ConfigParser import SafeConfigParser as configparser
from ConfigParser import NoOptionError

from mddb.config.mddbEnv import MDDBEnv

class F2CArgs(object):
    
    def __init__(self, configFile=None):
        """Constuctor returns an F2CArgs instance. All other functionality
        is called via supplied methods.
        """

        self.mddb_env = MDDBEnv()
        if configFile: self.mddb_env.configure(configFile)
        else: self.mddb_env.configure()

        
    def buildCmdLine(self, collId, override, config, defaults, uri):
        """Builds the fits2caom command line for use by caller.
        
        parameters: <string>, <string>, <string>, <string>, <string>
                    collId:   arbitrary collection id for db insert
                    override: override file path
                    config:   db config file path 
                    defaults: db defaults file path
                    uri:      URI to CyberSKA dataset platform resource, 
                        eg.,
                        www.cyberska.org/pg/file/read/18868/3mm-continuum-on-m100

        return:     <list>, built fits2caom command line.

        """
        cmd = []
        cmd.append(self.mddb_env.executable)

        # insert boolean switches 
        cmd = self.__cmdSwitches(cmd)
        logname = 'file_guid_'+collId+'.log'
        logFileName = join(self.mddb_env.logs,logname)

        cmd.extend(['--server='    +self.mddb_env.server,
                    '--database='  +self.mddb_env.database,
                    '--schema='    +self.mddb_env.schema,
                    '--collection='+self.mddb_env.collection,

                    '--collectionID='+collId,
                    '--uri='         +uri,
                    '--log='         +logFileName,
                    '--config='      +config,
                    '--overrides='   +override,
                    '--defaults='    +defaults
                    ])
        return cmd


    #################################### prive #################################

    def __cmdSwitches(self,cmd):
        """Extend command line with boolean switches in config file.
        The verbose switch for fits2caom appears to be unique as the only 
        short option available, hence a single '-' opt.
        """
        boolOpts = 'switches'

        conf = configparser()
        conf.read(self.mddb_env.configFile)
        opts = conf.options(boolOpts)
        for opt in opts:
            try: 
                assert conf.getboolean(boolOpts,opt)
                if opt == 'verbose': cmd.extend(['-v'])
                else: cmd.extend(['--'+opt])
            except AssertionError: pass
            except ValueError: pass
            except NoOptionError: pass
        return cmd

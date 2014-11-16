#!/usr/bin/env python
#
#                                                           CyberSKA DQS Project
#
#                                                     mddb.mains.baseDbInsert.py
#                                                      Kenneth Anderson, 2012-06
#                                                            ken.anderson@ubc.ca
# ------------------------------------------------------------------------------

# $Id$
# ------------------------------------------------------------------------------
__version__      = '$Revision$'[11:-3]
__version_date__ = '$Date$'[7:-3]
__author__       = "k.r. anderson, <ken.anderson@ubc.ca>"
# ------------------------------------------------------------------------------

"""Module provides base class for CAOM DB insertion of all metadata types CADC
metadata database (MDDB).
"""

import os

from subprocess import Popen, CalledProcessError, PIPE, STDOUT
from shutil     import copyfile
from datetime   import date

from mddb import mddbVersion

from mddb.db     import confirmKeys
from mddb.config import mddbEnv
from mddb.utils  import f2cArgs


class BaseDbInsert(object):

    def __init__(self, configFile, verbose):
        """Constructor for the base insert class. Builds the environment.
        The datasetType is determined by an upper layer, and the appropriate
        subclass is called.  This class should be not be called directly.
        It provides no data engineering of header data into CAOM compatible.
        That is up to the apprpriate subclass and is based on the datasetType,
        i.e. FITS, CASA Image, UVFITS, UV MS. Each of these types will be
        provided a specific subclass in this package.
        """
        self.verbose = verbose
        self.validationMsg  = []
        self.configFile = configFile
        self.dbEnv = mddbEnv.MDDBEnv()
        self.dbEnv.configure(configFile)

    def buildOverride(self, header, uri, public):
        """This method receives a filename as a path to a textual header file,
        and a URI to the described data resource. The file must be either a
        pure header or a header as produced by the metaData package.
        The file can have an arbitrary location, but the buildOverride() method
        will put a copy in the MDDBEnv.HEADERS directory as a matter of record.
        Method will build a full override file ready for MDDB insertion. If
        no path is given to the header, and the file is not found in '.',
        the MDDBEnv.DATASETS directory is applied. The public parameter is a 
        boolean indicating public access or not.

        parameters: <string>, <string>, <bool> header name, uri, public
        return:     <string>, string indicating file written
        """

        fpath, fname = os.path.split(header)
        overrideName = os.path.splitext(fname)[0]+".override"
        newHdr       = os.path.join(self.dbEnv.HEADERS,fname)

        if not fpath:
            if os.path.isfile(header):
                copyfile(header,newHdr)
            elif os.path.isfile(os.path.join(self.dbEnv.DATASETS,fname)):
                    copyfile(os.path.join(self.dbEnv.DATASETS,fname),newHdr)
            else:
                if not os.path.isfile(newHdr):
                   raise IOError, "Cannot find header: "+fname
                else: pass
        else: 
            copyfile(header,newHdr)

        overrideLines = self.configureOverride(newHdr,uri, public)
        self.signature(overrideLines)
        if self.verbose: self.printOverride(overrideLines)
        ofile = self.writeOverride(overrideLines,overrideName)
        if self.verbose:
            print "\nWrote override file:\t",os.path.join(self.dbEnv.OVERRIDE,ofile)
        return ofile

    def configureOverride(self):
        """Abstract method. This method must be implemented in the subclass, 
        as each metadata data type will require a specific set of data
        engineering tasks. This method bundles the calls to these private methods,
        examples of which will be to validate, check coordinate reference system,
        insert CD matrix, insert DB keys, and various other dreadfully tedious chores.

        parameters: <void>
        return:     <void>
        """
        err = "This method must be implemented in the subclass."
        raise NotImplementedError, err
        return

    def signature(self, olines):
        """Add a data engineering signature."""
        olines.append("ENGINEER=\t\t"+ mddbVersion.pkg_name +" v"+mddbVersion.version)
        return

    def confirmOverride(self, ofile, ftype):
        """This method confirms the presence of keyword subsets for each data type, 
        FITS, CASA Image, UVFits, and UV MS. The method should return True on successful
        testing, or the filename of a validation error/warning file.

        parameters: <string>, <string>, <string>, override fileaname, filetype, collid
        return:     <void>
        """
        confirmErr  = "VO compliance metadata not found: "
        keysActual  = []
        keysMissing = []
        messageTypes= []

        if ftype == 'image/fits-image':
            checkKeys = confirmKeys.requireFITSKeys
        elif ftype == 'image/ms-image':
            checkKeys = confirmKeys.requireCASAKeys
        elif ftype == 'image/fits-uvw':
            raise NotImplementedError
        elif ftype == 'image/ms-uvw':
            raise NotImplementedError

        olines = open(ofile).readlines()
        for line in olines:
            keysActual.append(line.split('=',1)[0].strip())

        for ckey in checkKeys:
            try: assert(ckey in keysActual)
            except AssertionError:
                keysMissing.append(ckey)
                continue
        if keysMissing:
            for key in keysMissing:
                self.validationMsg.append(("ERROR:",confirmErr+key))
        for msgType,msg in self.validationMsg:
            messageTypes.append(msgType.strip())
        vfile = self.writeValidation(ofile)
        return messageTypes

    def printOverride(self, lines):
        """Print the override lines to stdout.

        parameters: <list>
        return:     <void>
        """
        for line in lines: print line
        return

    def writeOverride(self, overrideLines, overrideName):
        """Write the override file actual into $DQS/OVERRIDE.

        parameters: <list>, <string> list of override header lines, override name
        return:     <string> overrride file name 
        """
        overrideFile = os.path.join(self.dbEnv.OVERRIDE,overrideName)
        ovride = open(overrideFile,'w')
        for line in overrideLines:
            ovride.write(line+"\n")
        ovride.close()
        return overrideFile

    def writeValidation(self, ofile):
        """Write a validation file from the self.validationMsg object."""
        opath,oname = os.path.split(ofile)
        vname = os.path.splitext(oname)[0]+".valid"
        vfile = os.path.join(self.dbEnv.VALIDATE,vname)
        vfob = open(vfile,'w')
        vfob.write("# MDDB Validation report for "+ofile+"\n")
        vfob.write("# Written "+date.today().isoformat()+"\n")
        vfob.write("# Package Name: "+mddbVersion.pkg_name+"\n")
        vfob.write("# Package Version: "+mddbVersion.version+"\n\n")
        for level, msg in self.validationMsg:
            vfob.write(level+" "+msg+"\n")
        vfob.close()
        del vfob
        if self.verbose: print "Wrote valid file:\t",vfile
        return vfile
        

    def executeInsert(self, collid, oride, uri):
        """Run fits2caom, called from super() in the subclass. Subclasses
        *must* define 

        self.cfgf
        self.deff

        which are the CAOM db config, defaults files, respectively.
       
        parameters: <string>, <string>, <string>, collection id, override file, uri
        return:     <void>
        """

        fargs= f2cArgs.F2CArgs(self.configFile)
        cmd  = fargs.buildCmdLine(collid, oride, self.cfgf, self.deff, uri)
        if self.verbose:
            print "fits2caom command line args::"
            print "++++++++++++++"
            for carg in cmd:
                print "\t",carg
            print "++++++++++++++"
        try:
            dbiproc = Popen(cmd, stdout=PIPE, stderr=PIPE)
            sout,serr = dbiproc.communicate()
            print sout,serr
        except CalledProcessError, err:
            print "Remote process call failed:",err
        
        return
        
            
    ################################ prive #################################   
    # private methods must be implemented by subclasses.


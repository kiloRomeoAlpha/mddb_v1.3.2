#!/usr/bin/env python
#
#                                                           CyberSKA DQS Project
#
#                                                           mddb.utils.rUtils.py
#                                                      Kenneth Anderson, 2012-03
#                                                            ken.anderson@ubc.ca
# ------------------------------------------------------------------------------

# $Id$
# ------------------------------------------------------------------------------
__version__      = '$Revision$'[11:-3]
__version_date__ = '$Date$'[7:-3]
__author__       = "k.r. anderson, <ken.anderson@ubc.ca>"
# ------------------------------------------------------------------------------

"""Some utility funcs for command line interface."""
# ------------------------------------------------------------------------------

import sys
import getopt
import urlparse
from   datetime import date

from os import getenv
from os.path import basename, join, isfile, expanduser, split, splitext

from mddb import mddbVersion

from mddb.mains import dbFitsInsert
from mddb.mains import dbCImageInsert
from mddb.mains import dbUVFitsInsert # -- future implementation, raise NotImplementError
from mddb.mains import dbMSInsert     # -- future implementation, raise NotImplementError

# ------------------------------------------------------------------------------

def usage(mod):
    useBurp = '\n\t'+mod+' running '+mddbVersion.pkg_name+' v'\
        +mddbVersion.version +\
        '\n\n\tUsage: '+ mod + ' '\
        '[--help] ' \
        '[--public] ' \
        '[--verbose]' \
        '[--nodb]' \
        '[--config=<DQS-config-file>] ' \
        '--mtype=<mime-type> ' \
        '--hdr=<hdrfile> --uri=<uri> \n\n\t' \
        'Three (3) keyword arguments are required. \n\n\t'\
        '--mtype= \t<mime-type> of dataset to be inserted\n\t\t'\
                 '\tOne (1) of CyberSKA metadata mime-types:\n\n\t\t'\
                 '\t\timage/fits-image, \n\t\t'\
                 '\t\timage/ms-image, \n\t\t'\
                 '\t\timage/fits-uvw,\n\t\t'\
                 '\t\timage/ms-uvw\n\n\t'\
        '--hdr=   \t<header file for the dataset>\n\t'\
        '--uri=   \t<URI to CyberSKA platform page, or download link>,\n\t\t'\
                 '\twhich should look like,\n\n\t\t'\
                 '\thttp://www.cyberska.org/pg/file/read/<nnnnn>, or\n\t\t'\
                 '\thttp://dms.cyberska.org:8080/dlmanager/getfile?fileid=<nnnnnn>\n\n\t'\
        '--public\tThe dataset metadata are publicly available.\n\t'\
        '--verbose\tTurn on stdout messages.\n\t' \
        '--nodb\t\tNo DB insert. executeInsert() is not called.\n\n\t'\
        'A user may pass a DQS configuration file, i.e., an mddb.cfg:\n\n\t'\
        '--config= \t<config-file> path to a DQS config file.\n\n\t'\
        '\t\tIf "--config" is not provided at the command line, a search \n\t'\
        '\t\tfor "mddb.cfg" will occur on ~ and $DQS.  An Exception is\n\t'\
        '\t\traised if an mddb.cfg file cannot be found.\n\n\t'\
        '--help \t\tThis message.\n\n'
    return useBurp


def handleCLargs(args):
    mod = basename(sys.argv[0])
    long_options = ['help','public','verbose', 'nodb','mtype=','hdr=','uri=','config=']
    required     = ['--mtype', '--hdr', '--uri']
    nrequired    = len(required)
    Nreqd        = 0
    valid_mtypes = ['image/fits-image',
                    'image/ms-image',
                    'image/fits-uvw',
                    'image/ms-uvw'
                    ]
    try:
        opts, arg = getopt.getopt(sys.argv[1:],'',long_options)
    except getopt.GetoptError,err:
        print "Option parsing recieved an error:"
        print err
        sys.exit(usage(mod))
        
    if arg:
        print "Unexpected arg(s):",arg
	sys.exit(usage(mod))

    # Three (3) arguments are required, see 'required' list. 
    # --mtype   mime-type of the dataset to be inserted
    # --hdr     header file for the dataset
    # --uri     URI to the CyberSKA file platform page,
    #           which hould look like,
    #           www.cyberska.org/pg/file/read/<nnnnn>/<page-name>
    # --public  indicates that the dataset is publicly accessible.
    # --verbose Turns on stdout messages.
    # --config  may be passed. This is a path to an mddb.cfg file.
    # --nodb    No DB interaction; executeInsert() is not called.

    cl_args = []
    if opts:
	for o, a in opts:
	    if o in ("--help",):
		sys.exit(usage(mod))
            if o in ("--public"):
                cl_args.append(o)
            if o in ("--verbose"):
                cl_args.append(o)
            if o in ("--nodb"):
                cl_args.append(o)
	    if a and o in required:
                Nreqd +=1
		cl_args.append(o+"="+a)
            elif a:
                cl_args.append(o+"="+a)
    else: sys.exit(usage(mod))

    # Ensure the required three (3) args have been passed.
    if Nreqd != nrequired:
        print "\n\tMissing required arguments (see usage)."
        sys.exit(usage(mod))

    # Ensure valid CyberSKA mime-type.
    err = "\nError:: Unrecognized mime-type:"
    for kwarg in cl_args:
        if '--mtype' in kwarg:
            key,val = kwarg.split('=')
            if val not in valid_mtypes:
                print err,val
                sys.exit(usage(mod))
        else: continue
    return cl_args


def parseArgs(clargs):
    pargs = {}
    pargs['public']  = False    # permission default is private.
    pargs['verbose'] = False    # default no stdout messaging
    pargs['nodb']    = False    # default runs executeInsert()

    for kwarg in clargs:
        if '--public' in kwarg:
            pargs['public'] = True
            continue
        if '--verbose' in kwarg:
            pargs['verbose'] = True
            continue
        if '--nodb' in kwarg:
            pargs['nodb'] = True
            continue
        if '--uri' in kwarg:
            urlset = urlparse.urlparse(kwarg)
            key,val = (urlset.path).split('=')
            val= val+"?"+urlset.query
            pargs[key.strip('--')] = val
            continue
        else:
            key,val = kwarg.split('=')
            pargs[key.strip('--')] = val

    if 'config' in pargs:
        cfgFile = expanduser(pargs['config'])
        if isfile(cfgFile): pargs['config'] = cfgFile
        else: raise RuntimeError(pargs['config']+" Not found.")
    else:
        cfgFile = findCfg()
        pargs['config'] = cfgFile
    return pargs


def findCfg():
    """Hunt down an 'mddb.cfg' file, first in ~, then in $DQS. Raise expcetion
    if none found.
    
    parameters: <void>
    return:     <string>, mddb.cfg path
    """
    noEnvVar     = 'mddb.cfg not found in ~; DQS environment variable not defined.'
    filenotfound = 'mddb configuration file NOT found. Check ~ and $DQS'

    cfgFile  = None
    testhome = join(getenv('HOME'),'mddb.cfg')

    if isfile(testhome):
        cfgFile = testhome
    else:
        try:
            dqsFile = join(getenv('DQS'),'mddb.cfg')
            if not isfile(dqsFile):
                raise RuntimeError(filenotfound)
        except AttributeError:
            raise RuntimeError(noEnvVar)
        if isfile(dqsFile):
            cfgFile = dqsFile
        else:
            raise RuntimeError(filenotfound)
    return cfgFile


def getCollId(uri):
    """Get the CyberSKA file_guid id or a fileid value from a passed URI string.
    A cyberska.org URI will be of the form,

    http://www.cyberska.org/pg/file/read/<nnnnn>/<page-name>,       or
    http://dms.cyberska.org:8080/dlmanager/getfile?fileid=<nnnnn>
    
    where <nnnnn> is a file_guid ID or fileid

    parameters: <string>, cyberska.org URI string
    return:     <string>, ID value
    """
    purl = urlparse.urlparse(uri)
    if purl.query:
        try:
            collid = urlparse.parse_qs(purl.query)['fileid'][0]
        except AttributeError:
            collid = purl.query.split('=')[1]
    else:
        collid = split(purl.path)[-1]
    return collid


# v1.1 added '--nodb' switch, halts processing, does not call 
# executeInsert()

def run(clArgs):
    useFits    = useUVFits = useCimage = useUVMSet = False
    pArgs      = parseArgs(clArgs)
    uri        = pArgs['uri']
    hdrFile    = pArgs['hdr']
    fileType   = pArgs['mtype']
    configFile = pArgs['config']
    public     = pArgs['public']
    verbose    = pArgs['verbose']
    nodbInsert = pArgs['nodb']
    collid     = getCollId(uri)
    abortString="Database insert aborted. See validation file."

    # Determine class use by fileType
    if fileType == 'image/fits-image':
        useFits   = True
    elif fileType == 'image/ms-image':
        useCimage = True
    elif fileType == 'image/fits-uvw':
        useUVFits = True
    elif fileType == 'image/ms-uvw':
        useUVMSet = True

    if verbose:
        print "\n\n\tThis is mddb, v"+mddbVersion.version
        print "\t"+("-")*19+"\n"
        print "\n\nConfiguration parameters:"
        print "__________________"
        print "DB config file:\t",configFile
        print "DB coll ID:\t",collid
        print "Header file:\t",hdrFile
        print "MIME-type:\t",fileType
        print "Resource URI:\t",uri
        print "Public Release:\t",public
        print "__________________\n"


    if useFits:
        dbtask  = dbFitsInsert.DbFitsInsert(configFile, verbose)
        override= dbtask.buildOverride(hdrFile, uri, public)
        msgTypes= dbtask.confirmOverride(override, fileType)
        if nodbInsert:
            sys.exit("No DB request. Done")
        elif not "ERROR:" in msgTypes: 
            dbtask.executeInsert(collid, override, uri)
        else:
            if verbose: print abortString
            sys.exit("-1")
    elif useCimage:
        dbtask  = dbCImageInsert.DbCImageInsert(configFile, verbose)
        override= dbtask.buildOverride(hdrFile, uri, public)
        msgTypes= dbtask.confirmOverride(override, fileType)
        if nodbInsert:
            sys.exit("No DB request. Done")
        elif not "ERROR:" in msgTypes:
            dbtask.executeInsert(collid, override, uri)
        else:
            if verbose: print abortString
            sys.exit("-1")
    elif useUVFits:
        dbtask  = dbUVFitsInsert.DbUVFitsInsert(configFile, verbose)
        try: override= dbtask.buildOverride(hdrFile,uri,public)
        except NotImplementedError, err:
            writeNoGo(hdrFile,fileType,dbtask.dbEnv.VALIDATE)
            sys.exit("-2")
        msgTypes= dbtask.confirmOverride(override,fileType)
        if nodbInsert:
            sys.exit("No DB request. Done")
        elif not "ERROR:" in msgTypes:
            dbtask.executeInsert(collid,override,uri)
        else:
            if verbose: print abortString
            sys.exit("-1")
    elif useUVMSet:
        dbtask  = dbMSInsert.DbMSInsert(configFile, verbose)
        try: override= dbtask.buildOverride(hdrFile,uri,public)
        except NotImplementedError, err:
            writeNoGo(hdrFile,fileType,dbtask.dbEnv.VALIDATE)
            sys.exit("-2")
        msgTypes= dbtask.confirmOverride(override,fileType)
        if nodbInsert:
            sys.exit("No DB request. Done")
        elif not "ERROR:" in msgTypes:
            dbtask.executeInsert(collid,override,uri)
        else:
            if verbose: print abortString
            sys.exit("-1")
    return


def writeNoGo(hdr, mtype, where):
    """Write a .nogo file when NotImplementedError is raised.

    parameters: <string>, <string, <string>
    return:     <void>
    """

    path,hfile=split(hdr)
    head = splitext(split(hdr)[1])[0]
    nogoFile = join(where,head)+".nogo"

    nogo = open(nogoFile,"w")
    nogo.write("# MDDB Nogo file written for header file: "+hdr+"\n")
    nogo.write("# Written "+date.today().isoformat()+"\n")
    nogo.write("# Package Name: "+mddbVersion.pkg_name+"\n")
    nogo.write("# Package Version: "+mddbVersion.version+"\n\n")
    nogo.write("File, "+hdr+", is a nogo for CAOM v1 database insertion.\n\n")
    nogo.write("Received a NotImplementedError\n")
    nogo.write("Unsupported MIME-TYPE: "+mtype)
    return

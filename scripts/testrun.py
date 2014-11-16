#!/usr/bin/env python
#
#                                                           CyberSKA DQS Project
#
#                                                        mddb.scripts.testrun.py
#                                                      Kenneth Anderson, 2012-03
#                                                            ken.anderson@ubc.ca
# ------------------------------------------------------------------------------

from public_uris_fullset import dbinsertDownloadArgs
#from public_uris import dbinsertArgs, dbinsertDownloadArgs
#from public_uris import dbinsertDownloadArgs

from subprocess import Popen, CalledProcessError, PIPE, STDOUT

if __name__ == '__main__':
    
    for argset in dbinsertDownloadArgs:
        cmd = []
        cmd.append('./dbinsert')
        if len(argset) != 3: raise IOError, "short argset @ "+argset[1]
        argset[0]='--mtype='+argset[0]
        argset[1]='--uri='+argset[1]
        argset[2]='--hdr='+argset[2]
        argset.append('--public')
        argset.append('--nodb')
        argset.append('--verbose')
        cmd.extend(argset)
        print cmd
        try:
            dbiproc = Popen(cmd, stdout=PIPE, stderr=PIPE)
            sout,serr = dbiproc.communicate()
            print sout,serr
        except CalledProcessError, err:
            print "Remote process call failed:",err

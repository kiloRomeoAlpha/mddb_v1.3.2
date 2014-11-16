#!/usr/bin/env python
#
#                                                           CyberSKA DQS Project
#
#                                                    mddb.utils.keyAssertions.py
#                                                      Kenneth Anderson, 2012-11
#                                                            ken.anderson@ubc.ca
# ------------------------------------------------------------------------------

# $Id$
# ------------------------------------------------------------------------------
__version__      = '$Revision$'[11:-3]
__version_date__ = '$Date$'[7:-3]
__author__       = "k.r. anderson, <ken.anderson@ubc.ca>"
# ------------------------------------------------------------------------------
projection_types = ['DEF','AZP','TAN','SIN','STG','ARC','ZPN','ZEA','AIR','CYP',
                    'CAR','MER','CEA','COP','COD','COE','COO','BON','PCO','SFL',
                    'PAR','AIT','MOL','CSC','QSC','TSC', 'SZP'
                    ]
# ------------------------------------------------------------------------------


from checkSetKeys import checkFitsKeys, setFitsKeys

def checkSetKeys(lines):
    sansKeys = []
    galfa    = False
    telescop = False

    for checkKey in checkFitsKeys:
        keyThere = assertKey(checkKey, lines)
        if not keyThere:
            sansKeys.append(checkKey)
        else:
            if checkKey == 'OBJECT' and 'GALFACT' in keyThere:
                galfa    = True
            if checkKey == 'TELESCOP':
                telescop = True
                teleValu = keyThere
            continue

    for skey in sansKeys:
        if skey == 'TELESCOP'   and galfa is True:
            lines.insert(3,setFitsKeys['TEL_GALFA'])
        elif skey == 'INSTRUME' and galfa is True:
            lines.insert(3,setFitsKeys['INS_GALFA'])
        elif skey == 'INSTRUME' and telescop is True:
            lines.insert(3,setInstrumentLineBasedOnTelescopeValue(teleValu))
        else: lines.insert(3,setFitsKeys[skey])
    return

def assertKey(checkKey, lines):
    keyPresent = ''
    for line in lines:
        key = getKeyWord(line)
        if key == checkKey:
            keyPresent = getStringVal(line)
            break
        else: continue
    return keyPresent

# imitating java  ...

def setInstrumentLineBasedOnTelescopeValue(tvalue):
    return 'INSTRUME=                  %s /mddb insert\n' % tvalue


# ------------------------------------------------------------------------------


def checkSetObserver(lines):
    """assert keyword OBSERVER; set to 'Unknown' if false."""
    obsrvrKey = 'OBSERVER=               Unknown / mddb inserted\n'
    obsrvr    = False
    for line in lines:
        key = getKeyWord(line)
        if key == getKeyWord(obsrvrKey):
            obsrvr = True
            break
        else: continue
    if not obsrvr:
        print "Inserting OBSERVER key as 'Unknown'"
        lines.insert(3,obsrvrKey)
    return obsrvr

def checkSetTele(lines):
    """assert keyword TELESCOP; set to 'Unknown' if false."""
    teleKey    = 'TELESCOP=               Unknown / mddb inserted\n'
    areciboKey = 'TELESCOP=               Arecibo / mddb inserted\n'
    tele    = False
    for line in lines:
        key = getKeyWord(line)
        if key == getKeyWord(teleKey):
            tele = True
            break
        else: continue
    if not tele:
        arecibo = setArecibo(lines)
        if arecibo:
            print "Found GLAFACTS in OBJECt field: TELESCOPE= Arecibo"
            print "Inserting TELESCOP key as 'Arecibo'"
            lines.insert(3, areciboKey)
        else:
            print "Inserting TELESCOP key as 'Unknown'"
            lines.insert(3, teleKey)
    return tele

def checkSetInstr(lines):
    """assert keyword INSTRUME; set to 'Unknown' if false."""
    instruKey= 'INSTRUME=               Unknown / mddb inserted\n'
    instru   = False
    for line in lines:
        key = getKeyWord(line)
        if key == getKeyWord(instruKey):
            instru = True
            break
        else: continue
    if not instru:
        print "Inserting INSTRUME key as 'Unknown'"
        lines.insert(5, instruKey)
    return instru

def setArecibo(lines):
    """return 'Arecibo' if GALFACTS in OBJECT value."""
    objKey     = 'OBJECT'
    objectTest = 'GALFACTS'
    arecibo    = False
    
    for line in lines:
        key = getKeyWord(line)
        if key == objKey:
            val = getStringVal(line)
            if objectTest in val:
                arecibo = True
                break
        else: continue
    return arecibo

# ---------------------------------- utils --------------------------------------

def getNumVal(line):
    """Pare a numeric value from a header line string.
    
    parameters: <string>
    return:     <float>
    """
    return float(line.split('=')[1].split('/')[0].strip())

def getStringVal(line):
    """Pare string value from a header line string.
    
    parameters: <string>
    return:     <string>
    """
    return line.split('=')[1].split('/')[0].strip()

def getKeyWord(line):
    """Pare a keyword from a header line string.
    
    parameters: <string>
    return:     <string>
    """
    return line.split('=')[0].strip()


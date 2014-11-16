#!/usr/bin/env python
#
#                                                           CyberSKA DQS Project
#
#                                                     mddb.mains.dbFitsInsert.py
#                                                      Kenneth Anderson, 2012-03
#                                                            ken.anderson@ubc.ca
# ------------------------------------------------------------------------------

# $Id$
# ------------------------------------------------------------------------------
__version__      = '$Revision$'[11:-3]
__version_date__ = '$Date$'[7:-3]
__author__       = "k.r. anderson, <ken.anderson@ubc.ca>"
# ------------------------------------------------------------------------------

"""Module and class to insert FITS metadata into CADC metadata database (MDDB).
"""

from types import NoneType
from math  import sin, cos, radians
from datetime import date

from mddb.mains.baseDbInsert import BaseDbInsert

from mddb.convert import keymaps
from mddb.convert import mjdConversions
from mddb.db      import xDBKeys, checkSetKeys


class FitsHeaderError(IndexError):
    """Raise this error when required metadata are missing from a FITS
    header.
    """
    pass


class DbFitsInsert(BaseDbInsert):

    def configureOverride(self, hdr, uri, public):
        """Bundles calls to private methods to validate, check coordinate
        reference system, insert CD matrix, insert DB keys, and various other
        dreadfully tedious chores.
        
        parameters: <string>, <string>, <bool> file name, uri, public switch
        return:     <list>,   header lines, list of strings
        """
        flines = self.__validate(hdr)
        self.__assertSimple(flines)
        self.__setMetaRelease(flines, public)
        self.ndims = self.__naxis(flines)
        self.__assertDirectionCoord(flines)
        self.__setSpectralCoord(flines)
        self.__checkSetKeys(flines)
        self.__setFreqUnit(flines)
        self.__setSpecSys(flines)
        self.__setCoordSys(flines)
        try: self.__insertCDMatrix(flines)
        except FitsHeaderError: pass
        self.__insertDBKeys(flines, uri)
        try: self.__dates2mjd(flines)
        except FitsHeaderError: pass
        return flines

    def executeInsert(self, collid, oride, uri):
        """Run fits2caom.

        parameters: <string>, <string>, <string> collection id, override file, uri
        return:     <void>
        """
        if   self.ndims == 2: self.cfgf = self.dbEnv.fits2dDBConfig
        elif self.ndims == 3: self.cfgf = self.dbEnv.fits3dDBConfig
        elif self.ndims == 4: self.cfgf = self.dbEnv.fitsDBConfig
        else: raise FitsHeaderError("Cannot handle "+str(self.ndims)+"D image.")
        self.deff = self.dbEnv.fitsDBDefault
        super(DbFitsInsert, self).executeInsert(collid, oride, uri)
        return

      
    ################################ prive #################################   

    def __validate(self, fitsHdr):
        """Method determines whether the file passed by Caller is a properly
        formed textual fits header, as a '.hdr' file written by metaData.
        This will be the full path name to the copy of the fits header placed in
        MDDBEnv.HEADERS

        parameters: <string>, header file name
        return:     <list>, list of read lines from fits header file.
        """
        errstr='Invalid FITS type header file. Missing keyword signifier: SIMPLE'
        
        flines = open(fitsHdr).readlines()
        strippedLines = self.__stripComment(flines)
        try:
            assert("SIMPLE" in strippedLines[0])
        except AssertionError: 
            try:
                assert("SIMPLE" in strippedLines[1])
            except AssertionError:
                self.validationMsg.append(("ERROR:",errstr))
        return strippedLines

    def __assertSimple(self, lines):
        """Test that the passed FITS file is simple and not multi-extension.
        MEF handling is not implemented. Add an ERROR to the validationMsg
        list if an MEF if detected.

        parameters: <list>, header lines
        return:     <void>
        """
        errstr = "[N]EXTEND keyword(s) detected. Cannot insert MEF files"
        xtendKeys = ['EXTEND','NEXTEND']
        for line in lines:
            key = self.__getKeyWord(line)
            try:
                assert(key in xtendKeys)
                self.validationMsg.append(("ERROR:",errstr))
                break
            except AssertionError: continue
        return

    def __setMetaRelease(self, lines, public):
        """Set the Meta Release Date as the override keyword, MRELEASE, with
        the current date.  This is needed for CAOM database queries to 
        'see' the metadata.
        """
        metaReleaseKey = 'MRELEASE'
        if public:
            newline = metaReleaseKey + '=\t\t' + date.today().isoformat()
        else:
            newline = metaReleaseKey + '=\t\t2099-01-01'
        lines.insert(2,newline)
        self.validationMsg.append(("INFO: ","Metadata release date set: " + 
                                   newline.split('=')[1].strip()))
        return

    def __naxis(self, lines):
        """Return the number of dimensions of the image.

        parameters:  <list>, header lines
        return:      <int>, naxis value
        """
        naxisKey = 'NAXIS'
        for idx in range(len(lines)):
            key = self.__getKeyWord(lines[idx])
            if key == naxisKey:
                naxis = self.__getNumVal(lines[idx])
                break
        return int(naxis)

    def __assertDirectionCoord(self, lines):
        """Determine the presence or lack of a fully specified 'direction' coordinate,
        described in checkSetKeys.directionCodes and checkSetKeys.projectionCodes
        
        parameters: <list>, header lines
        return:     <void> 
        """
        directionError = "VO services require a Direction Coordinate. None Found."
        tcount = 0
        for line in lines:
            if "CTYPE1" in line:
                self.__affirmDirection(line)
                tcount += 1
            if "CTYPE2" in line:
                self.__affirmDirection(line)
                tcount += 1
            if tcount == 2: break
            else: continue

        if not tcount == 2:
            if self.verbose:
                print "FATAL ERROR: Direction Coordinate not found."
            self.validationMsg.append(("ERROR:",directionError))
        return

    def __affirmDirection(self,line):
        directionError = "Unrecognized direction coordinate:: "
        projectionError= "Unrecognized FITS projection code:: "
        dCoord = None
        dProj  = None
        dkey   = self.__getKeyWord(line)
        pvals  = self.__getStringVal(line).split('-')
        dCoord = pvals[0]

        if len(pvals) == 1:
            dProj = ''
        else:
            dProj = self.__getStringVal(line).split('-')[-1]

        if dCoord in checkSetKeys.directionCodes:
            if self.verbose:
                print "Got direction code:", dCoord, "in",dkey
        else:
            if self.verbose:
                print dkey, directionError, dCoord
            self.validationMsg.append(("ERROR:",directionError+dCoord))

        if dProj in checkSetKeys.projectionCodes:
            if self.verbose:
                print "Got projection code:", dProj, "in",dkey
        elif dProj:
            self.validationMsg.append(("ERROR:",projectionError+dProj))
        else:
            self.validationMsg.append(("ERROR:","No parsable projection code"))
        return

    def __setSpectralCoord(self,lines):
        warnmsg = "Spectral coordinate value in %s interpreted as FREQ"
        spectralCoordLine = "%s  =                  FREQ"
        specIdx = None
        for idx in range(len(lines)):
            key = self.__getKeyWord(lines[idx])
            if 'CTYPE' in key:
                sval = self.__getStringVal(lines[idx])
                if sval == 'Frequency':
                    lines.pop(idx)
                    lines.insert(idx,spectralCoordLine % key)
                    self.validationMsg.append(("WARN: ",warnmsg % key))
                    break
                elif sval == 'FREQUENC':
                    lines.pop(idx)
                    lines.insert(idx,spectralCoordLine % key)
                    self.validationMsg.append(("WARN: ",warnmsg % key))
                    break
            else: continue
        return

    def __checkSetKeys(self, lines):
        """Method asserts presence of keywords in the header lines. The set of
        keywords is provided by checkSetKeys.checkFitsKeys list, and currently
        includes 'OBJECT', 'INSTRUME', 'TELESCOP', 'OBSERVER'. Missing keywords
        are set by values specified in checkSetKeys.setFitsKeys dict.

        parameters: <list>, header lines
        return:     <void>
        """
        warnStr  = "Interpolated value: "
        sansKeys = []
        galfa    = False
        telescop = False

        for checkKey in checkSetKeys.checkFitsKeys:
            keyThere = self.__assertKey(checkKey, lines)
            if not keyThere:
                sansKeys.append(checkKey)
            else:
                if checkKey == 'OBJECT' and 'GALFACT' in keyThere:
                    galfa    = True
                elif checkKey == 'TELESCOP':
                    telescop = True
                    teleValu = keyThere
                continue

        for skey in sansKeys:
            if skey == 'TELESCOP'   and galfa is True:
                lines.insert(3, checkSetKeys.setFitsKeys['TEL_GALFA'])
                self.validationMsg.append(("WARN: ",warnStr+checkSetKeys.setFitsKeys['TEL_GALFA']))
            elif skey == 'INSTRUME' and galfa is True:
                lines.insert(3, checkSetKeys.setFitsKeys['INS_GALFA'])
                self.validationMsg.append(("WARN: ",warnStr+checkSetKeys.setFitsKeys['INS_GALFA']))
            elif skey == 'INSTRUME' and telescop is True:
                lines.insert(3,self.__setInstrumentLineBasedOnTelescopeValue(teleValu))
                self.validationMsg.append(("WARN: ",skey+" set to "+teleValu))
            else: lines.insert(3, checkSetKeys.setFitsKeys[skey])
        return

    def __assertKey(self, checkKey, lines):
        """Determine the presence of a passed keyword in lines. Returns a null string
        or the string value if found.

        parameters:  <string>, <list>, keyword, header lines
        return:      <string>, '' or string value found for the passed key.
        """
        keyPresent = ''
        for line in lines:
            key = self.__getKeyWord(line)
            if key == checkKey:
                keyPresent = self.__getStringVal(line)
                break
            else: continue
        return keyPresent

    # imitating java  ...
    def __setInstrumentLineBasedOnTelescopeValue(self, tvalue):
        return 'INSTRUME=                  %s /mddb insert' % tvalue

    def __setSpecSys(self,lines):
        """Set the spectral coordinate reference system, SPECSYS, if not present
        in the header. SPECSYS may be determined from the VELREF keyword value,
        if present. The VELREF value is interpolated to the respective SPECSYS
        string value via the keymaps.velrefMap dict, which implements
        Table 8 of Greisen et al, 2002 and the casacore VELREF bitmap:

            Radio 256+  1 LSRK, 2 HELIOCENT, 3 TOPOCENT, 4 LSRD, 5 GEOCENT,
                        6 SOURCE, 7 GALACTOC

        If neither VELREF nor SPECSYS are found, SPECSYS defaults to 'TOPOCENT'.

        (See Greisen et al, Representation of Spectral Coordinates in FITS,
        2002, Table 8, p. 14)

        parameters: <list>, list of header lines
        return:     <void>
        """
        specsysLine    = 'SPECSYS =              '
        specsysDefault = 'TOPOCENT'
        specDefIndex   = 20
        spec = velr = vindex = False

        for idx in range(len(lines)):
            key = self.__getKeyWord(lines[idx])
            if key == 'SPECSYS':
                spec = True
                break
            elif key == 'VELREF':
                velr = True
                vindex = idx
            else: continue

        if not velr and not spec:
            if self.verbose: print "\n\tWriting default SPECSYS keyword..."
            lines.insert(specDefIndex,specsysLine+specsysDefault)
        elif velr and not spec:
            if self.verbose: print "\n\tFound VELREF keyword. Interpolating ..."
            velrefValue = self.__getNumVal(lines[vindex])
            specsysTerm = keymaps.velrefMap[velrefValue]
            if self.verbose: print "\n\tInterpolated SPECSYS Term:",specsysTerm
            lines.insert(vindex,specsysLine+specsysTerm)
            self.validationMsg.append(("INFO: ","VELREF keyword: "+ str(velrefValue)))
            self.validationMsg.append(("INFO: ","Interpolated SPECSYS Term: "+specsysTerm))
        else: pass
        return

    def __setCoordSys(self, lines):
        """Set the coordinate reference system, if none is specified. This
        coordinate system is defined by keywords, EQUINOX, RADESYS. These may or
        may not be present, though at least one (1) is required for determination.
        The FITS WCS spec (Calabretta & Greisen, A&A, 2002) states a number of 
        defaults based upon the presence and/or absence of these keys.

        If not RADESYS and not EQUINOX :: RADESYS = ICRS

        EQUINOX > 1984 :: RADESYS = FK5
        EQUINOX < 1984 :: RADESYS = FK4
        
        Furthermore, an extant keyword 'EPOCH' is replaced by 'EQUINOX' using
        the value supplied, and RADESYS is written appropros to the value.

        Calabretta & Greisen state that if neither 'EPOCH' nor 'EQUINOX' are
        present, the default EQUINOX shall be 1950.0 (Calabretta & Greisen, A&A,
        2002, p.1082). However, it is the judgement of the CyberSKA project that
        this default specification be overridden here and the value of 2000.0 be
        used instead.

        This method greps the coordinate reference system keywords and values
        from the header lines into a dict for presence testing and evaluation.
        
        parameters: <list>, header lines
        return:     <void>
        """
        hdrErr  = "Incompatible Reference System parameters: RADESYS, EQUINOX"
        eqRef   = "EQUINOX" + " =                "
        radeRef = "RADESYS" + " =                   "
        refSys  = {}
        syskeys = poplist = []
        poppings = 0
        eqIndex = epIndex = radeIndex = refsysIndex = None

        for idx in range(len(lines)):
            key = self.__getKeyWord(lines[idx])
            if key == 'EQUINOX':
                eqIndex = idx
                refSys[key] = self.__getNumVal(lines[idx])
                syskeys.append(key)
                if not refsysIndex: refsysIndex = idx
                continue
            elif key == 'EPOCH':
                epIndex = idx
                refSys[key] = self.__getNumVal(lines[idx])
                syskeys.append(key)
                if not refsysIndex: refsysIndex = idx
                continue
            elif key == 'RADESYS':
                radeIndex = idx
                refSys[key] = self.__getStringVal(lines[idx])
                syskeys.append(key)
                if not refsysIndex: refsysIndex = idx
                continue

            # Sanity checks on extant ref sys keys ...
            # Nominal headers, i.e. ones with both RADESYS and EQUINOX 
            # keywords will *return* 'lines' after true assertions.

            if 'EQUINOX' in syskeys and 'RADESYS' in syskeys:
                if refSys['RADESYS'] == 'FK5':
                    try: assert(refSys['EQUINOX'] == 2000.0)
                    except AssertionError:
                        self.validationMsg.append(("ERROR:","Conflicting RADESYS, EQUINOX"))
                elif refSys['RADESYS'] == 'FK4':
                    try:assert(refSys['EQUINOX'] == 1950)
                    except AssertionError:
                        self.validationMsg.append(("ERROR:","Conflicting RADESYS, EQUINOX"))
                if self.verbose: print "\n\tFound RADESYS and EQUINOX keywords.\n"
                return lines
            elif len(syskeys) == 3: break
            else: pass

        # Expunge ref sys keys, set defaults & reinsert. Expunge 
        # occurs when one (1) or three (3) ref sys keys are found.
        poplist = [epIndex,eqIndex,radeIndex]
        poplist.sort()
        for popindex in poplist:
            if popindex != None:
                lines.pop(popindex-poppings)
                poppings += 1
 
        # Defaults spec'd in Calabretta & Greisen, p.1082
        if 'RADESYS' in syskeys:
            if   refSys['RADESYS'] == 'FK4-NO-E': refSys['EQUINOX'] = 1950.0
            elif refSys['RADESYS'] == 'FK4':      refSys['EQUINOX'] = 1950.0
            elif refSys['RADESYS'] == 'FK5':      refSys['EQUINOX'] = 2000.0
            syskeys.append('EQUINOX')
        
        if 'EPOCH' not in syskeys and 'EQUINOX' not in syskeys:
            refSys['EQUINOX'] = 2000.0
        if 'EPOCH' in syskeys and 'EQUINOX' not in syskeys:
            refSys['EQUINOX'] = refSys['EPOCH']

        if 'RADESYS' not in syskeys:
            if   refSys['EQUINOX'] >= 1984: refSys['RADESYS']='FK5'
            elif refSys['EQUINOX'] <  1984: refSys['RADESYS']='FK4'

        if not refsysIndex:
            refsysIndex = 22

        # Reinsert ref sys post sanity, defaulting
        eqRef   = eqRef + str(refSys['EQUINOX'])
        radeRef = radeRef + str(refSys['RADESYS'])
        if self.verbose: print "\tWriting EQUINOX and RADESYS keywords ...\n"
        lines.insert(refsysIndex,eqRef)
        lines.insert(refsysIndex+1,radeRef)
        self.validationMsg.append(("INFO: ","Wrote EQUINOX: "+str(refSys['EQUINOX'])))
        self.validationMsg.append(("INFO: ","Wrote RADESYS: "+str(refSys['RADESYS'])))
        return

    def __setFreqUnit(self, lines):
        """Ensure the Frequency Units for the overrride are set to 
        'Hz' exactly. This is required by fits2caom. Inhomogeneity exists in
        FITS headers and the spectral units may be represented by literals like
        'HZ' or even 'Hertz'. 'Hz' MUST be the unit for the Frequency axis.

        parameters: <list>, header lines
        return:     <void>
        """
        freqUnitKey   = None
        freqUnitValue = '  =                    Hz'

        for cIndex in range(len(lines)):
            if 'CTYPE' in lines[cIndex] and 'FREQ' in lines[cIndex]:
                 freqIndex   = lines[cIndex].split('=')[0].strip()[-1]
                 freqUnitKey = 'CUNIT'+freqIndex
                 continue
            elif lines[cIndex].split('=')[0].strip() == freqUnitKey:
                freqUnitLine = freqUnitKey+freqUnitValue
                lines.pop(cIndex)
                lines.insert(cIndex,freqUnitLine)
                self.validationMsg.append(("WARN: ","Spectral unit set to Hz"))
                break
            else: continue
        return

    def __insertCDMatrix(self, lines):
        """Determine if a CD matrix is present in the header lines passed by
        the caller.  If no CD matrix is found, select the CDELTn/CROTA[n] keywords,
        calcuate the transformation, and insert the new CDn_n keywords into the 
        header lines. The CDELTA-CDMatrix transformation is performed to the FITS
        specification (Calabretta and Geisen, 2002). N.B. CDELTA1 and CDELTA2 are
        assumed to conform to FITS convention, where CDELTA1 = RA, CDELTA2 = Dec,
        and specified by the above cited FITS standard.

        parameters: <list>, header lines list of strings from FITS header file.
        return:     <void>
        """
        wcsErr = "WCS metadata not found: "
        delta1 = delta2 = rota1 = rota2 = rota = None

        try: assert(self.__assertCDMatrix(lines))
        except AssertionError:
            for idx in range(len(lines)):
                if 'CDELT1' in lines[idx]:
                    insertIndex = idx
                    delta1 = self.__getNumVal(lines[idx])
                    continue
                elif 'CDELT2' in lines[idx]:
                    insertIndex = idx
                    delta2 = self.__getNumVal(lines[idx])
                    continue
                elif 'CROTA1' in lines[idx]:
                    insertIndex = idx
                    rota1 = self.__getNumVal(lines[idx])
                    continue
                elif 'CROTA2' in lines[idx]:
                    insertIndex = idx
                    rota2 = self.__getNumVal(lines[idx])
                    continue
            rota = self.__pickRotation(rota1,rota2)

            # Check delta values populated. Rotation angle may be
            # undefined: set to zero. If no CD matrix, CDELTAs MUST
            # be present.

            if type(delta1) == NoneType:
                self.validationMsg.append(("ERROR:",wcsErr+"CDELT1"))
                raise FitsHeaderError, "FITS Foul: CDELT1 not found."
            elif type(delta2) == NoneType:
                self.validationMsg.append(("ERROR:",wcsErr+"CDELT2"))
                raise FitsHeaderError, "FITS Foul: CDELT2 not found."

            cdMatrix = self.__computeMatrix(delta1,delta2,rota)
            lines.insert(insertIndex+1,"CD1_1   =\t"+str(cdMatrix[0]))
            lines.insert(insertIndex+2,"CD1_2   =\t"+str(cdMatrix[1]))
            lines.insert(insertIndex+3,"CD2_1   =\t"+str(cdMatrix[2]))
            lines.insert(insertIndex+4,"CD2_2   =\t"+str(cdMatrix[3]))
            self.validationMsg.append(("INFO: ","Wrote CD Matrix"))
        return

    def __assertCDMatrix(self,lines):
        """Determine if a CD matrix is present in the header.
        
        parameters: <list>
        return:     <bool>
        """
        cdmatrix    = False
        cdMatrixKey = 'CD1_1'   # if CD matrix is present, CD1_1 MUST be present.

        for headerline in lines:
            if cdMatrixKey in headerline:
                cdmatrix = True
                self.validationMsg.append(("INFO: ","Found CD Matrix"))
                break
        return cdmatrix

    def __pickRotation(self,rota1,rota2):
        """Pick the rotation angle of two, where rota2 is preferred.
        Zero if both NoneType.

        parameters: <float>, <float>
        return:     <float>
        """
        if rota2: rota = rota2
        elif rota1 and not rota2: rota = rota1
        elif not rota1 and not rota2: rota = 0.0
        self.validationMsg.append(("INFO: ","WCS Rotation angle: " + str(rota)))
        return rota

    def __computeMatrix(self, cdelt1, cdelt2, rho):
        """Compute the Coordinate Description matrix. Caller passes
        three arguments: CDELT1, CDELT2, CROTA2, the rotation angle if 
        any.
        
        parameters: <float>, <float>, <float>
        return:     <list>, list of four (4) CD matrix values (floats).
        """

        cd11 = cdelt1*cos(radians(rho))
        cd12 = -1*cdelt2*sin(radians(rho))
        cd21 = cdelt1*sin(radians(rho))
        cd22 = cdelt2*cos(radians(rho))
        return [cd11,cd12,cd21,cd22]

    def __insertDBKeys(self,headerLines, uri):
        """Insert required MDDB keywords for CAOM database insertion.
        See xDBkeys module.

        parameters: <list>, a list of header line strings
        return:     <void>
        """

        for xi in range(len(xDBKeys.xdbkeys)):
            if 'DATAURI' in xDBKeys.xdbkeys[xi][0]:
                headerLines.insert(xi+3,xDBKeys.xdbkeys[xi][0]+ \
                                       '=\t\t'+ uri)
            else:
                headerLines.insert(xi+3,xDBKeys.xdbkeys[xi][0]+ \
                                       '=\t\t'+str(xDBKeys.xdbkeys[xi][1]))
        self.validationMsg.append(("INFO: ","Data URI "+uri))
        return

    def __stripComment(self,lines):
        """Strip the comments from any header lines.

        parameters: <list>, a list of header lines as strings
        return:     <list>, a list of header lines, stripped of comments
        """
        stripped =[]
        for line in lines:
            if "COMMENT" in line:   continue
            elif "HISTORY" in line: continue
            stripped.append(line.split('/')[0].strip())
        return stripped

    def __dates2mjd(self,lines):
        """For DATE like header keywords produce an MJD. CAOM model requires
        dates in MJD. 'MJD-OBS' keyword is inserted, as are CTYPE5,CUNIT5,
        CRPIX5,CRVAL5 CAOM representation of CAOM time config.

        A TypeError is raised if dateObsIndex remains <NoneType>, i.e. DATE-OBS
        is not found. A default DATE-OBS is then inserted at the arbitrary index
        of 20. Default date is 2020-01-01.

        N.B. Future implementations will examine other possible observation date
        keywords that may be used, eg., OBSDATE, START-OBS, ...

        MJD zero point = 2400000.5
        
        parameters: <list>, a set of header lines
        return:     <void>
        """
        parseErr     = "Could not parse DATE-OBS, Ref. ISO 8601"
        dateObsIndex = None
        defDateLine  = 'DATE-OBS=            2020-01-01'
        MJD0         = 2400000.5

        for i in range(len(lines)):
            try:
                assert("MJD-OBS" in lines[i])
                self.validationMsg.append(("INFO: ","MJD-OBS keyword found. No Action."))
                return
            except AssertionError: pass
            try: 
                assert("DATE-OBS" in lines[i])
                dateObsIndex = i
                break
            except AssertionError: continue

        try:
            key,dateVal=lines[dateObsIndex].split('=')
        except TypeError:
            dateObsIndex = 20
            lines.insert(dateObsIndex,defDateLine)
            key,dateVal=defDateLine.split('=')
            if self.verbose: print "\tDATE-OBS not found. Inserted default."
            if self.verbose: print "\t",defDateLine,"\n"
            self.validationMsg.append(("WARN: ","DATE-OBS not found"))
            self.validationMsg.append(("WARN: ","DATE-OBS Defaulted: " + dateVal))

        isoDayTimeList = self.__parseISODate(dateVal)

        if len(isoDayTimeList) < 3:
            self.validationMsg.append(("ERROR:","Unrecognized DATE-OBS value"))
            self.validationMsg.append(("ERROR:",parseErr))
            raise FitsHeaderError

        iyear = isoDayTimeList[0]
        imon  = isoDayTimeList[1]
        iday  = isoDayTimeList[2]
        if len(isoDayTimeList) == 6:
            ihour = isoDayTimeList[3]
            imin  = isoDayTimeList[4]
            isec  = isoDayTimeList[5]
        else:
            ihour = '0'
            imin  = '0'
            isec  = '0.0'
        mjdDate = mjdConversions.julian_date(iyear,imon,iday,ihour,imin,isec) - MJD0
        mjdLine = 'MJD-OBS =\t'+ str(mjdDate)
        lines.insert(dateObsIndex+1,mjdLine)
        # insert the db wcs.time keys
        for i in range(len(xDBKeys.dbWcsTimeKeys)):
            if 'CRVAL5' in xDBKeys.dbWcsTimeKeys[i][0]:
                lines.insert(dateObsIndex+i+2,xDBKeys.dbWcsTimeKeys[i][0]+ \
                                '=\t'+ str(mjdDate))
                continue
            lines.insert(dateObsIndex+i+2,xDBKeys.dbWcsTimeKeys[i][0]+ \
                                '=\t\t'+str(xDBKeys.dbWcsTimeKeys[i][1]))
        return

    def __parseISODate(self,dval):
        """Method receives a date-time of the expected ISO8601 format
        returns a set of values for year, month, day, hour, min, sec,
        where ISO8601 format is
        
        yyyy-mm-ddThh:mm:ss.ssss
        
        eg.,

        >>> .__parseISODate('2011-09-10T18:28:58.511999')
        2011,9,10,18,28,58.511999

        parameters: <string>, DATE-OBS ISO 8601 
        return:     <list>,   a list of strings, as
                              ['yyyy','mm','dd,'hh','mm','ss.sss']
        """
        daytime = dval.strip().strip("'").split('T')
        ymd = daytime[0].split('-')
        if len(daytime) == 2:
            hms   = daytime[1].split(':')
        else: hms = []
        return ymd+hms

    #################### List line keys & values methods. ###################

    def __getNumVal(self, line):
        """Pare a numeric value from a header line string.

        parameters: <string>
        return:     <float>
        """
        return float(line.split('=')[1].split('/')[0].strip())

    def __getStringVal(self, line):
        """Pare string value from a header line string.

        parameters: <string>
        return:     <string>
        """
        return line.split('=')[1].split('/')[0].strip()

    def __getKeyWord(self, line):
        """Pare a keyword from a header line string.

        parameters: <string>
        return:     <string>
        """
        return line.split('=')[0].strip()


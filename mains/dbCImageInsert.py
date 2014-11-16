#!/usr/bin/env python
#
#                                                           CyberSKA DQS Project
#
#                                                   mddb.mains.dbCImageInsert.py
#                                                      Kenneth Anderson, 2012-03
#                                                            ken.anderson@ubc.ca
# ------------------------------------------------------------------------------

# $Id$
# ------------------------------------------------------------------------------
__version__      = '$Revision$'[11:-3]
__version_date__ = '$Date$'[7:-3]
__author__       = "k.r. anderson, <ken.anderson@ubc.ca>"
# ------------------------------------------------------------------------------
"""Module and classes to insert CASA Image metadata into CADC metadata database
(MDDB).
"""

from types    import NoneType
from math     import sin, cos, radians
from datetime import date

from mddb.mains.baseDbInsert import BaseDbInsert
from mddb.convert.converters import decimalize, formatRA, llh2XYZ
from mddb.convert.converters import revertFrequency, fitsify
from mddb.convert import keymaps

from mddb.db import xDBKeys


class CasaImageHeaderError(IndexError):
    """Raise this error when required metadata are missing from a Casa Image
    header.
    """
    pass


class DbCImageInsert(BaseDbInsert):

    def configureOverride(self, hdr, uri, public):
        """Bundles calls to private methods to validate, check coordinate 
        reference system, insert CD matrix, insert DB keys, and various other
        dreadfully tedious chores.
        
        parameters: <string>, <string> header file name, uri
        return:     <list>,   list of configured db override lines 
        """
        symbol = "="
        flines = self.__validate(hdr)
        self.__setMetaRelease(flines, public)
        self.__setOBSGEO(flines)
        self.ndims = self.__setImageDims(flines) # get a NAXIS value return
        self.__revertFrequencies(flines)
        self.__directionCoordUnits(flines)
        self.__setCTYPES(flines)  
        self.__setCoordSys(flines)
        self.__setCRVALS(flines)
        self.__setDirectionRefPixels(flines)
        self.__insertCDMatrix(flines)
        self.__insertDBKeys(flines, uri)
        self.__dates2mjd(flines)
        self.__setParseSymbol(flines, symbol)
        dblines = self.__stripSlashN(flines)
        return dblines

    def executeInsert(self, collid, oride, uri):
        """Run fits2caom.

        parameters: <string>, <string>, <string> collection id, override file, uri
        return:     <void>
        """
        self.cfgf = self.dbEnv.cimageDBConfig
        self.deff = self.dbEnv.cimageDBDefault
        super(DbCImageInsert, self).executeInsert(collid, oride, uri)
        return

            
    ################################ prive #################################   

    def __validate(self,cimageHdr):
        """Method determines the type of file passed by Caller, whether a
        header file contains some CASA Image signifiers, as '.hdr' file as 
        written by metaData. This will be the full path name to the copy of the 
        header placed in MDDBEnv.HDRS

        parameters: <string>, header file name
        return:     <list>,   list of read lines from CASA Image header file.
        """
        errstr='Invalid CASA Image header file. Missing: FILETYPE\t\tCASA Image\n'
        
        clines = open(cimageHdr).readlines()
        try:
            assert("CASA Image" in clines[0]) 
        except AssertionError:
            self.validationMsg.append(("ERROR:",errstr))
        return clines

    def __setMetaRelease(self,lines, public):
        """Set the Meta Release Date as the keyword, META-RELEASE, with
        the current date.  This is needed for CAOM database queries to 
        'see' the metadata.
        """
        metaReleaseKey = 'META-RELEASE'
        defaultMetaDate= '2099-01-01'

        if public:
            newline = metaReleaseKey + '\t\t' + date.today().isoformat()
        else:
            newline = metaReleaseKey + '\t\t' + defaultMetaDate
        lines.insert(2,newline)
        self.validationMsg.append(("INFO: ","Metadata release date set: " + 
                                   newline.split('\t\t')[1].strip()))
        return

    def __setOBSGEO(self, lines):
        """Set the OBSGEO-[XYZ] keywords based on and converted from CASA Image
        keywords

        TELESCOP_LAT
        TELESCOP_LON
        TELESCOP_HGT	

        parameters: <list>, list of header lines
        return:     <void>
        """
        tlat = 'TELESCOP_LAT'
        tlon = 'TELESCOP_LON'
        thgt = 'TELESCOP_HGT'
        obsX = 'OBSGEO-X'
        obsY = 'OBSGEO-Y'
        obsZ = 'OBSGEO-Z'
        geounit = 'm'
        err = "Telscope position parameters not found."
        lat = lon = hgt = posIndex = None

        for idx in range(len(lines)):
            lvals = lines[idx].split('\t')
            if lvals[0] == tlat:
                lat = lvals[2]
                continue
            if lvals[0] == tlon:
                lon = lvals[2]
                continue
            if lvals[0] == thgt:
                hgt = lvals[2]
                posIndex = idx
                continue
            if hgt and lon and lat: break

        if not hgt and not lon and not lat: raise CasaImageHeaderError,err
        X,Y,Z = llh2XYZ(float(lat), float(lon), float(hgt))
        lines.insert(posIndex+3,obsX+'\t\t'+str(X))
        lines.insert(posIndex+4,obsY+'\t\t'+str(Y))
        lines.insert(posIndex+5,obsZ+'\t\t'+str(Z))
        lines.insert(posIndex+6,"OBSGEO_UNIT"+'\t\t'+geounit)
        self.validationMsg.append(("INFO: ","SET OBSGEO keywords"))
        return

    def __setImageDims(self, lines):
        """Method sets NAXIS[i] keywords based on the IMAGE-SHAPE
        CASA Image keyword, which is of the form

        IMAGE-SHAPE		[1, 1, 64, 64]
        
        where,

        NAXIS1 = 1
        NAXIS2 = 1     
        NAXIS3 = 64        
        NAXIS4 = 64

        parameters: <list>, header lines
        return:     <int>,  number of image dimensions
        """
        axesKey   = 'IMAGE-SHAPE'
        baseNaxis = 'NAXIS'
        dimIndex  = None

        for idx in range(len(lines)):
            key = self.__getKeyWord(lines[idx])
            if key == axesKey:
                dimIndex = idx
                break
            else: continue
        shape = lines[dimIndex].split('E')[2].strip()
        dims  = shape.strip(']').strip('[').split(',')
        # dims should be a list like ['1', ' 1', ' 64', ' 64']
        # iterable
        naxis = len(dims)
        for i in range(naxis):
            lines.insert(dimIndex+1+i,baseNaxis+str(i+1) \
                             +"\t\t\t"+dims[i].strip())
        return naxis

    def __revertFrequencies(self,lines):
        """Revert Frequency values in lines to simple 'Hz' numbers.
        Current, CASA Image headers will specify frequency values in
        the COORDINATE0 related keywords in 'human readable' form.

        eg.,
        REFERENCE0-VALUE	115, GHz
        INCREMENT0		120 MHz
        REST-FREQUENCY		115, GHz

        parameters: <list>, header lines
        return:     <void>
        """
        freqKeys = ['REFERENCE0-VALUE','INCREMENT0','REST-FREQUENCY']
        matched  = 0

        for idx in range(len(lines)):
            if matched == 3: break
            key = self.__getKeyWord(lines[idx])
            if key in freqKeys:
                matched += 1
                lvals = lines[idx].split()
                fval  = float(lvals[1].strip().strip(','))
                unit  = lvals[2].strip()
                pureHz = revertFrequency(fval,unit)
                if key == freqKeys[0]:
                    lines[idx]   = key+"\t"+str(pureHz)
                else: lines[idx] = key+"\t\t"+str(pureHz)
            else: continue
        return

    def __directionCoordUnits(self, lines):
        """Break out the direction coordinate (COORDINATE2) units, insert two
        (2) lines for CUNITs.

        parameters: <list>, header lines list
        return:     <void>
        """
        unitKey   = 'INCREMENT2_UNITS'
        dirCunit1 = None
        dirCunit2 = None
        dir1Cunit = "DIR1_UNIT"
        dir2Cunit = "DIR2_UNIT"

        for idx in range(len(lines)):
            key = self.__getKeyWord(lines[idx])
            if key == unitKey:
                dirCunit1,dirCunit2 = self.__getValTuple(lines[idx])
                break
        lines.insert(idx+1, dir1Cunit+"\t\t"+dirCunit1)
        lines.insert(idx+2, dir2Cunit+"\t\t"+dirCunit2)
        return

    def __setCTYPES(self, lines):
        """Convert COORDINATE[i]-NAME string values to acceptable FITS wcs 
        string values.

        Eg., a nominal 4D image cube w/ freq, stokes, dec, ra.

        COORDINATE0-NAME    Frequency --> 'FREQ'
        COORDINATE1-NAME    Stokes    --> 'STOKES'

        Reconfiguring CASA Image direction coordinate requires separation,
        truncation, then concatenation of the projection parameter.

        Eg.,
        COORDINATE2-NAME    Declination, Right Ascension
        PROJECTION2	    SIN

        reconfigures to 
        
        COORDINATE2_1      'DEC--SIN'
        COORDINATE2_2      'RA---SIN'

        In the case of a CASA Image registered in galactic coords these values
        will likely appear as 

        COORDINATE[i]-NAME    Latitude, Longitude
        PROJECTION[i]         CAR

        and reconfigures as

        COORDINATE[i]_1      GLON--CAR
        COORDINATE[i]_2      GLAT--CAR
        
        parameters: <list>, header lines
        return:     <void>
        """
        # Find all coordinate type parameters, based on N_OF-AXES value
        naxis    = 'N_OF-AXES'
        projTag  = 'PROJECTION'
        coordTyp = []
        coordNam = []
        nIndex   = None
        projection = None

        for idx in range(len(lines)):
            key = self.__getKeyWord(lines[idx])
            if key == naxis:
                nIndex = idx
                naxisVal = self.__getNumVal(lines[idx])
                break
            else: continue

        # construct coordinate[n] name keywords. If one coordinate is of
        # type 'direction', n will be one greater than the number of
        # coordinates actual.
        for n in range(int(naxisVal)):
            coordTyp.append('COORDINATE'+str(n)+'-TYPE')
        # get values for each coord type.
        for i in range(nIndex, len(lines)):
            line = lines[i]
            key = self.__getKeyWord(line)
            if key in coordTyp:
                ctype = self.__getStringVal(line)
                if ctype == 'direction':
                    cname1,cname2 = self.__getValTuple(lines[i+1])
                    coordNam.append(key+'_NAME:'+cname1+' & '+cname2)
                else:
                    coordNam.append(key+'_NAME:'+self.__getStringVal(lines[i+1]))
            elif projTag in key:
                projIndex  = i
                projection = self.__getStringVal(line)
            else: continue

        # coordNam now looks like,
        # ['COORDINATE0-TYPE_NAME:Frequency',
        #  'COORDINATE1-TYPE_NAME:Stokes',
        #  'COORDINATE2-TYPE_NAME:Declination & Right Ascension'
        # ]
        # where list index equals coordinate number, i.e. COORDINATE[i]

        for i in range(len(coordNam)):
            fitsCTYPE = fitsify(coordNam[i], i+1, projection)
            if len(fitsCTYPE) == 2:
                lines.insert(projIndex+1, fitsCTYPE[0]+"\t\t\t"+fitsCTYPE[1])
            elif len(fitsCTYPE) == 4:
                lines.insert(projIndex+1, fitsCTYPE[2]+"\t\t\t"+fitsCTYPE[3])
                lines.insert(projIndex+2, fitsCTYPE[0]+"\t\t\t"+fitsCTYPE[1])
        return

    def __setCRVALS(self, lines):
        """Set the CRVAL keywords, keying on direction coordinate keyword,
        REFERENCE2-VALUE.

        eg.,

        REFERENCE2-VALUE 	+44.55.19.95, 04:45:31.695

        where the ordered values represent DEC, RA of the reference pixel.

        parameters: <list>, header lines 
        return:     <void>
        """
        crvalKey   = 'REFERENCE2-VALUE'
        pixval_ra  = 'CRVAL2_2'
        pixval_dec = 'CRVAL2_1'
        crvalIndex = None

        for idx in range(len(lines)):
            key = self.__getKeyWord(lines[idx])
            if key == crvalKey:
                linevals = lines[idx].split()
                dec = linevals[1].strip()
                ra  = linevals[2].strip()
                crvalIndex = idx + 1
                break
            else: continue
        
        crval_dec = decimalize(dec)
        crval_ra  = decimalize(formatRA(ra))*15
        lines.insert(crvalIndex,pixval_dec+'\t\t'+str(crval_dec))
        lines.insert(crvalIndex+1,pixval_ra+'\t\t'+str(crval_ra))
        return

    def __setDirectionRefPixels(self, lines):
        """Set the reference pixels for the direction coordinate to a pair of
        CRPIX[i] keywords

        parameters: <list>, header lines list
        return:     <void>
        """
        crpix3 = 'CRPIX3'
        crpix4 = 'CRPIX4'
        refPixelKey = 'REFERENCE2-PIXEL'
        for idx in range(len(lines)):
            pixKey = self.__getKeyWord(lines[idx])
            if pixKey == refPixelKey:
                pixelIndex = idx
                strpix1,strpix2 = self.__getValTuple(lines[idx])
                break
            else: continue
        pix1 = float(strpix1)+1.0 # +1 for fits2caom indexing
        pix2 = float(strpix2)+1.0 # +1 for fits2caom indexing
        lines.insert(idx+1, crpix3+"\t\t\t"+str(pix1))
        lines.insert(idx+2, crpix4+"\t\t\t"+str(pix2))
        return

    def __setCoordSys(self, lines):
        """Set the coordinate reference system. For CASA Images, this should
        only need to set a 'RADESYS' keyword, as 'EQUINOX' type is consistently
        written in the metadata under the dict hierarchy,

        coordinates: direction0: system

        This frame is getable via a call to the directioncoordinate.get_frame()
        method.

        which the metadata package writes as the keyword-val pair,
        
        eg., FRAME2	 J2000

        Under MDDB-CAOM interoperability, a 'RADESYS' keyword, or one describing
        this value, must be written to the override file.
        
        The FITS WCS spec (Calabretta & Greisen, A&A, 2002) states the conditions
        that define the appropriate value for 'RADESYS' for a given equinox.

        EQUINOX > 1984 :: RADESYS = FK5
        EQUINOX < 1984 :: RADESYS = FK4

        Furthermore, frame values of 'J2000', 'B1950', and 'B1950_VLA' are 
        swapped for numeric values stripped of alpha text due to fits2caom
        exception throwing:

        'J2000' --> '2000'
        'B1950' --> '1950', etc.
        
        parameters: <list>, header lines
        return:     <void>
        """
        errstr      = 'Coordinate reference frame not found in header.\n'
        frameKey    = 'FRAME2'
        radeRef     = 'RADESYS'
        refSys      = {}
        refsysIndex = None

        for idx in range(len(lines)):
            key = self.__getKeyWord(lines[idx])
            if key == frameKey:
                refSys[key] = self.__getStringVal(lines[idx])
                if not refsysIndex: refsysIndex = idx
                break
            else: continue

        # Defaults spec'd in Calabretta & Greisen, p.1082

        if  '2000' in refSys[frameKey]: 
            refSys[radeRef] = 'FK5'
            refSys[frameKey] = keymaps.frameValueMap[refSys[frameKey]]
            lines.pop(refsysIndex)
            lines.insert(refsysIndex,frameKey+"\t\t\t"+refSys[frameKey])
            self.validationMsg.append(("INFO: ","Set "+radeRef+": "+refSys[radeRef]))
        elif '1950' in refSys[frameKey]: 
            refSys[radeRef] = 'FK4'
            refSys[frameKey] = keymaps.frameValueMap[refSys[frameKey]]
            lines.pop(refsysIndex)
            lines.insert(refsysIndex,frameKey+"\t\t\t"+refSys[frameKey])
            self.validationMsg.append(("INFO: ","Set "+radeRef+": "+refSys[radeRef]))
        if not refSys[frameKey]:
            raise CasaImageHeaderError, errstr
        lines.insert(refsysIndex+1,radeRef+"\t\t"+refSys[radeRef])
        return

    def __insertCDMatrix(self, lines):
        """A CASA Image header will present the positional 'cdelt' metadata in the
        keyword 'INCREMENT2', where '2' indicates the direction coordinate as defined
        in the CASA Image metadata structure:

        direction0:cdelt:array([cdelta_RA, cedlta_Dec])

        The metaData package converts the values to degrees and reverses the order
        for consistency with the axes as presented by the coordinates.get_axes() method
        call.

        eg.,

        INCREMENT2		+0.0.1.0, -0.0.1.0

        These values are 'unconverted' and the CD matrix transformation id performed. 
        New CDn_n keywords are inserted into the header lines. The INREMENT2-CDMatrix
        transformation is performed to the FITS specification
        (Calabretta and Geisen, 2002). INCREMENT2[0] is DEC and INCREMENT2[1] is 
        RA. The final inserted CD matrix must adhere to the FITS specification for 
        fits2caom/CAOM compatibility, i.e. CD1_1 is the RA component of the transformation
        and CD2_2 is the Dec component, with the cross components populated under 
        rotation and null otherwise.  Rotation is not expected in CASA Images.

        parameters: <list>, header lines list of strings from CASA Image header file.
        return:     <void>, referenced list is updated.
        """
        errstr   = "Image Foul: cdelt values not found."
        cdelta2Str = cdelta1Str = cdelta1 = cdelta2 = None
        deltaKey = 'INCREMENT2'

        for idx in range(len(lines)):
            if deltaKey in lines[idx]:
                insertIndex = idx
                break
        cdelta2Str, cdelta1Str = self.__getValTuple(lines[insertIndex])

        if type(cdelta2Str) == NoneType:
            raise CasaImageHeaderError, errstr
        elif type(cdelta1Str) == NoneType:
            raise CasaImageHeaderError, errstr

        # convert string dms cdelta values to float decimal deg.
        cdelta1 = decimalize(cdelta1Str)
        cdelta2 = decimalize(cdelta2Str)

        cdMatrix= self.__computeMatrix(cdelta1,cdelta2)

        lines.insert(insertIndex+1,"CD1_1    \t\t"+str(cdMatrix[0]))
        lines.insert(insertIndex+2,"CD1_2    \t\t"+str(cdMatrix[1]))
        lines.insert(insertIndex+3,"CD2_1    \t\t"+str(cdMatrix[2]))
        lines.insert(insertIndex+4,"CD2_2    \t\t"+str(cdMatrix[3]))
        self.validationMsg.append(("INFO: ","Wrote CD Matrix"))
        return

    def __computeMatrix(self, cdelt1, cdelt2, rho=0):
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

        parameters: <list>, a list of header line strings
        return:     <void>, referenced list updated w/ xdbkeys
        """

        for xi in range(len(xDBKeys.xcimdbkeys)):
            if 'DATAURI' in xDBKeys.xdbkeys[xi][0]:
                headerLines.insert(xi+3,xDBKeys.xcimdbkeys[xi][0]+ \
                                       ' \t\t'+ uri)
            else:
                headerLines.insert(xi+3,xDBKeys.xcimdbkeys[xi][0]+ \
                                       ' \t\t'+str(xDBKeys.xcimdbkeys[xi][1]))
        self.validationMsg.append(("INFO: ","DB Keys inserted."))
        return

    def __stripSlashN(self, lines):
        """Rid lines of newline chars, \n"""
        return [line.strip() for line in lines]

    def __dates2mjd(self,lines):
        """Null method (for now)"""
        mjdKeys  = ['MJD-OBS','DATE-OBS-MJD']
        taxisKey = 'CRVAL5'
        mjdIndex = None
        mjdDate  = None

        for idx in range(len(lines)):
            key = self.__getKeyWord(lines[idx])
            if key in mjdKeys:
                mjdIndex = idx
                mjdDate = self.__getNumVal(lines[idx])
                break
        try:
            assert(mjdDate)
            for i in range(len(xDBKeys.dbWcsTimeKeys)):
                if taxisKey in xDBKeys.dbWcsTimeKeys[i][0]:
                    lines.insert(mjdIndex+i+1,xDBKeys.dbWcsTimeKeys[i][0]+ \
                                     '\t\t'+ str(mjdDate))
                    continue
                lines.insert(mjdIndex+i+1,xDBKeys.dbWcsTimeKeys[i][0]+ \
                                '\t\t'+str(xDBKeys.dbWcsTimeKeys[i][1]))
        except AssertionError:
            err = 'Observation Date not found.'
            self.validationMsg.append(("ERROR:","Observation Date not found."))
        return


    def __setParseSymbol(self, lines, symbol):
        """Inject the passed parse symbol into lines. The symbol is injected 
        into each line of lines after the first field of the line, i.e. a nominal
        keyword, for fits2caom parsing. Currently, fits2caom parses on "=" as 
        a field splitter in FITS headers.

        parameters: <list>, header lines list
        return:     <void>, lines are updated with injected symbol
        """
        symbol = symbol+"\t"
        for idx in range(len(lines)):
            oldline = lines.pop(idx)
            newline = symbol.join(oldline.split('\t',1))
            lines.insert(idx,newline)
        return

    ############### List line keys & values methods. ########################

    def __getValTuple(self, line):
        """Return a 2-tuple of values from a multiply valued header line.

        egs.,
        >>>__getValTuple('POINTING          03:41:47.8999999999   +62.38.53.9999999988')
        ('03:41:47.8999999999', '+62.38.53.9999999988')
        >>>__getValTuple('COORDINATE2-NAME       Declination, Right Ascension')
        ('Declination', 'Right Ascension')

        N.B. This method handles only lines with two parsable values, as above. It is
        inappropriate for lines containing more than two values.

        parameters: <string>, header line comprising a keyword and csv values.
        return:     <tuple>,  2-tuple of strings
        """
        val1 = val2 = ''
        vals = line.split()
        if len(vals) == 3:
            val1 = vals[1]
            val2 = vals[2]
        elif len(vals) == 4:
            val1 = vals[1]
            for val in vals[2:]:
                val2 += ' '+val
        else: raise TypeError, 'inappropriate line for this method.'
        return val1.strip(','),val2.strip()

    def __getNumVal(self, line):
        """Pare a numeric value from a header line string.

        parameters: <string>
        return:     <float>
        """
        return float(line.split()[1].strip())

    def __getStringVal(self, line):
        """Pare string value from a header line string.

        parameters: <string>
        return:     <string>
        """
        return line.split()[1].strip()

    def __getKeyWord(self, line):
        """Pare a keyword from a header line string.

        parameters: <string>
        return:     <string>
        """
        return line.split()[0].strip()


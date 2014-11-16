#
#
#                                                 CyberSKA CASA Metadata Project
#
#                                                             mddb.db.xDBKeys.py
#                                                      Kenneth Anderson, 2012-03
#                                                            ken.anderson@ubc.ca
# ------------------------------------------------------------------------------

# $Id$
# ------------------------------------------------------------------------------
__version__      = '$Revision$'[11:-3]
__version_date__ = '$Date$'[7:-3]
__author__       = "k.r. anderson, <ken.anderson@ubc.ca>"
# ------------------------------------------------------------------------------

"""Module provides required CAOM data model keys not found in a nominal FITS
   header.
   
   Time is treated somewhat as a coordinate, values in an override file for
   DATE-OBS:

   NAXIS5 = 1
   CTYPE5 = MJD
   CUNIT5 = d
   CRPIX5 = 0.5
   CRVAL5 = <start time in MJD>, i.e. DATE-OBS | START-OBS
   CDELT5 = <integration time in days>, START-OBS - END-OBS | EXPTIME | 1s

   Various CASA produced FITS images do not have an EXPTIME or even start/end 
   dates (see CyberSKA public test image, M100contimage.fits). 
   Advice in such a circumstance is to set

   CDELT5 = 1 s

"""
Projekt='CYBERSKADQS'

xdbkeys = [
	('PROJEKT ' ,Projekt),
	('DATAURI ' ,''),
        ('OBSCTYPE' ,'PROD'),
        ('OBSCUNIT' ,''),
        ('POSAXIS1' ,1),
        ('POSAXIS2' ,2),
        ('ENAXIS  ' ,3),
        ('POLAXIS ' ,4),
        ('TAXIS   ' ,5),
        ('SSYSOBS ' ,'TOPOCENT'),
        ('VELSYS  ' ,'')
        ]

xcimdbkeys = [
	('PROJEKT ' ,Projekt),
	('DATAURI ' ,''),
        ('OBSCTYPE' ,'PROD'),
        ('OBSCUNIT' ,''),
        ('POSAXIS1' ,3),
        ('POSAXIS2' ,4),
        ('ENAXIS  ' ,1),
        ('POLAXIS ' ,2),
        ('TAXIS   ' ,5),
        ('SSYSOBS ' ,'TOPOCENT'),
        ('VELSYS  ' ,'')
        ]

dbWcsTimeKeys = [
    ('NAXIS5  '  ,1),
    ('CTYPE5  '  ,'MJD'),
    ('CUNIT5  '  ,'d'),
    ('CRPIX5  '  , 0.5),
    ('CRVAL5  '  ,''),
    ('CDELT5  '  , 0.0000115)
    ]

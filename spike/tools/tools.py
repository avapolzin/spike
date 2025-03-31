from asdf import AsdfFile
from astropy.coordinates import SkyCoord, name_resolve
import astropy
import astropy.units as u
from astropy.io import fits
from astropy.wcs import WCS, utils
import numpy as np
import os
import pkg_resources
from scipy.interpolate import RectBivariateSpline
import warnings

def warning_on_one_line(message, category, filename, lineno, file=None, line=None):
	return '%s:%s: %s: %s\n' % (filename, lineno, category.__name__, message)

warnings.formatwarning = warning_on_one_line

CONFIG_PATH = pkg_resources.resource_filename('spike', 'configs/')

# #########
#  * * * * 
# #########

def objloc(obj):
	"""
	Get object location.

	Parameters:
		obj (str): Name or coordinates for object of interest. If coordinates, should be in
			HH:MM:SS DD:MM:SS or degree formats. Names must be resolvable in SIMBAD.
	Returns:
		coords (astropy coordinates object)
	"""
	isname = False #check if obj is name or coordinates
	for s in obj:
		if s.isalpha():
			isname = True
			break

	if isname:
		coords = name_resolve.get_icrs_coordinates(obj)

	if not isname:
		if ':' in obj:
			coords = SkyCoord(obj, unit = (u.hour, u.deg), frame = 'icrs')
		if not ':' in obj:
			coords = SkyCoord(obj, unit = u.deg, frame = 'icrs')

	return coords


def checkpixloc(coords, img, inst, camera = None):
	"""
	Get object location on detector. 

	Parameters:
		coords (astropy skycoord object): Coordinates of object of interest or list of skycoord objects.
		img (str): Path to image.
		inst (str): Instrument of interest. 
				HST: 'ACS', 'WFC3', 'WFPC', WFPC2', 'NICMOS'
				JWST: 'MIRI', 'NIRCAM', 'NIRISS'
				Roman: 'WFI', 'CGI'
		camera (str): Camera associated with instrument.
				HST/ACS: 'WFC', 'HRC'
				HST/WFC3: 'UVIS', 'IR'
				JWST/NIRISS: 'Imaging', 'AMI' #AMI has different multi-extension mode

	Returns:
		[X, Y, chip, filter] (list): Pixel coordinates, chip number (HST) or detector name (JWST/Roman) if relevant, and filter name.
			Only returned if object coordinates fall onto detector - returns NaNs if not.

	"""
	hdu = fits.open(img)
	if camera:
		imcam = inst.upper() + '/' + camera.upper()
	if not camera:
		imcam = inst.upper()

	try: #get filter
		filt = hdu[0].header['FILTER']
	except:
		if hdu[0].header['FILTER1'].startswith('F'):
			filt = hdu[0].header['FILTER1']
		else:
			filt = hdu[0].header['FILTER2']

	### instrument checks ###
	if imcam in ['ACS/WFC', 'WFC3/UVIS']:
		chip1 = hdu[4]
		chip2 = hdu[1]
		chips = [chip1, chip2]

		chip = np.nan
		for a in chips:
			wcs1 = WCS(a.header, fobj = hdu)
			datshape = a.data.shape[::-1] #transposed based on numpy vs. fits preference
			if type(coords) != astropy.coordinates.sky_coordinate.SkyCoord:
				xcoord_out = []
				ycoord_out = []
				chip_out = []
				for coord in coords:
					check = utils.skycoord_to_pixel(coord, wcs1)
					if np.logical_and(0 <= check[0] <= datshape[0], 0 <= check[1] <= datshape[1]):
						xcoord_out.append(check[0])
						ycoord_out.append(check[1])
						if a == chip1:
							chip_out.append('1')
						if a == chip2:
							chip_out.append('2')
				if len(xcoord_out) >= 1:
					out = [[xcoord_out[i], ycoord_out[i], chip_out[i], filt] for i in range(len(coords))]
				if len(xcoord_out) == 0:
					out = [np.nan] * 4
			if type(coords) == astropy.coordinates.sky_coordinate.SkyCoord:
				check = utils.skycoord_to_pixel(coords, wcs1)
				if np.logical_and(0 <= check[0] <= datshape[0], 0 <= check[1] <= datshape[1]):
					x_coord = check[0]
					y_coord = check[1]
					if a == chip1:
						chip = 1
					if a == chip2:
						chip = 2
		if (type(chip) != str) and (np.isnan(chip)):
			out = [np.nan, np.nan, chip, np.nan]
		else:
			out = [float(x_coord), float(y_coord), chip, filt]

	if imcam in ['WFPC', 'WFPC1', 'WFPC2']:
		if imcam in ['WFPC', 'WFPC1']: #accounting for use of both names
			chip1 = hdu[1]
			chip2 = hdu[2]
			chip3 = hdu[3]
			chip4 = hdu[4]
			chip1 = hdu[5]
			chip2 = hdu[6]
			chip3 = hdu[7]
			chip4 = hdu[8]
			chips = [chip1, chip2, chip3, chip4, chip5, chip6, chip7, chip8]
		if imcam == 'WFPC2':
			chip1 = hdu[1]
			chip2 = hdu[2]
			chip3 = hdu[3]
			chip4 = hdu[4]
			chips = [chip1, chip2, chip3, chip4]

		chip = np.nan
		for a in chips:
			wcs1 = WCS(a.header, fobj = hdu)
			datshape = a.data.shape[::-1] #transposed based on numpy vs. fits preference
			if type(coords) != astropy.coordinates.sky_coordinate.SkyCoord:
				xcoord_out = []
				ycoord_out = []
				chip_out = []
				for coord in coords:
					check = utils.skycoord_to_pixel(coord, wcs1)
					if np.logical_and(0 <= check[0] <= datshape[0], 0 <= check[1] <= datshape[1]):
						xcoord_out.append(check[0])
						ycoord_out.append(check[1])
						if a == chip1:
							chip_out.append('1')
						if a == chip2:
							chip_out.append('2')
				if len(xcoord_out) >= 1:
					out = [[float(xcoord_out[i]), float(ycoord_out[i]), chip_out[i], filt] for i in range(len(coords))]
				if len(xcoord_out) == 0:
					out = [np.nan] * 4
			if type(coords) == astropy.coordinates.sky_coordinate.SkyCoord:
				check = utils.skycoord_to_pixel(coords, wcs1)
				if np.logical_and(0 <= check[0] <= datshape[0], 0 <= check[1] <= datshape[1]):
					x_coord = check[0]
					y_coord = check[1]

					chip = np.where(np.array(chips) == a)[0][0] + 1
					
		if (type(chip) != str) and (np.isnan(chip)):
			out = [np.nan, np.nan, chip, np.nan]
		else:
			out = [float(x_coord), float(y_coord), chip, filt]


	if imcam in ['ACS/HRC', 'WFC3/IR', 'NICMOS',
				 'MIRI', 'NIRCAM', 'NIRISS', 'NIRISS/IMAGING', 
				 'WFI', 'CGI']:
		# for WFC3, only checks the final readout by design
		chip = 0 #no chip
		wcs1 = WCS(hdu[1].header, fobj = hdu)
		datshape = hdu[1].data.shape[::-1] #transposed based on numpy vs. fits preference
		if type(coords) != astropy.coordinates.sky_coordinate.SkyCoord:
			xcoord_out = []
			ycoord_out = []
			chip_out = []
			for coord in coords:
				check = utils.skycoord_to_pixel(coord, wcs1)
				xcoord_out.append(check[0])
				ycoord_out.append(check[1])
				if imcam == 'NIRCAM':
					chip = hdu[0].header['DETECTOR']
					if chip in ['NRCALONG', 'NRCBLONG']:
						chip = chip.replace('LONG', '5')
				if imcam == 'WFI':
					# based on how SCA detector is identified in simulated data: https://roman.ipac.caltech.edu/sims/Simulations_csv.html
					strlist = img.split('_')
					chip = 'SCA%s'%strlist[-1].split('.')[0].rjust(2, '0')
				chip_out.append(chip)
			if len(xcoord_out) >= 1:
				out = [[float(xcoord_out[i]), float(ycoord_out[i]), chip_out[i], filt] for i in range(len(coords))]
			if len(xcoord_out) == 0:
				out = [np.nan] * 4


		if type(coords) == astropy.coordinates.sky_coordinate.SkyCoord:
			check = utils.skycoord_to_pixel(coords, wcs1)
			if np.logical_and(0 <= check[0] <= datshape[0], 0 <= check[1] <= datshape[1]):
				x_coord = check[0]
				y_coord = check[1]
				if imcam == 'NIRCAM':
					chip = hdu[0].header['DETECTOR']
					if chip in ['NRCALONG', 'NRCBLONG']:
						chip = chip.replace('LONG', '5')
				if imcam == 'WFI':
					# based on how SCA detector is identified in simulated data: https://roman.ipac.caltech.edu/sims/Simulations_csv.html
					strlist = img.split('_')
					chip = 'SCA%s'%strlist[-1].split('.')[0].rjust(2, '0')
				out = [float(x_coord), float(y_coord), chip, filt]
			else:
				out = [np.nan] * 4

	return out

	#add support for FOC and NIRISS AMI


def to_asdf(fitspath, save = True):
	"""
	Convert .fits file to .asdf by simply wrapping data and header extensions.

	Parameters:
		fitspath (str): Path to .fits file to convert.
		save (bool): If True, saves the .asdf file.

	Returns:
		ASDF file object
	"""

	fits_in = fits.open(fitspath)
	# dicts = [{} for i in range(len(orig))]
	headers = {}
	for i in range(len(fits_in)):
		headers['head'+str(i)] = {**fits_in[i].header}
	
	asdf_out = AsdfFile(headers)

	for i in range(len(fits_in)):
		asdf_out['dat'+str(i)] = fits_in[i].data

	if save:
		asdf_out.write_to(fitspath.replace('fits', 'asdf'))

	return asdf_out


def pysextractor(img_path, config = None, psf = True, userargs = None, keepconfig = False):
	"""
	Wrapper to easily call SExtractor from python. 
	Using this in lieu of sep for easier compatibility with PSFEx.

	Parameters:
		img_path (str): Path to the image from the working directory.
		config (str): If specifying custom config, path to config file. If none, uses default.sex.
		psf (bool): If True and no configuration file specified, uses config and param files that work with PSFEx.
		userargs (str): Any additional command line arguments to feed to SExtractor. The preferred way to include
			user arguments is via specification in the config file as command line arguments simply override the 
			corresponding configuration setting.
		keepconfig (str): If True, retain parameter files and convolutional kernels moved to working dir.

	Returns:
		Generates a .cat file with the same name as img_path

	"""

	if not config:
		if psf:
			configpath = CONFIG_PATH + 'sextractor_config/default_psf.sex'
		if not psf:
			configpath = CONFIG_PATH + 'sextractor_config/default.sex'
		os.system('cp '+ CONFIG_PATH +'sextractor_config/default.conv .')
		os.system('cp '+ CONFIG_PATH +'sextractor_config/* .')
	if config:
		configpath = config

	sextractor_args = 'sex '+img_path+' -c '+configpath

	if userargs:
		sextractor_args += ' '+userargs

	os.system(sextractor_args)

	imgpath = img_path.split('[')[0]
	if imgpath.split('_')[-1].startswith('mask'):
		imgpath = imgpath.replace('_mask.fits', '.fits')
	os.system('mv test.cat ' + imgpath.replace('fits', 'cat')) #move to img name

	if (not keepconfig) and (not config):
		# clean up user directory by removing copied files
		os.system('rm default*')
		os.system('rm *.conv')


def regridarr (im, sample):
	"""
	Regrid PSF model to input pixel scale.

	Parameters:
		im (arr): PSF image array.
		sample (float): Npix,im/Npix,orig. If sample > 1, oversampled; if sample < 1, undersampled.

	Returns:
		Interpolated and regridded PSF model.

	"""

	if sample == 1.:
		return im

	x,y = im.shape
	xnew = np.arange(0, x, sample)
	ynew = np.arange(0, y, sample)

	spline = RectBivariateSpline(np.arange(x), np.arange(y), im)
	out = spline(xnew[xnew <= x-1], ynew[ynew <= y-1])

	return out	


def psfexim(psfpath, pixloc, regrid = True, save = False):
	"""
	Generate image from PSFEx .psf file.

	Parameters:
		psfpath (str): Path to the relevant .psf file from the working directory.
		pixloc (tuple): Pixel location of object of interest in (x, y).
		regrid (bool): If True, will (interpolate and) regrid model PSF to image pixel scale.
		save (str): If 'fits' or 'arr', will save in the specified format with name from psfpath.
			The option to save as an array results in a .npy file.

	Returns:
		2D image of PSFEx model
	"""
	psfexmodel = fits.open(psfpath)

	if psfexmodel[1].header['PSFAXIS3'] == 1:
		warnings.warn('PSF model is based on only a single component vector.', Warning, stacklevel = 2)
		psfmodel = psfexmodel[1].data['PSF_MASK'][0, 0, :, :]

	else:
		x_, y_ = pixloc

		x = (x_ - psfexmodel[1].header['POLZERO1'])/psfexmodel[1].header['POLSCAL1']
		y = (y_ - psfexmodel[1].header['POLZERO2'])/psfexmodel[1].header['POLSCAL2']

		order = psfexmodel[1].header['POLDEG1']

		xpoly, ypoly = x**np.arange(order+1), y**np.arange(order+1)

		# takes X_c * Phi_c, where Phi is the vector and X_c(x, y) is the basis function
		# see https://psfex.readthedocs.io/en/latest/Working.html and
		# https://www.astromatic.net/wp-content/uploads/psfex_article.pdf

		xc = []
		for i, yy in enumerate(ypoly):
			for ii, xx in enumerate(xpoly[:(order+1-i)]):
				xc.append(xx*yy)

		phic = psfexmodel[1].data['PSF_MASK'][0]

		psfmodel = np.sum(phic * np.array(xc)[:, None, None], axis = 0)

	if regrid:
		if psfexmodel[1].header['PSF_SAMP'] != 1.:
			psfmodel = regridarr(psfmodel, psfexmodel[1].header['PSF_SAMP'])

	if save:
		if save.lower() not in ['arr', 'fits']:
			warnings.warn('Save input must be "arr" or "fits". Generating PSF model without saving.', Warning, stacklevel = 2)
		if save.lower() == 'arr':
			np.save(psfpath.replace('.psf', '_psfex_psf.npy'), psfmodel)
		if save.lower() == 'fits':
			fits.writeto(psfpath.replace('.psf', '_psfex_psf.fits'), psfmodel)

	return psfmodel


def pypsfex(cat_path, pos, config = None, userargs = None, makepsf = True, 
	savepsf = False, keepconfig = False, regrid = True):
	"""
	Wrapper to easily call PSFEx from python. 

	Parameters:
		cat_path (str): Path to the SExtractor catalog from the working directory.
		pos(tuple): Pixel (and spectral) location of object of interest in (x, y, chip, filter) - as from spike.tools.checkpixloc.
			If not specified, generates generic model assuming central pixel.
		config (str): If specifying custom config, path to config file. If none, uses default.psfex.
		userargs (str): Any additional command line arguments to feed to PSFEx. The preferred way to include
			user arguments is via specification in the config file as command line arguments simply override the 
			corresponding configuration setting.
		makepsf (bool): If True, returns 2D PSF model.
		savepsf (str): If 'fits', 'arr', or 'txt', will save 2D model PSF in that file format with the same name as the catalog.
		keepconfig (str): If True, retain parameter files and convolutional kernels moved to working dir.
		regrid (bool): If True, will (interpolate and) regrid model PSF to image pixel scale.

	Returns:
		Generates a .psf file that stores linear bases of PSF.
		If makepsf = True, also returns 2D array containing PSF model.
	"""

	if not config:
		configpath = CONFIG_PATH + 'psfex_config/default.psfex'
		os.system('cp '+ CONFIG_PATH +'psfex_config/* .')
	if config:
		configpath = config

	psfex_args = 'psfex '+cat_path+' -c '+configpath

	if userargs:
		psfex_args += ' '+userargs

	os.system(psfex_args)
	os.system('mv test.psf ' + cat_path.replace('cat', 'psf')) #move to img name

	if (not keepconfig) and (not config):
		# clean up user directory by removing copied files
		os.system('rm default*')
		os.system('rm *.conv')

	if makepsf:

		if pos:
			x, y, chip, filts = pos

		if not pos:
			#assumes that .cat and .fits file are in the same directory
			im = fits.open(cat_path.replace('cat', 'fits'))[1].data
			x, y = im.shape/2 #select central pixel if not specified


		psfmodel = psfexim(cat_path.replace('cat', 'psf'), pixloc = (x, y), save = savepsf, regrid = regrid)
			
		return psfmodel


def rewrite_fits(psfarr, coords, img, imcam, pos, method = None):
	"""
	Write relevant image headers to the model PSFs and modify the coordinates and WCS.
	Creates a full _topsf.fits file with only one SCI extension for use with drizzle/resample.

	Parameters:
		psfarr (arr): The 2D PSF model.
		coords (astropy skycoord object): Coordinates of object of interest or list of skycoord objects.
		img (str): Path to image for which PSF is generated.
		imcam (str): 'ACS/WFC' is the only recommended instrument/camera combination for this PSF generation method.
		pos (list): Location of object of interest (spatial and spectral).[X, Y, chip, filter]
		method (list): Method used to generate PSF.

	Returns: 
		Generates a new FITS file with a _topsf suffix, which stores the 2D PSF model in the 
		'SCI' extension and inherits the header information from the original image.

	"""

	ext = 1
	extv = 1
	if (imcam in ['ACS/WFC', 'WFC3/UVIS']) and (pos[2] == 1):
		ext = 4
		extv = 2
	if (imcam in ['ACS/WFC', 'WFC3/UVIS']) and (pos[2] == 2):
		ext = 1 #yes, it's already 1, but this is to make things explicit
		extv = 1
	if imcam in ['WFPC', 'WFPC1', 'WFPC2']:
		ext = pos[2]
		extv = pos[2]

	imgdat = fits.open(img)

	psfim = np.zeros_like(imgdat[ext].data)
	xmin = int(pos[0]) - psfarr.shape[0]//2
	xmax = int(pos[0]) + psfarr.shape[0]//2
	ymin = int(pos[1]) - psfarr.shape[1]//2
	ymax = int(pos[1]) + psfarr.shape[1]//2

	if psfarr.shape[0] % 2 == 0:
		psfim[ymin:ymax, xmin:xmax] += psfarr
	if psfarr.shape[0] % 2 != 0:
		psfim[ymin:ymax+1, xmin:xmax+1] += psfarr

	cphdr = fits.PrimaryHDU(header = imgdat[0].header)

	hdr = imgdat[ext].header
	if method:
		hdr['COMMENT'] = "PSF generated using %s via spike."%method
	if not method:
		hdr['COMMENT'] = "PSF generated via spike."
	cihdr = fits.ImageHDU(data = psfim, header = hdr, name = 'SCI')

	if img.split('_')[-1] != '_c0m.fits':
		ehdrdat = np.zeros_like(imgdat[('ERR', extv)].data) #shouldn't matter, but doing this explicitly anyway
		dqhdrdat = np.zeros_like(imgdat[('DQ', extv)].data)
		cehdr = fits.ImageHDU(data = ehdrdat, header = imgdat[('ERR', extv)].header, name = 'ERR')
		cdqhdr = fits.ImageHDU(data = dqhdrdat, header = imgdat[('DQ', extv)].header, name = 'DQ')

	coordstring = str(coords.ra)
	if coords.dec.deg > 0:
		coordstring += '+'+str(coords.dec)
	if coords.dec.deg >= 0:
		coordstring += str(coords.dec)

	modname = img.replace('.fits', '_'+coordstring+'_%s'%pos[3]+'_topsf.fits')

	if img.split('_')[-1] != '_c0m.fits':
		hdlist = [cphdr, cihdr, cehdr, cdqhdr]

	if img.split('_')[-1] == '_c0m.fits':
		hdlist = [cphdr, cihdr]

	try: #get WCSDVARR
		dp1 = hdr['DP1']
	except:
		dp1 = None

	try: #get WCSDVARR
		dp2 = hdr['DP2']
	except:
		dp2 = None

	try: #get D2IMARR
		d2im1 = hdr['D2IM1']
	except:
		d2im1 = None

	try: #get D2IMARR
		d2im2 = hdr['D2IM2']
	except:
		d2im2 = None


	if (d2im1 == 'EXTVER: 1') & (d2im2 == 'EXTVER: 2'):
		hdlist.append(fits.ImageHDU(data = imgdat[('D2IMARR', 1)].data, header = imgdat[('D2IMARR', 1)].header, 
			name = 'D2IMARR', ver = 1))
		hdlist.append(fits.ImageHDU(data = imgdat[('D2IMARR', 2)].data, header = imgdat[('D2IMARR', 2)].header, 
			name = 'D2IMARR', ver = 2))
	if (d2im1 == 'EXTVER: 3') & (d2im2 == 'EXTVER: 4'):
		hdlist.append(fits.ImageHDU(data = imgdat[('D2IMARR', 3)].data, header = imgdat[('D2IMARR', 3)].header, 
			name = 'D2IMARR', ver = 3))
		hdlist.append(fits.ImageHDU(data = imgdat[('D2IMARR', 4)].data, header = imgdat[('D2IMARR', 4)].header, 
			name = 'D2IMARR', ver = 4))

	if (dp1 == 'EXTVER: 1') & (dp2 == 'EXTVER: 2'):
		hdlist.append(fits.ImageHDU(data = imgdat[('WCSDVARR', 1)].data, header = imgdat[('WCSDVARR', 1)].header, 
			name = 'WCSDVARR', ver = 1))
		hdlist.append(fits.ImageHDU(data = imgdat[('WCSDVARR', 2)].data, header = imgdat[('WCSDVARR', 2)].header, 
			name = 'WCSDVARR', ver = 2))
	if (dp1 == 'EXTVER: 3') & (dp2 == 'EXTVER: 4'):
		hdlist.append(fits.ImageHDU(data = imgdat[('WCSDVARR', 3)].data, header = imgdat[('WCSDVARR', 3)].header, 
			name = 'WCSDVARR', ver = 3))
		hdlist.append(fits.ImageHDU(data = imgdat[('WCSDVARR', 4)].data, header = imgdat[('WCSDVARR', 4)].header, 
			name = 'WCSDVARR', ver = 4))

	if imcam in ['NIRCAM', 'MIRI', 'NIRISS']:
		hdlist.append(fits.ImageHDU(data = imgdat['AREA', 1].data, header = imgdat['AREA', 1].header))
		hdlist.append(fits.ImageHDU(data = imgdat['VAR_POISSON', 1].data, header = imgdat['VAR_POISSON', 1].header))
		hdlist.append(fits.ImageHDU(data = imgdat['VAR_RNOISE', 1].data, header = imgdat['VAR_RNOISE', 1].header))
		hdlist.append(fits.ImageHDU(data = imgdat['VAR_FLAT', 1].data, header = imgdat['VAR_FLAT', 1].header))
		hdlist.append(fits.BinTableHDU(data = imgdat['ASDF', 1].data, header = imgdat['ASDF', 1].header))

	hdulist = fits.HDUList(hdlist)

	if img.split('_')[-1] != '_c0m.fits':
		hdulist.writeto(modname)

	if img.split('_')[-1] == '_c0m.fits':
		modname = modname.replace('_topsf.fits', '_topsf_c0m.fits')
		hdulist.writeto(modname)
		os.system('cp %s %s'%(img.replace('c0m.fits', 'c1m.fits'), modname.replace('c0m.fits', 'c1m.fits')))


def mask_fits(img, ext = 1, maskdq = True, dqthresh = 0, 
	maskerr = False, errthresh = 20, usermask = None, fillval = 0):
	"""
	Generate a FITS file that fills in masked pixels with a specified value. Useful for
	feeding to e.g., SExtractor. Preserves truncated FITS extension structure, for the specified
	extension on which the the mask was applied plus ERR and DQ extensions. 
	(Assumes that extensions are named SCI, ERR, DQ.)

	Parameters:
		img (str): Path to image to which mask is applied.
		ext (int): Integer index for *version* of extension to which mask should be applied.
			This will be used to index dat[('SCI', ext)] etc.
		maskdq (bool): If True, masks values above dqthresh.
		dqthresh (float): Maximum acceptable value in DQ image. Pixels above dqthresh will be masked.
		maskerr (bool): If True, masks values above errthresh.
		errthresh (float): Maximum acceptable value in ERR image. Pixels above errthresh will be masked.
		usermask (arr): If specified, used as mask on data array (good pixels should have value of 0). 
			Must be the same dimensions as the data array. (Can be used in addition to DQ and ERR masking.)
		fillval (float): Value with which to fill the masked pixels.

	Returns: 
		Generates a new FITS file with a _mask suffix with masked pixels filled in by fillval.

	"""

	imgdat = fits.open(img)

	cphdr = fits.PrimaryHDU(header = imgdat[0].header)

	hdr = imgdat[('SCI', ext)].header
	dat = imgdat[('SCI', ext)].data

	if img.split('_')[-1] == '_c0m.fits':

		errdat = fits.open(img.split('_')[:-1]+'_c1m.fits')

		dq = errdat[('DQ', ext)].data
		err = errdat[('ERR', ext)].data

		if maskdq:
			dat[dq > dqthresh] = fillval
		if maskerr:
			dat[err > errthresh] = fillval
		if usermask:
			dat[usermask > 0] = fillval

		cihdr = fits.ImageHDU(data = dat, header = hdr, name = 'SCI')
		cehdr = fits.ImageHDU(data = err, header = errdat[('ERR', ext)].header, name = 'ERR')
		cdqhdr = fits.ImageHDU(data = dq, header = errdat[('DQ', ext)].header, name = 'DQ')


	else:

		dq = imgdat[('DQ', ext)].data
		err = imgdat[('ERR', ext)].data

		if maskdq:
			dat[dq > dqthresh] = fillval
		if maskerr:
			dat[err > errthresh] = fillval
		if usermask:
			dat[usermask > 0] = fillval

		cihdr = fits.ImageHDU(data = dat, header = hdr, name = 'SCI')
		cehdr = fits.ImageHDU(data = err, header = imgdat[('ERR', ext)].header, name = 'ERR')
		cdqhdr = fits.ImageHDU(data = dq, header = imgdat[('DQ', ext)].header, name = 'DQ')


	hdlist = [cphdr, cihdr, cehdr, cdqhdr]

	hdulist = fits.HDUList(hdlist)
	hdulist.writeto(img.replace('.fits', '_mask.fits'))


def cutout(img, coords, ext = 1, fov_pixel = 120, save = True):
	"""
	Get cutout of image around some coordinates.

	Parameters:
		img (str): Path to image to crop.
		coords (astropy skycoords object): Coordinates of object of interest or list of skycoord objects.
			Easiest is to feed in the output of spike.tools.objloc.
		ext (int): Integer index of extension to crop.
		fov_pixel (int): Diameter of square cutout region in pixels.
		save (bool): If True, will save a FITS file containing cropped region.

	Returns: 
		cutoutim (arr): Array containing cutout region of the image.

		If save = True, will save a cropped version of the .fits file (given 
		image name + _crop suffix), including modified WCS.
	"""

	imgdat = fits.open(img)

	cphdr = fits.PrimaryHDU(header = imgdat[0].header)

	dat = imgdat[ext].data
	hdr = imgdat[ext].header

	wcs = WCS(hdr, imgdat)
	pos = utils.skycoord_to_pixel(coords, wcs)

	x0 = int(pos[0])
	y0 = int(pos[1])

	xmin = x0 - fov_pixel//2
	xmax = x0 + fov_pixel//2
	ymin = y0 - fov_pixel//2
	ymax = y0 + fov_pixel//2

	if fov_pixel % 2 == 0:
		coords0 = utils.pixel_to_skycoords((x0, y0), wcs)
		ra = coords0.ra.deg
		dec = coords0.dec.deg
		cutoutim = dat[ymin:ymax, xmin:xmax]
	if fov_pixel % 2 != 0:
		ra = coords.ra.deg
		dec = coords.dec.deg
		cutoutim = dat[ymin:ymax+1, xmin:xmax+1]

	hdr['CRVAL1'] = ra
	hdr['CRVAL2'] = dec
	hdr['CRPIX1'] = fov_pixel//2
	hdr['CRPIX2'] = fov_pixel//2
	hdr['NAXIS1'] = fov_pixel
	hdr['NAXIS2'] = fov_pixel

	cihdr = fits.ImageHDU(data = cutoutim, header = hdr, name = 'SCI')

	hdlist = [cphdr, cihdr]
	hdulist = fits.HDUList(hdlist)
	if save:
		hdulist.writeto(img.replace('.fits', '_crop.fits'))

	return cutoutim


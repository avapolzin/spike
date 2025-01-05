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
				HST: 'ACS', 'WFC3', 'WFPC', WFPC2', 'NICMOS', 'STIS'
				JWST: 'MIRI', 'NIRCAM', 'NIRISS'
				Roman: 'WFI', 'CGI'
		camera (str): Camera associated with instrument.
				HST/ACS: 'WFC', 'HRC'
				HST/WFC3: 'UVIS', 'IR'
				JWST/NIRISS: 'Imaging', 'AMI' #AMI has different multi-extension mode

	Returns:
		[X, Y, chip, filter] (list): Pixel coordinates, chip number (HST) or detector name (JWST/Roman) -- 
			if relevant, and filter name.
			Only returned if object coordinates fall onto detector - returns NaNs if not.
			Also generates duplicate "topsf" image which will be used in PSF drizzling.

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
		if np.isnan(chip):
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
					out = [[xcoord_out[i], ycoord_out[i], chip_out[i], filt] for i in range(len(coords))]
				if len(xcoord_out) == 0:
					out = [np.nan] * 4
			if type(coords) == astropy.coordinates.sky_coordinate.SkyCoord:
				check = utils.skycoord_to_pixel(coords, wcs1)
				if np.logical_and(0 <= check[0] <= datshape[0], 0 <= check[1] <= datshape[1]):
					x_coord = check[0]
					y_coord = check[1]

					chip = np.where(np.array(chips) == a)[0][0] + 1
					
		if np.isnan(chip):
			out = [np.nan, np.nan, chip, np.nan]
		else:
			out = [float(x_coord), float(y_coord), chip, filt]


	if imcam in ['ACS/HRC', 'WFC3/IR', 'MIRI', 'NIRCAM', 'NIRISS/IMAGING', 'WFI', 'CGI']:
		# for WFC3, only checks the final readout by design
		chip = 0 #no chip
		wcs1 = WCS(hdu[1].header, fobj = hdu)
		datshape = hdu[1].data.shape[::-1] #transposed based on numpy vs. fits preference
		check = utils.skycoord_to_pixel(coord, wcs)
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

	#STIS and NICMOS?


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
		os.system('cp '+ CONFIG_PATH +'sextractor_config/* .')
	if config:
		configpath = config

	sextractor_args = 'sex '+img_path+' -c '+configpath

	if userargs:
		sextractor_args += ' '+userargs

	os.system(sextractor_args)
	os.system('mv test.cat ' + img_path.replace('fits', 'cat')) #move to img name

	if (not keepconfig) and (not config):
		# clean up user directory by removing copied files
		os.system('rm default*')
		os.system('rm *.conv')


def regrid (im, sample):
	"""
	Regrid PSF model to input pixel scale.

	Parameters:
		im (arr): PSF image array.
		sample (float): If sample > 1, oversampled; if sample < 1, undersampled.

	Returns:
		Interpolated and regridded PSF model.

	"""

	if sample == 1.:
		return im

	x,y = im.shape
	xnew = np.linspace(0, x, 1/sample)
	ynew = np.linspace(0, y, 1/sample)

	spline = RectBivariateSpline(np.arange(x), np.arange(y), im)
	out = spline(xnew, ynew)

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
			psfmodel = regrid(psfmodel, psfexmodel[1].header['PSF_SAMP'])

	if save:
		if save.lower() not in ['arr', 'fits']:
			warnings.warn('Save input must be "arr" or "fits". Generating PSF model without saving.', Warning, stacklevel = 2)
		if save.lower() == 'arr':
			np.save(psfpath.replace('.psf', '_psfex_psf.npy'), psfmodel)
		if save.lower() == 'fits':
			fits.writeto(psfpath.replace('.psf', '_psfex_psf.fits'), psfmodel)

	return psfmodel


def pypsfex(cat_path, pos, config = None, userargs = None, makepsf = True, 
	savepsf = False, keepconfig = False):
	"""
	Wrapper to easily call PSFEx from python. 

	Parameters:
		cat_path (str): Path to the SExtractor catalog from the working directory.
		pos(tuple): Pixel (and spectral) location of object of interest in (x, y, chip, filter) - as from spike.tools.checkpixloc.
			If not specified, generates generic model assuming basis vectors are equally weighted.
		config (str): If specifying custom config, path to config file. If none, uses default.psfex.
		userargs (str): Any additional command line arguments to feed to PSFEx. The preferred way to include
			user arguments is via specification in the config file as command line arguments simply override the 
			corresponding configuration setting.
		makepsf (bool): If True, returns 2D PSF model.
		savepsf (str): If 'fits', 'arr', or 'txt', will save 2D model PSF in that file format with the same name as the catalog.
		keepconfig (str): If True, retain parameter files and convolutional kernels moved to working dir.

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

		if coords:
			x, y, chip, filts = pos

		if not coords:
			#assumes that .cat and .fits file are in the same directory
			im = fits.open(cat_path.replace('cat', 'fits'))[1].data
			x, y = im.shape/2 #select central pixel if not specified


		psfmodel = psfexim(cat_path.replace('cat', 'psf'), pixloc = (x, y), save = savepsf)
			
		return psfmodel


def photutils_seg():
	return placeholder


def rewrite_fits(psfarr, coords, img, imcam, pos):
	"""
	Write relevant image headers to the model PSFs and modify the coordinates and WCS.
	Creates a full _topsf.fits file with only one SCI extension for use with drizzle/resample.

	Parameters:
		psfarr (arr): The 2D PSF model.
		coords (astropy skycoord object): Coordinates of object of interest or list of skycoord objects.
		img (str): Path to image for which PSF is generated.
		imcam (str): 'ACS/WFC' is the only recommended instrument/camera combination for this PSF generation method.
		pos (list): Location of object of interest (spatial and spectral).[X, Y, chip, filter]

	Returns: 
		Generates a new FITS file with a _topsf suffix, which stores the 2D PSF model in the 
		'SCI' extension and inherits the header information from the original image.

	"""

	CRVAL1 = coords.ra.deg #reference RA/Dec set to location at which PSF was generated
	CRVAL2 = coords.dec.deg
	CRPIX1 = psfarr.shape[1]//2 #reference pixel (center) set to nearest integer, order doesn't 
	CRPIX2 = psfarr.shape[0]//2 #matter since psf should be square, but this follows np vs fits

	ext = 1
	if (imcam in ['ACS/WFC', 'WFC3/UVIS']) and (pos[2] == 1):
		ext = 4
	if (imcam in ['ACS/WFC', 'WFC3/UVIS']) and (pos[2] == 2):
		ext = 1 #yes, it's already 1, but this is to make things explicit
	if imcam in ['WFPC', 'WFPC1', 'WFPC2']:
		ext = pos[2]

	imgdat = fits.open(img)

	cphdr = fits.PrimaryHDU(header = imgdat[0].header)

	hdr = imgdat[ext].header
	hdr['CRVAL1'] = CRVAL1
	hdr['CRVAL2'] = CRVAL2
	hdr['CRPIX1'] = CRPIX1
	hdr['CRPIX2'] = CRPIX2
	# have to add the pixel-corrected tweak parameters
	cihdr = fits.ImageHDU(data = psfarr, header = hdr, name = 'SCI')

	coordstring = str(coords.ra)
	if coords.dec.deg > 0:
		coordstring += '+'+str(coords.dec)
	if coords.dec.deg >= 0:
		coordstring += str(coords.dec)

	modname = img.replace('.fits', '_'+coordstring+'_%s'%pos[3]+'_topsf.fits')

	hdulist = fits.HDUList([cphdr, cihdr])
	hdulist.writeto(modname)



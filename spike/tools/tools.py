from asdf import AsdfFile
from astropy.coordinates import SkyCoord, name_resolve
import astropy
import astropy.units as u
from astropy.io import fits
from astropy.wcs import WCS, utils
import numpy as np
import os
import pkg_resources
CONFIG_PATH = pkg_resources.resource_filename('spike', 'configs/')


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
				HST: 'ACS', 'WFC3', 'WFPC1', WFPC2', 'FOC', 'NICMOS', 'STIS'
				JWST: 'MIRI', 'NIRCAM', 'NIRISS'
				Roman: 'WFI', 'CGI'
		camera (str): Camera associated with instrument.
				HST/ACS: 'WFC', 'HRC'
				HST/WFC3: 'UVIS', 'IR'
				JWST/NIRISS: 'Imaging', 'AMI' #AMI has different multi-extension mode

	Returns:
		[X, Y, chip] (list): Pixel coordinates and, if relevant, chip number (HST) or detector name (Roman).
				Only returned if object coordinates fall onto detector - returns NaNs if not.

	"""
	hdu = fits.open(img)
	if camera:
		imcam = inst.upper() + '/' + camera.upper()
	if not camera:
		imcam = inst.upper()

	### instrument checks ###
	if imcam in ['ACS/WFC', 'WFC3/UVIS']:
		chip1 = hdu[4]
		chip2 = hdu[1]
		chips = [chip1, chip2]

		chip = np.nan
		for a in chips:
			wcs1 = WCS(a.header, fobj = hdu)
			datshape = a.data.shape
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
					out = [[xcoord_out[i], ycoord_out[i], chip_out[i]] for i in range(len(coords))]
				if len(xcoord_out) == 0:
					out = [np.nan] * 3
			if type(coords) == astropy.coordinates.sky_coordinate.SkyCoord:
				check = utils.skycoord_to_pixel(coords, wcs1)
				if np.logical_and(0 <= check[0] <= datshape[0], 0 <= check[1] <= datshape[1]):
					x_coord = check[0]
					y_coord = check[1]
					if a == chip1:
						chip = '1'
					if a == chip2:
						chip = '2'
		if np.isnan(chip):
			out = [np.nan, np.nan, chip]
		else:
			out = [x_coord, y_coord, chip]
			os.system('cp '+img+' '+img.replace('.fits', '_topsf.fits')) #generate img to tweak + drizzle
			## generating the image and will process it in future step
			## actually will want to process here so that I can Tweak
			## then will drizzle the _topsf ones with the PSFs overwriting the other data
			## should actually be fairly simple (famous last words)



	if imcam in ['ACS/HRC', 'WFC3/IR', 'MIRI', 'NIRCAM', 'NIRISS/IMAGING']:
		# for WFC3, only checks the final readout by design
		chip = 0 #no chip
		wcs1 = WCS(hdu[1].header, fobj = hdu)
		datshape = hdu[1].data.shape
		check = utils.skycoord_to_pixel(coord, wcs)
		if np.logical_and(0 <= check[0] <= datshape[0], 0 <= check[1] <= datshape[1]):
			x_coord = check[0]
			y_coord = check[1]
			out = [x_coord, y_coord, chip]
			os.system('cp '+img+' '+img.replace('.fits', '_topsf.fits')) #generate img to tweak + drizzle
		else:
			out = [np.nan] * 3

	# if imcam in ['WFI', 'CGI']: #need to get detector name rather than chip number
	# 	#will have to look at simulated imaging to see how to do this
	# 	#detectors all lead to individual files, so will have to understand what part of name
	#   #or which part of header stores identifier

	# also still need to add all of the other HST imaging modes -- WFPC2 etc. BLERGH



	return out


def to_asdf(fitspath, save = True):
	"""
	Convert .fits file to .asdf, by simply wrapping data and header extensions.

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
		userargs (str): Any additional command line arguments to feed to SExtractor.
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



def psfexim(psfpath, pixloc, save = False):
	"""
	Generate image from PSFEx .psf file.

	Parameters:
		psfpath (str): Path to the relevant .psf file from the working directory.
		pixloc (tuple): Pixel location of object of interest in (x, y).
		save (str): If 'fits', 'arr', 'txt', will save in the specified format with name from psfpath.
			The option to save as an array results in a .npy file.

	Returns:
		2D image of PSFEx model
	"""
	psfexmodel = fits.open(psfpath)
	x_, y_ = pixloc

	x = (x_ - psfexmodel[1].header['POLZERO1'])/psfexmodel[1].header['POLSCAL1']
	y = (y_ - psfexmodel[1].header['POLZERO2'])/psfexmodel[1].header['POLSCAL2']




	return psfmodel



	## FINISH THIS ONEEEEEEE

def pypsfex(cat_path, pixloc = None, config = None, userargs = None, makepsf = True, keepconfig = False):
	"""
	Wrapper to easily call PSFEx from python. 

	Parameters:
		cat_path (str): Path to the SExtractor catalog from the working directory.
		pixloc (tuple): Pixel location of object of interest in (x, y, chip) - as from spike.tools.checkpixloc.
			If not specified, generates generic model assuming basis vectors are equally weighted.
		config (str): If specifying custom config, path to config file. If none, uses default.psfex.
		userargs (str): Any additional command line arguments to feed to PSFEx.
		makepsf (bool): If True, returns 2D PSF model.
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

	psfex_args = 'psfex'+cat_path+' -c '+configpath

	if userargs:
		psfex_args += ' '+userargs

	os.system(psfex_args)
	os.system('mv test.psf ' + img_path.replace('fits', 'psf')) #move to img name

	if (not keepconfig) and (not config):
		# clean up user directory by removing copied files
		os.system('rm default*')
		os.system('rm *.conv')

	if makepsf:
		sfexmodel = fits.open(img_path.replace('fits', 'psf'))

		if coords:
			x, y, chip = coords


		if not coords:
			## PSFEx .psf outputs store the linear basis vectors of the PSF in different extensions
			# this means a model should be a sum of over the first dimension of the .psf output
			# so to first order, this is correct, but does not account for geometric distortions
			psfmodel = np.sum(psfexmodel[1].data['PSF_MASK'][0], axis = 0)
		return psfmodel


def photutils_seg():


def rewrite_header(obj, header):
	"""
	Write HST and JWST image headers to the model PSFs and modify the coordinates and WCS.


	"""

def write_header(obj, header_params):
	"""
	Write Roman image headers to model PSFs and modify coordinates and WCS.
	Takes in dictionary of relevant header keys given size of files.


	"""



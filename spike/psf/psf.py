import os
import glob
from multiprocessing import Pool, cpu_count
from spike.tools import objloc
from astropy.io import fits
from astropy.wcs import WCS, utils
import numpy as np
import subprocess
from subprocess import call
import warnings

def warning_on_one_line(message, category, filename, lineno, file=None, line=None):
	return '%s:%s: %s: %s\n' % (filename, lineno, category.__name__, message)

warnings.formatwarning = warning_on_one_line

from drizzlepac import tweakreg, tweakback, astrodrizzle
# from spike.jwstcal import tweakreg, tweakback, resample #check name of tweak steps
# from spike.romancal import tweakreg, tweakback, resample

##########
# * * * *
##########


def hst(img_dir, obj, img_type, inst, camera, method, savepath = 'psfs/drizzledpsf.fits', drizzleimgs = False,
		pretweaked = False, keeporig = True, plot = False, verbose = False, parallel = False, out = 'fits', 
		## all of the drizzle parameters
		## all of the tweakreg parameters
		**kwargs):
	"""
	Generate drizzled HST PSFs.

	Parameters:
		img_dir (str): Path to directory containing _flt or _flc files for which model PSF will be generated.
		obj(str, arr-like): Name or coordinates of object of interest in HH:MM:DD DD:MM:SS or degree format.
		img_type (str): 'flc', 'flt', 'c0f', 'c1f', 'cal', 'calints' -- specifies which file-type to include.
		inst (str): 'ACS', 'WFC3', 'WFPC1', 'WFPC2', NICMOS', 'STIS'
		camera (str): 
		method (str): 'TinyTim', 'TinyTim_Gillis', 'STDPSF' (empirical),
				'epsf' (empirical), 'PSFEx' (empirical) -- see spike.psfgen for details -- or 'USER';
				if 'USER', method should be a function that generates, or path to a directory of user-generated, PSFs 
				named [coords]_[band]_psf.fits, e.g., 23.31+30.12_F814W_psf.fits or 195.78-46.52_F555W_psf.fits
		savepath (str): Where/with what name output drizzled PSF will be saved. Defaults to 'psfs/drizzledpsf.fits'.
		drizzleimgs (bool): If True, will drizzle the input images at the same time as creating a drizzled psf.
		pretweaked (bool): If True, skips TweakReg steps to include sub-pixel corrections.
		keeporig (bool): If True (and pretweaked = False), create copy of img_dir before TweakReg.
		plot (bool): If True, saves .pngs of the model PSFs.
		verbose (bool): If True, prints progress messages.
		parallel (bool): If True, runs PSF generation in parallel.
		out (str): 'fits' or 'asdf'. Output for the drizzled PSF. If 'asdf', .asdf AND .fits are saved.
		**kwargs: Keyword arguments for PSF generation function.
	"""

	if keeporig and not pretweaked:
		os.system('mkdir '+img_dir+'_orig')
		os.system('cp -r '+img_dir+' '+'img_dir'+'_copy')
		if verbose:
			print('Made copy of '+img_dir)


	imgs = sorted(glob.glob(img_dir+'/*'+img_type+'.fits'))

	if inst.upper() in ['ACS', 'WFC3']:
		imcam = inst.upper()+'/'+camera.upper()
	if inst.upper() in ['WFPC1', 'WFPC2', 'NICMOS', 'STIS']:
		imcam = inst.upper()

	if inst.upper() == 'WFPC2':
		updatewcs = True

	genpsf = True
	if method.upper() not in ['TINYTIM', 'TINYTIM_GILLIS', 'WFCPSF', 'STDPSF', 'EPSF', 'SEPSF', 'USER']:
		raise Exception('tool must be one of TINYTIM, TINYTIM_GILLIS, WFCPSF, STDPSF, EPSF, SEPSF, USER')
	if method.upper() == 'TINYTIM':
		if inst.upper() == 'WFC3':
			warnings.warn('TinyTim is not recommended for modeling WFC3 PSFs. See https://www.stsci.edu/hst/instrumentation/focus-and-pointing/focus/tiny-tim-hst-psf-modeling.',
				Warning, stacklevel = 2)
		psffunc = spike.psfgen.tinypsf
	if method.upper() == 'TINYTIM_GILLIS':
		psffunc = spike.psfgen.tinygillispsf
		psffunc = spike.psfgen.wfcpsf
	if method.upper() == 'EPSF':
		psffunc = spike.psfgen.effpsf
	if method.upper() == 'PSFEX':
		psffunc = spike.psfgen.psfex
	if method.upper() == 'USER':
		if type(method) == str: #check if user input is path to directory
			genpsf = False
		if type(method) != str: #or function
			psffunc = method

	if genpsf: #generate model PSFs for each image + object
		if type(obj) == str: #check number of objects
			skycoords = tools.objloc(o)
			for i in imgs:
				coords = tools.checkpixloc(skycoords, i, inst, camera)
				psffunc(coords, i, imcam, pos, **kwargs)

		if type(obj) != str: #if multiple objects, option to parallelize 
			skycoords = [] #only open each FITS file once
			for o in obj:
				skycoords.append(tools.objloc(o))
			
			for i in imgs:

				pos = tools.checkpixloc(skycoords, i, inst, camera)

				#need filter name to make PSFs drizzlable

				if parallel:
					if method.upper() == 'PSFEX':
						warnings.warn('Warning: Check your config and param files to ensure output files ...')
					pool = Pool(processes=(cpu_count() - 1))
					for coord in coords:
						pool.apply_async(psffunc, args = (coord, i, imcam, pos), kwds = kwargs)
					pool.close()
					pool.join()
				if not parallel:
					for coord in coords:
						psffunc(coords, i, imcam, pos, **kwargs) 
					

			## figure out how best to parallelize at this point


			# if not pretweaked:
				# otherwise skip the tweak steps





		# also need to iterate through files -- will need to do this with mpi4py integrated -- UGH
		# will need to decide how to iterate through objects and at what point
		# think I will name PSFs degcoord_imgname_band_psf.fits
		# can then combine on coordinates and filter easily enough
		# could add option for people to feed in a function that generates PSFs themselves, but that might be silly

		# https://hst-docs.stsci.edu/drizzpac/chapter-1-introduction-to-astrodrizzle-and-drizzlepac/1-4-data-from-the-mast-archive
		# need to figure out how WCSCORR plays into this -- that's where Tweakreg info is stored


	if out == 'asdf':
		# .asdf file read out in addition to .fits
		tools.to_asdf()



def jwst():

	return placeholder


def roman(config):
	"""
	Generate drizzled Roman Space Telescope PSFs.

	Parameters:
		

	Returns:

	"""

	return placeholder


### ADD COMMENT TO FINAL PSF FITS HEADER THAT IT WAS GENERATED WITH spike


import os
import glob
from multiprocessing import Pool, cpu_count
from spike.tools import objloc
from astropy.io import fits
from astropy.wcs import WCS, utils
import numpy as np

from drizzlepac import tweakreg, tweakback, astrodrizzle

##########
# * * * *
##########


def hst(img_dir, obj, 
	pretweaked = False, keeporig = True, plot = False, verbose = False, parallel = False, **kwargs):
	"""
	Generate drizzled HST PSFs.

	Parameters:
		img_dir (str): Path to directory containing _flt or _flc files for which model PSF will be generated.
		obj(str, arr-like): Name or coordinates of object of interest in HH:MM:DD DD:MM:SS or degree format.
		img_type (str): 'flc', 'flt', 'c0f', 'c1f' -- specifies which file-type to include.
		inst (str): 'ACS', 'WFC3', 'WFPC1', 'WFPC2', 'FOC', 'NICMOS', 'STIS'
		camera (str): 
		tool (str): 'TinyTim', 'TinyTim_Gillis', 'WFCPSF' (empirical), 'STDPSF' (empirical),
				'epsf' (empirical), 'PSFEx' (empirical) -- see spike.psfgen for details -- or 'USER';
				if 'USER', tool should be a function that generates, or path to a directory of user-generated, PSFs 
				named [coords]_[band]_psf.fits, e.g., 23.31+30.12_F814W_psf.fits or 195.78-46.52_F555W_psf.fits
		pretweaked (bool): If True, skips TweakReg steps to include sub-pixel corrections.
		keeporig (bool): If True (and pretweaked = False), create copy of img_dir before TweakReg.
		plot (bool): If True, saves .pngs of the model PSFs.
		verbose (bool): If True, prints progress messages.
		parallel (bool): If True, runs PSF generation in parallel.
		**kwargs: Keyword arguments for PSF generation function.
	"""

	if keeporig and not pretweaked:
		os.system('mkdir '+img_dir+'_orig')
		os.system('cp -r '+img_dir+' '+'img_dir'+'_copy')
		if verbose:
			print('Made copy of '+img_dir)


	imgs = glob.glob(img_dir+'/*'+img_type+'.fits')

	if inst.upper() == 'WFPC2':
		updatewcs = True

	genpsf = True
	if tool.upper() not in ['TINYTIM', 'TINYTIM_GILLIS', 'WFCPSF', 'STDPSF', 'EPSF', 'SEPSF', 'USER']:
		raise Exception('tool must be one of TINYTIM, TINYTIM_GILLIS, WFCPSF, STDPSF, EPSF, SEPSF, USER')
	if tool.upper() == 'TINYTIM':
		psffunc = spike.psfgen.tinypsf
	if tool.upper() == 'TINYTIM_GILLIS':
		psffunc = spike.psfgen.tinygillispsf
	if tool.upper() == 'WFCPSF':
		if inst != 'WFC3':
			raise Exception('spike.psfgen.wfcpsf ONLY works with HST/WFC3 images.')
		psffunc = spike.psfgen.wfcpsf
	if tool.upper() == 'EPSF':
		psffunc = spike.psfgen.effpsf
	if tool.upper() == 'SEPSF':
		psffunc = spike.psfgen.psfex
	if tool.upper() == 'USER':
		if type(tool) == str: #check if user input is path to directory
			genpsf = False
		if type(tool) != str: #or function
			psffunc = tool

	if genpsf: #generate model PSFs for each image + object
		if type(obj) == str: #check number of objects
			skycoords = tools.objloc(o)
			for i in imgs:
				coords = tools.checkpixloc(skycoords, inst, camera)
				psffunc(coords, i, **kwargs)

		if type(obj) != str: #if multiple objects, option to parallelize 
			skycoords = [] #only open each FITS file once
			for o in obj:
				skycoords.append(tools.objloc(o))
			
			for i in imgs:

				coords = tools.checkpixloc(skycoords, inst, camera)

				#need filter name to make PSFs drizzlable

				if parallel:
					pool = Pool(processes=(cpu_count() - 1))
					for coord in coords:
						pool.apply_async(psffunc, args = (coord, i), kwds = kwargs)
					pool.close()
					pool.join()
				if not parallel:
					for coord in coords:
						psffunc(coords, i, **kwargs) #will need to feed instrument and camera everytime
														# even if not used
														# so will need a comprehensive set of user inputs
														# in addition to kwargs
					

			## figure out how best to parallelize at this point



		# also need to iterate through files -- will need to do this with mpi4py integrated -- UGH
		# will need to decide how to iterate through objects and at what point
		# think I will name PSFs degcoord_imgname_band_psf.fits
		# can then combine on coordinates and filter easily enough
		# could add option for people to feed in a function that generates PSFs themselves, but that might be silly



def jwst():


def roman():



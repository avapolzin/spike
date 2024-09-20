import os
import glob
import mpi4py

##########
# * * * *
##########



def hst(img_dir, coords, 
	pretweaked = False, keeporig = True, plot = False, verbose = False, parallel = 1, **kwargs):
	"""
	Generate drizzled HST PSFs.

	Parameters:
		img_dir (str): Path to directory containing _flt or _flc files for which model PSF will be generated.
		coords (str, arr-like): Coordinates of object of interest in HH:MM:DD DD:MM:SS or degree format.
		img_type (str): 'flc', 'flt', 'c0f', 'c1f' -- specifies which file-type to include.
		inst (str): 'ACS', 'WFC3', 'WFPC2', 'FOC', 'NICMOS'
		tool (str): 'TinyTim', 'TinyTim_Gillis', 'WFCPSF' (empirical), 
				'epsf' (empirical), 'PSFEx' (empirical) -- see spike.psfgen for details -- or 'USER';
				if 'USER', tool should be a function that generates, or path to a directory of user-generated, PSFs 
				named [coords]_[band]_psf.fits, e.g., 23.31+30.12_F814W_psf.fits or 195.78-46.52_F555W_psf.fits
		pretweaked (bool): If True, skips TweakReg steps to include sub-pixel corrections.
		keeporig (bool): If True (and pretweaked = False), create copy of img_dir before TweakReg.
		plot (bool): If True, saves .pngs of the model PSFs.
		verbose (bool): If True, prints progress messages.
		nproc (int): If >1, runs PSF generation in parallel.
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

	for coord in coords:
		# also need to iterate through files -- will need to do this with mpi4py integrated -- UGH
		# will need to decide how to iterate through objects and at what point
		# think I will name PSFs degcoord_imgname_band_psf.fits
		# can then combine on coordinates and filter easily enough
		# could add option for people to feed in a function that generates PSFs themselves, but that might be silly

		if tool.upper() == 'TINYTIM':
			spike.psfgen.tinypsf(**kwargs)
		if tool.upper() == 'TINYTIM_GILLIS':
			spike.psfgen.tinygillispsf(**kwargs)
		if tool.upper() == 'WFCPSF':
			if inst != 'WFC3':
				raise Exception('spike.psfgen.wfcpsf ONLY works with HST/WFC3 images.')
			spike.psfgen.wfcpsf(**kwargs)
		if tool.upper() == 'EPSF':
			spike.psfgen.effpsf(**kwargs)
		if tool.upper() == 'SEPSF':
			spike.psfgen.psfex()



def jwst():


def roman():



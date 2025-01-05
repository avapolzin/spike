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

##########
# * * * *
##########


def hst(img_dir, obj, img_type, inst, camera, method, usermethod = None, 
		savepath = 'psfs/drizzledpsf.fits', drizzleimgs = False, pretweaked = False, 
		keeporig = True, plot = False, verbose = False, parallel = False, out = 'fits', 
		tweakparams = {'threshold':6.0, 
					   'searchrad':3.0, 
					   'dqbits':-16, 
					   'configobj':None, 
					   'interactive':False, 
					   'shiftfile':True, 
					   'expand_refcat':True,
					   'outshifts':'shift_searchrad.txt', 
					   'updatehdr':True,
					   'wcsname': 'TWEAK'}, 
		drizzleparams = {'preserve':False,
	    				 'driz_cr_corr':True,
						 'clean':False,
					     'configobj':None,
					     'final_pixfrac':0.8,
					     'wcskey':'TWEAK',
					     'build':True,
					     'combine_type':'imedian', 
					     'combine_nhigh':3}, 
		**kwargs):
	"""
	Generate drizzled HST PSFs.

	Parameters:
		img_dir (str): Path to directory containing calibrated files for which model PSF will be generated.
		obj(str, arr-like): Name or coordinates of object of interest in HH:MM:DD DD:MM:SS or degree format.
		img_type (str): 'flc', 'flt', 'c0f', 'c1f', 'cal', 'calints' -- specifies which file-type to include.
		inst (str): 'ACS', 'WFC3', 'WFPC', 'WFPC2', NICMOS', 'STIS'
		camera (str): 
		method (str): 'TinyTim', 'TinyTim_Gillis', 'STDPSF' (empirical),
				'epsf' (empirical), 'PSFEx' (empirical) -- see spike.psfgen for details -- or 'USER';
				if 'USER', usermethod should be a function that generates, or path to a directory of user-generated, PSFs 
				named [imgprefix]_[coords]_[band]_psf.fits, e.g., imgprefix_23.31+30.12_F814W_psf.fits or 
				imgprefix_195.78-46.52_F555W_psf.fits
		usermethod (func or str): If method = 'USER', usermethod should be a function that generates, or path to a 
				directory of user-generated, PSFs named [imgprefix]_[coords]_[band]_psf.fits, e.g., 
				imgprefix_23.31+30.12_F814W_psf.fits or imgprefix_195.78-46.52_F555W_psf.fits, where the 
				imgprefix corresponds to the name of the relevant flt/flc/c0f/c1f/... files in the directory and the 
				headers are from the original images (see spike.tools.rewrite_fits, which can be used to this end).
		savepath (str): Where/with what name output drizzled PSF will be saved. Defaults to 'psfs/drizzledpsf.fits'.
		drizzleimgs (bool): If True, will drizzle the input images at the same time as creating a drizzled psf.
		pretweaked (bool): If True, skips TweakReg steps to include sub-pixel corrections.
		keeporig (bool): If True (and pretweaked = False), create copy of img_dir before TweakReg.
		plot (bool): If True, saves .pngs of the model PSFs.
		verbose (bool): If True, prints progress messages.
		parallel (bool): If True, runs PSF generation in parallel.
		out (str): 'fits' or 'asdf'. Output for the drizzled PSF. If 'asdf', .asdf AND .fits are saved.
		tweakparams (dict): Dictionary of keyword arguments for drizzlepac.tweakreg. See the drizzlepac documentation
			for a full list.
		drizzleparams (dict): Dictionary of keyword arguments for drizzlepac.astrodrizzle. See the drizzlepac 
			documentation for a full list.
		**kwargs: Keyword arguments for PSF generation function.
	"""
	from drizzlepac import tweakreg, tweakback, astrodrizzle


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
	if method.upper() not in ['TINYTIM', 'TINYTIM_GILLIS', 'STDPSF', 'EPSF', 'PSFEX', 'USER']:
		raise Exception('tool must be one of TINYTIM, TINYTIM_GILLIS, STDPSF, EPSF, PSFEX, USER')
	if method.upper() == 'TINYTIM':
		if inst.upper() == 'WFC3':
			warnings.warn('TinyTim is not recommended for modeling WFC3 PSFs. See https://www.stsci.edu/hst/instrumentation/focus-and-pointing/focus/tiny-tim-hst-psf-modeling.',
				Warning, stacklevel = 2)
		psffunc = spike.psfgen.tinypsf
	if method.upper() == 'TINYTIM_GILLIS':
		if (inst.upper() != 'ACS') and (camera.upper() != 'WFC'):
			warnings.warn('The Gillis (2019) code is made for/tested on ACS/WFC and no modification is made here to generalize it to other HST instruments/cameras.')
		psffunc = spike.psfgen.tinygillispsf
	if method.upper() == 'EPSF':
		psffunc = spike.psfgen.effpsf
	if method.upper() == 'PSFEX':
		psffunc = spike.psfgen.psfex
	if method.upper() == 'USER':
		if type(usermethod) == str: #check if user input is path to directory
			genpsf = False
		if type(usermethod) != str: #or function
			psffunc = method

	if not pretweaked:
		# need to add these arguments to options above
		tweakreg.TweakReg(imgs, **tweakparams)

	drizzlelist = {} #write file prefixes to drizzle per object per filter
	if genpsf: #generate model PSFs for each image + object
		if type(obj) == str: #check number of objects
			drizzlelist[obj] = {}
			skycoords = tools.objloc(o)
			for i in imgs:
				pos = tools.checkpixloc(skycoords, i, inst, camera)
				if np.isfinite(pos[0]): #confirm object falls onto image
					if pos[3] not in drizzlelist.keys():
						drizzlelist[pos[3]] = []
					drizzlelist[obj][pos[3]].append(i)

					psffunc(coords, i, imcam, pos, **kwargs)

		if type(obj) != str: #if multiple objects, option to parallelize 
			skycoords = [] #only open each FITS file once

			for o in obj:
				drizzlelist[o] = {}
				skycoords.append(tools.objloc(o))
			
			for i in imgs:

				pos = tools.checkpixloc(skycoords, i, inst, camera)

				if parallel:
					if method.upper() == 'PSFEX':
						warnings.warn('Warning: Check your config and param files to ensure output files have unique names.', Warning, stacklevel = 2)
					pool = Pool(processes=(cpu_count() - 1))
					for j, p in enumerate(pos):
						if np.isfinite(p[0]): #confirm that object falls onto detector
							if pos[3] not in drizzlelist[obj[j]].keys():
								drizzlelist[obj[j]][pos[3]] = []
							drizzlelist[obj[j]][pos[3]].append(i)

							pool.apply_async(psffunc, args = (skycoords[j], i, imcam, p), kwds = kwargs)
					pool.close()
					pool.join()
				if not parallel:
					for coord in coords:
						psffunc(coords, i, imcam, pos, **kwargs) 
					
	if not genpsf:
		userpsfs = sorted(glob.glob(usermethod))

		for up in userpsfs:
			im, obj, filt, _ = up.split('_')
			if obj not in drizzlelist.keys():
				drizzlelist[obj] = {}
			if filt not in drizzlelist[obj].keys():
				drizzlelist[obj][filt] = []
			drizzlelist[obj][filt].append(im)
			


			## also need to parallelize the drizzling of PSFs by object


	if keeporig:
		drizzleparams['preserve'] = True #reset parameter to ensure that original files maintained
	# if method.upper() in ['EPSF', 'PSFEX']:
	# 	drizzleparams['drizz_cr_corr'] = False #CR-corrected imgs will already exist from PSF generation






	if out == 'asdf':
		# .asdf file read out in addition to .fits
		tools.to_asdf()



def jwst(usecrds = False):
	"""

	usecrds (bool): If True, use CRDS config settings as defaults. 

	"""

	os.environ['CRDS_SERVER_URL']="https://jwst-crds.stsci.edu"
	from spike.jwstcal import tweakreg_tweakreg_step, resample


	# resample.([jwdatamodel(i) for i in imgs]) # this is total placeholder to get down an idea \
	# for working with datamodels
	# not sure how the infrastructure works for CR removal or for tweaking for that matter
	# but will figure it out for JWST and then use the same for roman

	return placeholder


def roman(config, usecrds = False):
	"""
	Generate drizzled Roman Space Telescope PSFs.

	Parameters:
		

	Returns:

	"""
	os.environ['CRDS_SERVER_URL']="https://roman-crds.stsci.edu"
	from spike.romancal import tweakreg_step, resample

	return placeholder


### ADD COMMENT TO FINAL PSF FITS HEADER THAT IT WAS GENERATED WITH spike


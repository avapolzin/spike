import os
import glob
from multiprocessing import Pool, cpu_count
from spike import psfgen, tools
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


def hst(img_dir, obj, img_type, inst, camera = None, method='TinyTim', usermethod = None, 
		savedir = 'psfs', drizzleimgs = False, objonly = True, pretweaked = False,
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
						 'driz_cr_corr':False,
						 'clean':False,
						 'configobj':None,
						 'final_pixfrac':0.8,
						 'build':True,
						 'combine_type':'imedian',
						 'static':False},
		returnpsf = 'full',
		cutout_fov = 151,
		savecutout = True,
		finalonly = False,
		removedir = 'toremove',
		**kwargs):
	"""
	Generate drizzled HST PSFs.

	Parameters:
		img_dir (str): Path to directory containing calibrated files for which model PSF will be generated.
			If using the tweakreg step, best to include a drizzled file, as well, which can be used as a reference.
		obj(str, arr-like): Name or coordinates of object of interest in HH:MM:DD DD:MM:SS or degree format.
		img_type (str): e.g, 'flc', 'flt', 'cal', 'c0m' -- specifies which file-type to include.
			spike currently only works with MEF files (since astrodrizzle only works with MEF files).
		inst (str): 'ACS', 'WFC3', 'WFPC', 'WFPC2', NICMOS'
		camera (str): 'WFC', 'HRC' (ACS), 'UVIS', 'IR' (WFC3) -- MUST BE SPECIFIED FOR ACS, WFC3
		method (str): 'TinyTim', 'TinyTim_Gillis', 'STDPSF' (empirical),
				'epsf' (empirical), 'PSFEx' (empirical) -- see spike.psfgen for details -- or 'USER';
				if 'USER', usermethod should be a function that generates, or path to a directory of user-generated, PSFs 
				named [imgprefix]_[coords]_[band]_topsf.fits, e.g., imgprefix_23.31+30.12_F814W_topsf.fits or 
				imgprefix_195.78-46.52_F555W_topsf.fits
		usermethod (func or str): If method = 'USER', usermethod should be a function that generates, or path to a 
				directory of user-generated, PSFs named [imgprefix]_[coords]_[band]_psf.fits, e.g., 
				imgprefix_23.31+30.12_F814W_psf.fits or imgprefix_195.78-46.52_F555W_psf.fits, where the 
				imgprefix corresponds to the name of the relevant flt/flc/c0f/c1f/... files in the directory and the 
				headers are from the original images (see spike.tools.rewrite_fits, which can be used to this end).
		savedir (str): Where the PSF models and drizzled PSF will be saved. Defaults to 'psfs'.
		drizzleimgs (bool): If True, will drizzle the input images at the same time as creating a drizzled psf.
		objonly (bool): If True, only drizzles input images that cover the selected obj.
		pretweaked (bool): If True, skips TweakReg steps to include fine WCS corrections.
		keeporig (bool): If True (and pretweaked = False), create copy of img_dir before TweakReg.
		plot (bool): If True, saves .pngs of the model PSFs.
		verbose (bool): If True, prints progress messages.
		parallel (bool): If True, runs PSF generation in parallel.
		out (str): 'fits' or 'asdf'. Output for the drizzled PSF. If 'asdf', .asdf AND .fits are saved.
		tweakparams (dict): Dictionary of keyword arguments for drizzlepac.tweakreg. See the drizzlepac documentation
			for a full list.
		drizzleparams (dict): Dictionary of keyword arguments for drizzlepac.astrodrizzle. See the drizzlepac 
			documentation for a full list.
		returnpsf (str): 'full', 'crop', or None. If None, spike.psf.hst does not return anything. If 'full' (default),
			returns the PSF in the full spatial context of the processed image. If 'crop', returns the region immediately
			around the PSF (size of cutout set by cutout_fov).
		cutout_fov (int): Side length in pixels of square cutout region centered on PSF. Used if returnpsf = 'crop'.
		savecutout (bool): If True, save a .fits file with the cutout region, including WCS. Only used if returnpsf = 'crop'.
		finalonly (bool): If True, only retains final drizzled/resampled data products in savedir and deletes intermediate products.
		removedir (str): Directory (**to be deleted**) that stores intermediate products for removal. Default is 'toremove'.
		**kwargs: Keyword arguments for PSF generation function.

	Returns:
		Generates model PSFs and drizzled PSF. (If drizzledimgs = True, also produces drizzled image from input files.)

		If returnpsf = 'full', will return each of the full drizzled PSF images in an object, filter indexed dict.
		If returnpsf = 'crop', will return a cutout region of the drizzled PSF images (around the PSF) in an obj, filt indexed dict.
	"""
	from drizzlepac import tweakreg, tweakback, astrodrizzle

	if img_type.lower() in ['drc', 'drz']:
		raise Exception('%s files are already drizzled. spike works with calibrated, but not-yet-combined images -- e.g., flc, crf, cal.'%img_type)

	if img_dir[:-1] != '/':
		img_dir += '/' #force paths to work out

	if keeporig and not pretweaked:
		if not os.path.exists(img_dir+'_orig'):
			os.makedirs(img_dir+'_orig')
		os.system('cp -r '+img_dir+'*_'+img_type+'.fits '+img_dir+'_orig')
		if verbose:
			print('Made copy of '+img_dir)


	imgs = sorted(glob.glob(img_dir+'*'+img_type+'.fits'))

	if inst.upper() in ['ACS', 'WFC3']:
		imcam = inst.upper()+'/'+camera.upper()
	if inst.upper() in ['WFPC1', 'WFPC2', 'NICMOS', 'STIS']:
		imcam = inst.upper()

	if inst.upper() == 'WFPC2':
		updatewcs = True

	genpsf = True
	if method.upper() not in ['TINYTIM', 'TINYTIM_GILLIS', 'STDPSF', 'EPSF', 'PSFEX', 'USER']:
		raise Exception('method must be one of TINYTIM, TINYTIM_GILLIS, STDPSF, EPSF, PSFEX, USER')
	if method.upper() == 'TINYTIM':
		if inst.upper() == 'WFC3':
			warnings.warn('TinyTim is not recommended for modeling WFC3 PSFs. See https://www.stsci.edu/hst/instrumentation/focus-and-pointing/focus/tiny-tim-hst-psf-modeling.',
				Warning, stacklevel = 2)
		psffunc = psfgen.tinypsf
	if method.upper() == 'TINYTIM_GILLIS':
		if (inst.upper() != 'ACS') and (camera.upper() != 'WFC'):
			warnings.warn('The Gillis (2019) code is made for/tested on ACS/WFC and no modification is made here to generalize it to other HST instruments/cameras.')
		psffunc = psfgen.tinygillispsf
	if method.upper() == 'STDPSF':
		if inst.upper() in ['WFPC', 'WFPC1']:
			raise ValueError("There is no available STDPSF grid for WFPC imaging. Please select a different PSF generation method.")
		psffunc = psfgen.stdpsf
	if method.upper() == 'EPSF':
		psffunc = psfgen.effpsf
	if method.upper() == 'PSFEX':
		psffunc = psfgen.psfex
	if method.upper() == 'USER':
		if type(usermethod) == str: #check if user input is path to directory
			genpsf = False
		if type(usermethod) != str: #or function
			psffunc = method

	filelist = {} # generate list of files to tweak -- by filter
	for fi in imgs:
		hdu = fits.open(fi)
		try: #get filter
			filt = hdu[0].header['FILTER']
		except:
			if hdu[0].header['FILTER1'].startswith('F'):
				filt = hdu[0].header['FILTER1']
			else:
				filt = hdu[0].header['FILTER2']
		if filt not in filelist.keys():
			filelist[filt] = []
		filelist[filt].append(fi)

	if not pretweaked:
		# note that if there are many input files, tweakreg will be very slow and prone
		# to overuse of RAM	
		for fk in filelist.keys():
			tweakreg.TweakReg(filelist[fk], **tweakparams)

	drizzlelist = {} #write file prefixes to drizzle per object per filter
	imglist = {} #images to drizzle per object per filter (used if objonly = True)
	if genpsf: #generate model PSFs for each image + object
		if type(obj) == str: #check number of objects
			drizzlelist[obj] = {}
			imglist[obj] = {}
			skycoords = tools.objloc(obj)
			for i in imgs:
				pos = tools.checkpixloc(skycoords, i, inst, camera)

				coordstring = str(skycoords.ra)
				if skycoords.dec.deg >= 0:
					coordstring += '+'+str(skycoords.dec)
				if skycoords.dec.deg < 0:
					coordstring += str(skycoords.dec)

				modname = i.replace('%s.fits'%img_type, coordstring+'_%s'%pos[3]+'_topsf_%s.fits'%img_type)
				if np.isfinite(pos[0]): #confirm object falls onto image
					if pos[3] not in drizzlelist[obj].keys():
						drizzlelist[obj][pos[3]] = []
						imglist[obj][pos[3]] = []
					drizzlelist[obj][pos[3]].append(modname)
					imglist[obj][pos[3]].append(i)


					psffunc(skycoords, i, imcam, pos, plot, verbose, **kwargs)

		if type(obj) != str: #if multiple objects, option to parallelize 
			skycoords = [] #only open each FITS file once

			for o in obj:
				drizzlelist[o] = {}
				imglist[o] = {}
				skycoords.append(tools.objloc(o))
			
			for i in imgs:

				if parallel:
					if method.upper() == 'PSFEX':
						warnings.warn('Warning: Check your config and param files to ensure output files have unique names.', Warning, stacklevel = 2)
					pool = Pool(processes=(cpu_count() - 1))
					for j, coord in enumerate(skycoords):

						pos = tools.checkpixloc(coord, i, inst, camera)

						coordstring = str(coord.ra)
						if coord.dec.deg >= 0:
							coordstring += '+'+str(coord.dec)
						if coord.dec.deg < 0:
							coordstring += str(coord.dec)

						modname = i.replace('%s.fits'%img_type, coordstring+'_%s'%pos[3]+'_topsf_%s.fits'%img_type)
						if np.isfinite(pos[0]): #confirm that object falls onto detector
							if pos[3] not in drizzlelist[obj[j]].keys():
								drizzlelist[obj[j]][pos[3]] = []
								imglist[obj[j]][pos[3]] = []
							drizzlelist[obj[j]][pos[3]].append(modname)
							imglist[obj[j]][pos[3]].append(i)

							pool.apply_async(psffunc, args = (coord, i, imcam, pos, plot, verbose), kwds = kwargs)
					pool.close()
					pool.join()

				if not parallel:
					for j, coord in enumerate(skycoords):
						pos = tools.checkpixloc(coord, i, inst, camera)

						coordstring = str(coord.ra)
						if coord.dec.deg >= 0:
							coordstring += '+'+str(coord.dec)
						if coord.dec.deg < 0:
							coordstring += str(coord.dec)

						modname = i.replace('%s.fits'%img_type, coordstring+'_%s'%pos[3]+'_topsf_%s.fits'%img_type)
						if np.isfinite(pos[0]): #confirm that object falls onto detector
							if pos[3] not in drizzlelist[obj[j]].keys():
								drizzlelist[obj[j]][pos[3]] = []
								imglist[obj[j]][pos[3]] = []
							drizzlelist[obj[j]][pos[3]].append(modname)
							imglist[obj[j]][pos[3]].append(i)

						psffunc(coord, i, imcam, pos, plot, verbose, **kwargs) 
					
	if not genpsf:
		userpsfs = sorted(glob.glob(usermethod))

		for up in userpsfs:
			im, imtype, obj, filt, _ = up.split('_')

			img = imgdir+'%s_%s.fits'%(im, imtype)
			coord = tools.objloc(obj)
			pos = tools.checkpixloc(coords)

			psfmodel = fits.open(up)[1].data

			tools.rewrite_fits(psfmodel, img, coord, imcam, pos, method = 'USER')

			coordstring = str(coord.ra)
			if coord.dec.deg >= 0:
				coordstring += '+'+str(coord.dec)
			if coord.dec.deg < 0:
				coordstring += str(coord.dec)

			modname = img.replace('%s.fits'%imtype, coordstring+'_%s'%pos[3]+'_topsf_%s.fits'%imtype)

			if obj not in drizzlelist.keys():
				drizzlelist[obj] = {}
				imglist[obj] = {}
			if filt not in drizzlelist[obj].keys():
				drizzlelist[obj][filt] = []
				imglist[obj][filt] = []
			drizzlelist[obj][filt].append(modname)
			imglist[obj][filt].append(img)
			

	if keeporig:
		drizzleparams['preserve'] = True #reset parameter to ensure that original files maintained

	for do in drizzlelist.keys():
		cstring = tools.objloc(do)
		coordstring = str(cstring.ra)
		if cstring.dec.deg >= 0:
			coordstring += '+'+str(cstring.dec)
		if cstring.dec.deg < 0:
			coordstring += str(cstring.dec)

		if parallel:
			pool = Pool(processes=(cpu_count() - 1))
			for dk in drizzlelist[do].keys():
				outname = coordstring+'_'+dk+'_psf'
				drizzleparams['output'] = img_dir + outname #set output based on coord, filter
				pool.apply_async(astrodrizzle.AstroDrizzle, args = (drizzlelist[do][dk]), kwds = drizzleparams)
			pool.close()
			pool.join()
		if not parallel:
			for dk in drizzlelist[do].keys():
				outname = coordstring+'_'+dk+'_psf'
				drizzleparams['output'] = img_dir + outname #set output based on coord, filter
				astrodrizzle.AstroDrizzle(drizzlelist[do][dk], **drizzleparams)

	drzs = np.concatenate((sorted(glob.glob('%s*_drc.fits'%img_dir)), 
		sorted(glob.glob('%s*_drz.fits'%img_dir)), sorted(glob.glob('%s*_mos.fits'%img_dir))))

	if len(drzs) == 0:
		raise Exception('No co-added/resampled output files created. Check your input path, coordinates and the output of the PSF generation steps.')

	for dr in drzs: #rename drizzled outputs to something more manageable
		flist = dr.split('_')
		suff_ = flist[-1].split('.')[0]
		filt_ = flist[1]
		obj_ = flist[0]

		os.system('mv %s %s%s_%s_psf_%s.fits'%(dr, img_dir, obj_, filt_, suff_))

	suff = suff_ # store suffix, as there should be no variation within one run

	
	if drizzleimgs: # useful for processing all images + PSFs simultaneously
		drizzleparams['driz_cr_corr'] = True #reset parameters turned off for PSF
		drizzleparams['static'] = True
		if not objonly:
			for fk in filelist.keys():
				drizzleparams['output'] = img_dir + '%s_img'%fk #set output name with filter
				astrodrizzle.AstroDrizzle(filelist[fk], **drizzleparams)
		if objonly:
			for do in imglist.keys():
				cstring = tools.objloc(do)
				coordstring = str(cstring.ra)
				if cstring.dec.deg >= 0:
					coordstring += '+'+str(cstring.dec)
				if cstring.dec.deg < 0:
					coordstring += str(cstring.dec)

				if parallel:
					pool = Pool(processes=(cpu_count() - 1))
					for dk in imglist[do].keys():
						outname = coordstring+'_'+dk+'_img'
						drizzleparams['output'] = img_dir + outname #set output based on coord, filter
						pool.apply_async(astrodrizzle.AstroDrizzle, args = (imglist[do][dk]), kwds = drizzleparams)
					pool.close()
					pool.join()
				if not parallel:
					for dk in drizzlelist[do].keys():
						outname = coordstring+'_'+dk+'_img'
						drizzleparams['output'] = img_dir + outname #set output based on coord, filter
						astrodrizzle.AstroDrizzle(imglist[do][dk], **drizzleparams)

	if not finalonly:
		# clean up step to move all of the PSF files to the relevant directory
		# should grab all .pngs, .fits etc.
		if not os.path.exists(savedir):
			os.makedirs(savedir)

		os.system('mv %s*_drc* %s'%(img_dir, savedir)) # drizzled files
		os.system('mv %s*_drz* %s'%(img_dir, savedir)) # drizzled files
		os.system('mv %s*_mos* %s'%(img_dir, savedir)) # drizzled files

		os.system('mv %s*_psf* %s'%(img_dir, savedir)) # generated PSF models
		os.system('mv %s*.psf %s'%(img_dir, savedir))
		os.system('mv %s*_topsf* %s'%(img_dir, savedir)) # tweaked and drizzled PSF models

		## clean up other files generated in the process
		os.system('mv %s*.cat %s'%(img_dir, savedir))
		os.system('mv %s*_mask.fits %s'%(img_dir, savedir))
		os.system('mv ./*_sci1.fits %s'%(savedir))

		## clean up files generated in img drizzle
		os.system('mv %s*.cat %s'%(img_dir, savedir))
		os.system('mv %s*_staticMask.fits %s'%(img_dir, savedir))
		os.system('mv %s*_sci* %s'%(img_dir, savedir))
		os.system('mv %s*_mask* %s'%(img_dir, savedir))
		os.system('mv ./*_sci2.fits %s'%(savedir))
		os.system('mv %s*_wht.fits %s'%(img_dir, savedir))
		os.system('mv %s*_med.fits %s'%(img_dir, savedir))
		os.system('mv %s*_blt.fits %s'%(img_dir, savedir))
		os.system('mv %s*_crclean.fits %s'%(img_dir, savedir))
		os.system('mv %s*_crmask.fits %s'%(img_dir, savedir))


		if verbose:
			print('Moved PSF files to %s'%savedir)


	if finalonly:
		# clean up step to move all of the resampled files to the relevant directory
		if not os.path.exists(savedir):
			os.makedirs(savedir)

		os.system('mv %s*_drz* %s'%(img_dir, savedir)) #move files to preserve
		os.system('mv %s*_drc* %s'%(img_dir, savedir))
		os.system('mv %s*_mos* %s'%(img_dir, savedir))

		if verbose:
			print('Moved drizzled files to %s'%savedir)

		if os.path.exists(removedir):
			# raise warning if removedir exists; not an error, though since some people might create it for this purpose
			warnings.warn('%s already exists. This directory and its contents will be deleted.'%(removedir),
				Warning, stacklevel = 2)

		if not os.path.exists(removedir): #directory to remove excess files
			os.makedirs(removedir)

		os.system('mv %s*_psf* %s'%(img_dir, removedir)) # generated PSF models
		os.system('mv %s*.psf %s'%(img_dir, removedir))
		os.system('mv %s*_topsf* %s'%(img_dir, removedir))

		## clean up other files generated in the process
		os.system('mv %s*.cat %s'%(img_dir, removedir))
		os.system('mv %s*_mask.fits %s'%(img_dir, removedir))
		os.system('mv %s*sci1.fits %s'%(img_dir, removedir))

		## clean up files generated in img drizzle
		os.system('mv %s*.cat %s'%(img_dir, removedir))
		os.system('mv %s*_staticMask.fits %s'%(img_dir, removedir))
		os.system('mv %s*_sci* %s'%(img_dir, removedir))
		os.system('mv %s*sci2.fits %s'%(img_dir, removedir))
		os.system('mv %s*_wht.fits %s'%(img_dir, removedir))
		os.system('mv %s*_med.fits %s'%(img_dir, removedir))
		os.system('mv %s*_blt.fits %s'%(img_dir, removedir))
		os.system('mv %s*_crclean.fits %s'%(img_dir, removedir))
		os.system('mv %s*_crmask.fits %s'%(img_dir, removedir))

		os.system('rm -r %s'%(removedir))

		if verbose:
			print('Deleted intermediate products and removedir.')




	if out == 'asdf':
		# .asdf file read out in addition to .fits
		if savedir.split('/')[-1] != '':
			savedir += '/'

		sufs = ['drc', 'drz', 'mos']
		dout = np.concatenate((sorted(glob.glob(savedir+'*_drc.fits')), 
			sorted(glob.glob(savedir+'*_drz.fits')), sorted(glob.glob(savedir+'*_mos.fits'))))
		for di in dout:
			tools.to_asdf(di)

		if verbose:
			print('Generated ASDF output')

	if returnpsf:
		returndict = {}
		for o, do in enumerate(drizzlelist.keys()):
			if type(obj) == str:
				coordstring = str(skycoords.ra)
				if skycoords.dec.deg >= 0:
					coordstring += '+'+str(skycoords.dec)
				if skycoords.dec.deg < 0:
					coordstring += str(skycoords.dec)

			if type(obj) != str:
				coordstring = str(skycoords[o].ra)
				if skycoords[o].dec.deg >= 0:
					coordstring += '+'+str(skycoords[o].dec)
				if skycoords[o].dec.deg < 0:
					coordstring += str(skycoords[o].dec)

			returndict[do] = {}
			for dk in drizzlelist[do].keys():

				if savedir.split('/')[-1] != '':
					savedir += '/'

				if returnpsf == 'full':	
					dr_psf = fits.open(savedir+'%s_%s_psf_%s.fits'%(coordstring, dk, suff))
					returndict[do][dk] = dr_psf[1].data

				if returnpsf == 'crop':
					crop = tools.cutout(img = savedir+'%s_%s_psf_%s.fits'%(coordstring, dk, suff), 
									coords = tools.objloc(do), fov_pixel = cutout_fov, save = savecutout)
					returndict[do][dk] = crop

		return returndict



def jwst(img_dir, obj, inst, img_type = 'cal', camera = None, method = 'WebbPSF', usermethod = None, 
		savedir = 'psfs', drizzleimgs = False, objonly = True, pretweaked = False, usecrds = False, 
		keeporig = True, plot = False, verbose = False, parallel = False, out = 'fits',
		returnpsf = 'full', cutout_fov = 151, savecutout = True, finalonly = False, 
		removedir = 'toremove', tweakparams = {}, drizzleparams = {'allowed_memory':0.5}, **kwargs):
	"""
	Generate drizzled James Webb Space Telescope PSFs.

	Parameters:
		img_dir (str): Path to directory containing calibrated files for which model PSF will be generated.
				If using the tweakreg step, best to include a drizzled file, as well, which can be used as a reference.
		obj(str, arr-like): Name or coordinates of object of interest in HH:MM:DD DD:MM:SS or degree format.
		img_type (str): e.g, 'cal', 'calints', 'crf', 'crfints' -- specifies which file-type to include.
		inst (str): 'MIRI', 'NIRCAM', 'NIRISS'
		camera (str): 'Imaging', 'AMI' -- MUST BE SPECIFIED FOR NIRISS
		method (str): 'WebbPSF', 'STDPSF' (empirical), 'epsf' (empirical), 'PSFEx' (empirical) -- see spike.psfgen for details -- or 'USER';
				if 'USER', usermethod should be a function that generates, or path to a directory of user-generated, PSFs 
				named [imgprefix]_[coords]_[band]_psf.fits, e.g., imgprefix_23.31+30.12_F814W_psf.fits or 
				imgprefix_195.78-46.52_F555W_psf.fits. Note: the WebbPSF name is maintained here in lieu of STPSF to avoid
				confusion with the generation of empirical STDPSFs.
		usermethod (func or str): If method = 'USER', usermethod should be a function that generates, or path to a 
				directory of user-generated, PSFs named [imgprefix]_[coords]_[band]_psf.fits, e.g., 
				imgprefix_23.31+30.12_F814W_psf.fits or imgprefix_195.78-46.52_F555W_psf.fits, where the 
				imgprefix corresponds to the name of the relevant flt/flc/c0f/c1f/... files in the directory and the 
				headers are from the original images (see spike.tools.rewrite_fits, which can be used to this end).
		savedir (str): Where the PSF models and drizzled PSF will be saved. Defaults to 'psfs'.
		drizzleimgs (bool): If True, will drizzle the input images at the same time as creating a drizzled psf.
		objonly (bool): If True, only drizzles input images that cover the selected obj.
		pretweaked (bool): If True, skips tweak step to include fine WCS corrections.
		usecrds (bool): If True, use CRDS config settings as defaults. 
		keeporig (bool): If True (and pretweaked = False), create copy of img_dir before tweak.
		plot (bool): If True, saves .pngs of the model PSFs.
		verbose (bool): If True, prints progress messages.
		parallel (bool): If True, runs PSF generation in parallel.
		out (str): 'fits' or 'asdf'. Output for the drizzled PSF. If 'asdf', .asdf AND .fits are saved.
		returnpsf (str): 'full', 'crop', or None. If None, spike.psf.jwst does not return anything. If 'full' (default),
			returns the PSF in the full spatial context of the processed image. If 'crop', returns the region immediately
			around the PSF (size of cutout set by cutout_fov).
		cutout_fov (int): Side length in pixels of square cutout region centered on PSF. Used if returnpsf = 'crop'.
		savecutout (bool): If True, save a .fits file with the cutout region, including WCS. Only used if returnpsf = 'crop'.
		finalonly (bool): If True, only retains final drizzled/resampled data products in savedir and deletes intermediate products.
		removedir (str): Directory (**to be deleted**) that stores intermediate products for removal. Default is 'toremove'.
		tweakparams (dict): Dictionary of keyword arguments for drizzlepac.tweakreg. See the drizzlepac documentation
				for a full list. See here: https://jwst-pipeline.readthedocs.io/en/latest/jwst/tweakreg/README.html#step-arguments
		drizzleparams (dict): Dictionary of keyword arguments for drizzlepac.astrodrizzle. See the drizzlepac 
				documentation for a full list.
		**kwargs: Keyword arguments for PSF generation function.

	Returns:
		Generates model PSFs and drizzled PSF. (If drizzledimgs = True, also produces drizzled image from input files.)

		If returnpsf = 'full', will return each of the full drizzled PSF images in an object, filter indexed dict.
		If returnpsf = 'crop', will return a cutout region of the drizzled PSF images (around the PSF) in an obj, filt indexed dict.
	"""

	os.environ['CRDS_SERVER_URL']="https://jwst-crds.stsci.edu"

	if not usecrds:
		os.environ["STPIPE_DISABLE_CRDS_STEPPARS"] = 'True'

	from spike.jwstcal import resample_step
	from spike.jwstcal import tweakreg_tweakreg_step as tweakreg_step

	if img_dir[:-1] != '/':
		img_dir += '/' #force paths to work out

	if keeporig and not pretweaked:
		if not os.path.exists(img_dir+'_orig'):
			os.makedirs(img_dir+'_orig')
		os.system('cp -r '+img_dir+'*_'+img_type+'.fits '+'img_dir'+'_orig')
		if verbose:
			print('Made copy of '+img_dir)


	imgs = sorted(glob.glob(img_dir+'*'+img_type+'.fits'))

	imcam = inst.upper()

	genpsf = True
	if method.upper() not in ['WEBBPSF', 'STDPSF', 'EPSF', 'PSFEX', 'USER']:
		raise Exception('tool must be one of WEBBPSF, STDPSF, EPSF, PSFEX, USER')
	if method.upper() == 'WEBBPSF':
		psffunc = psfgen.jwpsf
	if method.upper() == 'STDPSF':
		psffunc = psfgen.stdpsf
	if method.upper() == 'EPSF':
		psffunc = psfgen.effpsf
	if method.upper() == 'PSFEX':
		psffunc = psfgen.psfex
	if method.upper() == 'USER':
		if type(usermethod) == str: #check if user input is path to directory
			genpsf = False
		if type(usermethod) != str: #or function
			psffunc = method

	filelist = {} # generate list of files to tweak -- by filter
	for fi in imgs:
		hdu = fits.open(fi)
		try: #get filter
			filt = hdu[0].header['FILTER']
		except:
			if hdu[0].header['FILTER1'].startswith('F'):
				filt = hdu[0].header['FILTER1']
			else:
				filt = hdu[0].header['FILTER2']
		if filt not in filelist.keys():
			filelist[filt] = []
		filelist[filt].append(fi)

	if not pretweaked:
		for fk in filelist.keys():
			filemodels = tweakreg_step.TweakRegStep(**tweakparams).call(filelist[fk], 
					output_dir = img_dir, save_results = True)

		imgs = sorted(glob.glob(img_dir+'*_tweakregstep.fits'))

	drizzlelist = {} #write file prefixes to drizzle per object per filter
	imglist = {} #write file names to drizzle per object per filter
	if genpsf: #generate model PSFs for each image + object
		if type(obj) == str: #check number of objects
			drizzlelist[obj] = {}
			imglist[obj] = {}
			skycoords = tools.objloc(obj)
			for i in imgs:
				pos = tools.checkpixloc(skycoords, i, inst, camera)

				coordstring = str(skycoords.ra)
				if skycoords.dec.deg >= 0:
					coordstring += '+'+str(skycoords.dec)
				if skycoords.dec.deg < 0:
					coordstring += str(skycoords.dec)

				modname = i.replace('%s.fits'%img_type, coordstring+'_%s'%pos[3]+'_topsf_%s.fits'%img_type)
				if np.isfinite(pos[0]): #confirm object falls onto image
					if pos[3] not in drizzlelist[obj].keys():
						drizzlelist[obj][pos[3]] = []
						imglist[obj][pos[3]] = []
					drizzlelist[obj][pos[3]].append(modname)
					imglist[obj][pos[3]].append(i)

					psffunc(skycoords, i, imcam, pos, plot, verbose, **kwargs)

		if type(obj) != str: #if multiple objects, option to parallelize 
			skycoords = [] #only open each FITS file once

			for o in obj:
				drizzlelist[o] = {}
				imglist[o] = {}
				skycoords.append(tools.objloc(o))
			
			for i in imgs:

				if parallel:
					if method.upper() == 'PSFEX':
						warnings.warn('Warning: Check your config and param files to ensure output files have unique names.', Warning, stacklevel = 2)
					pool = Pool(processes=(cpu_count() - 1))
					for j, coord in enumerate(skycoords):
						coordstring = str(sc.ra)
						if coord.dec.deg >= 0:
							coordstring += '+'+str(coord.dec)
						if coord.dec.deg < 0:
							coordstring += str(coord.dec)

						pos = tools.checkpixloc(coord, i, inst, camera)

						modname = i.replace('%s.fits'%img_type, coordstring+'_%s'%pos[3]+'_topsf_%s.fits'%img_type)
						if np.isfinite(p[0]): #confirm that object falls onto detector
							if pos[3] not in drizzlelist[obj[j]].keys():
								drizzlelist[obj[j]][pos[3]] = []
								imglist[obj[j]][pos[3]] = []
							drizzlelist[obj[j]][pos[3]].append(modname)
							imglist[obj[j]][pos[3]].append(i)

							pool.apply_async(psffunc, args = (coord, i, imcam, pos, plot, verbose), kwds = kwargs)
					pool.close()
					pool.join()

				if not parallel:
					for j, coord in enumerate(skycoords):
						pos = tools.checkpixloc(coord, i, inst, camera)

						coordstring = str(coord.ra)
						if coord.dec.deg >= 0:
							coordstring += '+'+str(coord.dec)
						if coord.dec.deg < 0:
							coordstring += str(coord.dec)

						modname = i.replace('%s.fits'%img_type, coordstring+'_%s'%pos[3]+'_topsf_%s.fits'%img_type)
						if np.isfinite(pos[0]): #confirm that object falls onto detector
							if pos[3] not in drizzlelist[obj[j]].keys():
								drizzlelist[obj[j]][pos[3]] = []
								imglist[obj[j]][pos[3]] = []
							drizzlelist[obj[j]][pos[3]].append(modname)
							imglist[obj[j]][pos[3]].append(i)

						psffunc(coord, i, imcam, pos, plot, verbose, **kwargs) 
					
	if not genpsf:
		userpsfs = sorted(glob.glob(usermethod))

		for up in userpsfs:
			## JWST names in program_program2_exp_cal.fits form

			im, im2, im3, imtype, obj, filt, _ = up.split('_')

			img = imgdir+'%s_%s_%s_%s.fits'%(im, im2, im3, imtype)
			coord = tools.objloc(obj)
			pos = tools.checkpixloc(coords)

			psfmodel = fits.open(up)[1].data

			tools.rewrite_fits(psfmodel, img, coord, imcam, pos, method = 'USER')

			coordstring = str(coord.ra)
			if coord.dec.deg >= 0:
				coordstring += '+'+str(coord.dec)
			if coord.dec.deg < 0:
				coordstring += str(coord.dec)

			modname = img.replace('%s.fits'%imtype, coordstring+'_%s'%pos[3]+'_topsf_%s.fits'%imtype)

			if obj not in drizzlelist.keys():
				drizzlelist[obj] = {}
				imglist[obj] = {}
			if filt not in drizzlelist[obj].keys():
				drizzlelist[obj][filt] = []
				imglist[obj][filt] = []
			drizzlelist[obj][filt].append(modname)
			imglist[obj][filt].append(img)

	#####################################################################
	for do in drizzlelist.keys():
		if parallel:
			pool = Pool(processes=(cpu_count() - 1))
			for dk in drizzlelist[do].keys():

				shortdec, shortra = [cc.split('.')[0] for cc in do.split(' ')]

				if ':' not in shortra:
					if int(shortra) > 0:
						shortra = "+"+shortra

				resampname = shortdec+shortra+'_'+dk
				resampname = resampname.replace(':', '').replace(' ', '')

				resamp = resample_step.ResampleStep(**drizzleparams)
				resampkwds = {'input_models': drizzlelist[do][dk], 
							  'output_file': resampname,
							  'output_dir':img_dir, 
							  'save_results':True}
				pool.apply_async(resamp.call, kwds = resampkwds)
			pool.close()
			pool.join()
		if not parallel:
			for dk in drizzlelist[do].keys():
				shortdec, shortra = [cc.split('.')[0] for cc in do.split(' ')]

				if ':' not in shortra:
					if int(shortra) > 0:
						shortra = "+"+shortra

				resampname = shortdec+shortra+'_'+dk
				resampname = resampname.replace(':', '').replace(' ', '')

				resamp = resample_step.ResampleStep(**drizzleparams).call(drizzlelist[do][dk],
					output_file = resampname, 
					output_dir = img_dir, save_results = True)


	
	if drizzleimgs: # useful for processing all images + PSFs simultaneously
		if not objonly:
			for fk in filelist.keys():
				resamp = resample_step.ResampleStep(**drizzleparams).call(filelist[fk],
						output_file = '%s_img'%fk, output_dir = img_dir, save_results = True)
		if objonly:
			if parallel:
				pool = Pool(processes=(cpu_count() - 1))
				for dk in imglist[do].keys():

					shortdec, shortra = [cc.split('.')[0] for cc in do.split(' ')]

					if ':' not in shortra:
						if int(shortra) > 0:
							shortra = "+"+shortra

					resampname = shortdec+shortra+'_'+dk+'_img'
					resampname = resampname.replace(':', '').replace(' ', '')

					resamp = resample_step.ResampleStep(**drizzleparams)
					resampkwds = {'input_models': imglist[do][dk], 
								  'output_file': resampname,
								  'output_dir':img_dir, 
								  'save_results':True}
					pool.apply_async(resamp.call, kwds = resampkwds)
				pool.close()
				pool.join()
			if not parallel:
				for dk in imglist[do].keys():
					shortdec, shortra = [cc.split('.')[0] for cc in do.split(' ')]

					if ':' not in shortra:
						if int(shortra) > 0:
							shortra = "+"+shortra

					resampname = shortdec+shortra+'_'+dk+'_img'
					resampname = resampname.replace(':', '').replace(' ', '')

					resamp = resample_step.ResampleStep(**drizzleparams).call(imglist[do][dk],
						output_file = resampname, 
						output_dir = img_dir, save_results = True)


	#####################################################################
	suff = "resamplestep"

	if not finalonly:
		# clean up step to move all of the PSF files to the relevant directory
		# should grab all .pngs, .fits etc.
		if not os.path.exists(savedir):
			os.makedirs(savedir)
		os.system('mv %s*_%s* %s'%(img_dir, suff, savedir)) # generated PSF models
		os.system('mv %s*_psf %s'%(img_dir, savedir))
		os.system('mv %s*.psf %s'%(img_dir, savedir))
		os.system('mv %s*_topsf* %s'%(img_dir, savedir)) # tweaked and drizzled PSF models

		## clean up other files generated in the process
		os.system('mv %s*.cat %s'%(img_dir, savedir))
		os.system('mv %s*_mask.fits %s'%(img_dir, savedir))
		# retain tweaked version in working directory for re-runs etc.
		# os.system('mv %s*_tweakregstep.fits %s'%(img_dir, savedir))

		if verbose:
			print('Moved PSF files to %s'%savedir)

	if finalonly:
		# clean up step to move all of the resampled files to the relevant directory
		if not os.path.exists(savedir):
			os.makedirs(savedir)

		os.system('mv %s*_resamplestep* %s'%(img_dir, savedir)) #move files to preserve
		os.system('mv %s*_%s* %s'%(img_dir, suff, savedir)) # generic name for flexibility

		if verbose:
			print('Moved resampled files to %s'%savedir)


		if os.path.exists(removedir):
			# raise warning if removedir exists; not an error, though since some people might create it for this purpose
			warnings.warn('%s already exists. This directory and its contents will be deleted.'%(removedir),
				Warning, stacklevel = 2)

		if not os.path.exists(removedir): #directory to remove excess files
			os.makedirs(removedir)

		os.system('mv %s*_psf %s'%(img_dir, removedir))
		os.system('mv %s*.psf %s'%(img_dir, removedir))
		os.system('mv %s*_topsf* %s'%(img_dir, removedir))

		## clean up other files generated in the process
		os.system('mv %s*.cat %s'%(img_dir, removedir))
		os.system('mv %s*_mask.fits %s'%(img_dir, removedir))

		os.system('rm -r %s'%(removedir))

		if verbose:
			print('Deleted intermediate products and removedir.')



	if out == 'asdf':
		# .asdf file read out in addition to .fits
		# defining suffix from resample output
		if savedir.split('/')[-1] != '':
			savedir += '/'

		dout = sorted(glob.glob(savedir+'*_%s.fits'%suff)) 
		for di in dout:
			tools.to_asdf(di)
		if verbose:
			print('Generated ASDF output')

	if returnpsf:
		returndict = {}
		for do in drizzlelist.keys():
			returndict[do] = {}
			for dk in drizzlelist[do].keys():

				shortdec, shortra = [cc.split('.')[0] for cc in do.split(' ')]
				if ':' not in shortra:
					if int(shortra) > 0:
						shortra = "+"+shortra

				resampname = shortdec+shortra+'_'+dk
				resampname = resampname.replace(':', '').replace(' ', '')

				if savedir.split('/')[-1] != '':
					savedir += '/'

				if returnpsf == 'full':	
					dr_psf = fits.open(savedir+'%s_%s.fits'%(resampname ,suff))
					returndict[do][dk] = dr_psf[1].data

				if returnpsf == 'crop':
					crop = tools.cutout(img = savedir+'%s_%s.fits'%(resampname ,suff), 
									coords = tools.objloc(do), fov_pixel = cutout_fov, save = savecutout)
					returndict[do][dk] = crop

		return returndict


def roman(img_dir, obj, inst, img_type= 'cal', file_type = 'fits', camera = None, method = 'WebbPSF', 
		usermethod = None, savedir = 'psfs', drizzleimgs = False, objonly = True, pretweaked = False, 
		usecrds = False, keeporig = True, plot = False, verbose = False, parallel = False, 
		out = 'fits', returnpsf = 'full', cutout_fov = 151, savecutout = True, finalonly = False,
		removedir = 'toremove', tweakparams = {}, drizzleparams = {}, **kwargs):
	"""
	Generate drizzled Roman Space Telescope PSFs.

	Parameters:
		img_dir (str): Path to directory containing calibrated files for which model PSF will be generated.
				If using the tweakreg step, best to include a drizzled file, as well, which can be used as a reference.
		obj(str, arr-like): Name or coordinates of object of interest in HH:MM:DD DD:MM:SS or degree format.
		img_type (str): e.g, 'cal' -- specifies which file-type to include.
		file_type (str): 'fits' or 'asdf' -- format to use for reading and manipulating data files.
		inst (str): 'WFI', 'CGI'
		camera (str): None
		method (str): 'WebbPSF', 'epsf' (empirical), 'PSFEx' (empirical) -- see spike.psfgen for details -- or 'USER';
				if 'USER', usermethod should be a function that generates, or path to a directory of user-generated, PSFs 
				named [imgprefix]_[coords]_[band]_psf.fits, e.g., imgprefix_23.31+30.12_F814W_psf.fits or 
				imgprefix_195.78-46.52_F555W_psf.fits. Note: the WebbPSF name is maintained here in lieu of STPSF to avoid
				confusion with the generation of empirical STDPSFs.
		usermethod (func or str): If method = 'USER', usermethod should be a function that generates, or path to a 
				directory of user-generated, PSFs named [imgprefix]_[coords]_[band]_psf.fits, e.g., 
				imgprefix_23.31+30.12_F814W_psf.fits or imgprefix_195.78-46.52_F555W_psf.fits, where the 
				imgprefix corresponds to the name of the relevant cal/calints... files in the directory and the 
				headers are from the original images (see spike.tools.rewrite_fits, which can be used to this end).
		savedir (str): Where the PSF models and drizzled PSF will be saved. Defaults to 'psfs'.
		drizzleimgs (bool): If True, will drizzle the input images at the same time as creating a drizzled psf.
		objonly (bool): If True, only drizzles input images that cover the selected obj.
		pretweaked (bool): If True, skips tweak step to include fine WCS corrections.
		usecrds (bool): If True, use CRDS config settings as defaults. 
		keeporig (bool): If True (and pretweaked = False), create copy of img_dir before tweak.
		plot (bool): If True, saves .pngs of the model PSFs.
		verbose (bool): If True, prints progress messages.
		parallel (bool): If True, runs PSF generation in parallel.
		out (str): 'fits' or 'asdf'. Output for the drizzled PSF. If 'asdf', .asdf AND .fits are saved.
		returnpsf (str): 'full', 'crop', or None. If None, spike.psf.roman does not return anything. If 'full' (default),
			returns the PSF in the full spatial context of the processed image. If 'crop', returns the region immediately
			around the PSF (size of cutout set by cutout_fov).
		cutout_fov (int): Side length in pixels of square cutout region centered on PSF. Used if returnpsf = 'crop'.
		savecutout (bool): If True, save a .fits file with the cutout region, including WCS.
		finalonly (bool): If True, only retains final drizzled/resampled data products in savedir and deletes intermediate products.
		removedir (str): Directory (**to be deleted**) that stores intermediate products for removal. Default is 'toremove'.
		tweakparams (dict): Dictionary of keyword arguments for drizzlepac.tweakreg. See the drizzlepac documentation
				for a full list.
		drizzleparams (dict): Dictionary of keyword arguments for drizzlepac.astrodrizzle. See the drizzlepac 
				documentation for a full list.
		**kwargs: Keyword arguments for PSF generation function.

	Returns:
		Generates model PSFs and drizzled PSF. (If drizzledimgs = True, also produces drizzled image from input files.)

		If returnpsf = 'full', will return each of the full drizzled PSF images in an object, filter indexed dict.
		If returnpsf = 'crop', will return a cutout region of the drizzled PSF images (around the PSF) in an obj, filt indexed dict.
	"""
	os.environ['CRDS_SERVER_URL']="https://roman-crds.stsci.edu"

	if not usecrds:
		os.environ["STPIPE_DISABLE_CRDS_STEPPARS"] = 'True'

	from spike.romancal import tweakreg_step, resample_step

	if img_dir[:-1] != '/':
		img_dir += '/' #force paths to work out

	if keeporig and not pretweaked:
		if not os.path.exists(img_dir+'_orig'):
			os.makedirs(img_dir+'_orig')
		os.system('cp -r '+img_dir+'*_'+img_type+'.fits '+'img_dir'+'_orig')
		if verbose:
			print('Made copy of '+img_dir)


	imgs = sorted(glob.glob(img_dir+'*'+img_type+'.fits'))

	imcam = inst.upper()

	genpsf = True
	if method.upper() not in ['WEBBPSF', 'EPSF', 'PSFEX', 'USER']:
		raise Exception('tool must be one of WEBBPSF, EPSF, PSFEX, USER')
	if method.upper() == 'WEBBPSF':
		psffunc = psfgen.jwpsf
	if method.upper() == 'EPSF':
		psffunc = psfgen.effpsf
	if method.upper() == 'PSFEX':
		psffunc = psfgen.psfex
	if method.upper() == 'USER':
		if type(usermethod) == str: #check if user input is path to directory
			genpsf = False
		if type(usermethod) != str: #or function
			psffunc = method

	filelist = {} # generate list of files to tweak -- by filter
	for fi in imgs:
		hdu = fits.open(fi)
		try: #get filter
			filt = hdu[0].header['FILTER']
		except:
			if hdu[0].header['FILTER1'].startswith('F'):
				filt = hdu[0].header['FILTER1']
			else:
				filt = hdu[0].header['FILTER2']
		if filt not in filelist.keys():
			filelist[filt] = []
		filelist[filt].append(fi)

	if not pretweaked:
		for fk in filelist.keys():
			filemodels = tweakreg_step.TweakRegStep(**tweakparams).call(filelist[fk], 
					output_dir = img_dir, save_results = True)

		imgs = sorted(glob.glob(img_dir+'*_tweakregstep.fits'))

	drizzlelist = {} #write file prefixes to drizzle per object per filter
	imglist = {}
	if genpsf: #generate model PSFs for each image + object
		if type(obj) == str: #check number of objects
			drizzlelist[obj] = {}
			imglist[obj] = {}
			skycoords = tools.objloc(obj)
			for i in imgs:
				pos = tools.checkpixloc(skycoords, i, inst, camera)
				coordstring = str(skycoords.ra)
				if skycoords.dec.deg >= 0:
					coordstring += '+'+str(skycoords.dec)
				if skycoords.dec.deg < 0:
					coordstring += str(skycoords.dec)

				modname = i.replace('%s.fits'%img_type, coordstring+'_%s'%pos[3]+'_topsf_%s.fits'%img_type)
				if np.isfinite(pos[0]): #confirm object falls onto image
					if pos[3] not in drizzlelist[obj].keys():
						drizzlelist[obj][pos[3]] = []
						imglist[obj][pos[3]] = []
					drizzlelist[obj][pos[3]].append(modname)
					imglist[obj][pos[3]].append(i)

					psffunc(skycoords, i, imcam, pos, plot, verbose, **kwargs)

		if type(obj) != str: #if multiple objects, option to parallelize 
			skycoords = [] #only open each FITS file once

			for o in obj:
				drizzlelist[o] = {}
				imglist[o] = {}
				skycoords.append(tools.objloc(o))
			
			for i in imgs:

				pos = tools.checkpixloc(skycoords, i, inst, camera)

				if parallel:
					if method.upper() == 'PSFEX':
						warnings.warn('Warning: Check your config and param files to ensure output files have unique names.', Warning, stacklevel = 2)
					pool = Pool(processes=(cpu_count() - 1))
					for j, p in enumerate(pos):
						coordstring = str(skycoords[j].ra)
						if skycoords[j].dec.deg >= 0:
							coordstring += '+'+str(skycoords[j].dec)
						if skycoords[j].dec.deg < 0:
							coordstring += str(skycoords[j].dec)
							
						modname = i.replace('%s.fits'%img_type, coordstring+'_%s'%pos[3]+'_topsf_%s.fits'%img_type)
						if np.isfinite(p[0]): #confirm that object falls onto detector
							if p[3] not in drizzlelist[obj[j]].keys():
								drizzlelist[obj[j]][p[3]] = []
								imglist[obj[j]][p[3]] = []
							drizzlelist[obj[j]][p[3]].append(modname)
							imglist[obj[j]][p[3]].append(i)

							pool.apply_async(psffunc, args = (skycoords[j], i, imcam, p, plot, verbose), kwds = kwargs)
					pool.close()
					pool.join()
				if not parallel:
					for j, coord in enumerate(skycoords):
						pos = tools.checkpixloc(coord, i, inst, camera)

						coordstring = str(coord.ra)
						if coord.dec.deg >= 0:
							coordstring += '+'+str(coord.dec)
						if coord.dec.deg < 0:
							coordstring += str(coord.dec)

						modname = i.replace('%s.fits'%img_type, coordstring+'_%s'%pos[3]+'_topsf_%s.fits'%img_type)
						if np.isfinite(pos[0]): #confirm that object falls onto detector
							if pos[3] not in drizzlelist[obj[j]].keys():
								drizzlelist[obj[j]][pos[3]] = []
								imglist[obj[j]][pos[3]] = []
							drizzlelist[obj[j]][pos[3]].append(modname)
							imglist[obj[j]][pos[3]].append(i)

						psffunc(coord, i, imcam, pos, plot, verbose, **kwargs) 
					
	if not genpsf:
		userpsfs = sorted(glob.glob(usermethod))

		for up in userpsfs:
			## Roman names in dc2_filt_NNNNN_det.fits form
			# based on simulations

			im, imf, imn, imd, imtype, obj, filt, _ = up.split('_')

			img = imgdir+'%s_%s_%s_%s_%s.fits'%(im, imf, imn, imd, imtype)
			coord = tools.objloc(obj)
			pos = tools.checkpixloc(coords)

			psfmodel = fits.open(up)[1].data

			tools.rewrite_fits(psfmodel, img, coord, imcam, pos, method = 'USER')

			coordstring = str(coord.ra)
			if coord.dec.deg >= 0:
				coordstring += '+'+str(coord.dec)
			if coord.dec.deg < 0:
				coordstring += str(coord.dec)

			modname = img.replace('%s.fits'%imtype, coordstring+'_%s'%pos[3]+'_topsf_%s.fits'%imtype)

			if obj not in drizzlelist.keys():
				drizzlelist[obj] = {}
				imglist[obj] = {}
			if filt not in drizzlelist[obj].keys():
				drizzlelist[obj][filt] = []
				imglist[obj][filt] = []
			drizzlelist[obj][filt].append(modname)
			imglist[obj][filt].append(img)

	#####################################################################
	for do in drizzlelist.keys():
		if parallel:
			pool = Pool(processes=(cpu_count() - 1))
			for dk in drizzlelist[do].keys():
				shortdec, shortra = [cc.split('.')[0] for cc in do.split(' ')]

				if ':' not in shortra:
					if int(shortra) > 0:
						shortra = "+"+shortra

				resampname = shortdec+shortra+'_'+dk
				resampname = resampname.replace(':', '').replace(' ', '')

				resamp = resample_step.ResampleStep(**drizzleparams)
				resampkwds = {'input_models': drizzlelist[do][dk], 
							  'output_file': resampname,
							  'output_dir':img_dir, 
							  'save_results':True}
				pool.apply_async(resamp.call, kwds = resampkwds)
			pool.close()
			pool.join()
		if not parallel:
			for dk in drizzlelist[do].keys():
				shortdec, shortra = [cc.split('.')[0] for cc in do.split(' ')]

				if ':' not in shortra:
					if int(shortra) > 0:
						shortra = "+"+shortra

				resampname = shortdec+shortra+'_'+dk
				resampname = resampname.replace(':', '').replace(' ', '')

				resamp = resample_step.ResampleStep(**drizzleparams).call(drizzlelist[do][dk],
					output_file = resampname, output_dir = img_dir, save_results = True)


	
	if drizzleimgs: # useful for processing all images + PSFs simultaneously
		if not objonly:
			for fk in filelist.keys():
				resamp = resample_step.ResampleStep(**drizzleparams).call(filelist[fk],
						output_file = '%s_img'%fk, output_dir = img_dir, save_results = True)
		if objonly:
			if parallel:
				pool = Pool(processes=(cpu_count() - 1))
				for dk in imglist[do].keys():
					shortdec, shortra = [cc.split('.')[0] for cc in do.split(' ')]

					if ':' not in shortra:
						if int(shortra) > 0:
							shortra = "+"+shortra

					resampname = shortdec+shortra+'_'+dk+'_img'
					resampname = resampname.replace(':', '').replace(' ', '')

					resamp = resample_step.ResampleStep(**drizzleparams)
					resampkwds = {'input_models': imglist[do][dk], 
								  'output_file': resampname,
								  'output_dir':img_dir, 
								  'save_results':True}
					pool.apply_async(resamp.call, kwds = resampkwds)
				pool.close()
				pool.join()
			if not parallel:
				for dk in imglist[do].keys():
					shortdec, shortra = [cc.split('.')[0] for cc in do.split(' ')]

					if ':' not in shortra:
						if int(shortra) > 0:
							shortra = "+"+shortra

					resampname = shortdec+shortra+'_'+dk+'_img'
					resampname = resampname.replace(':', '').replace(' ', '')

					resamp = resample_step.ResampleStep(**drizzleparams).call(imglist[do][dk],
						output_file = resampname, output_dir = img_dir, save_results = True)
	#####################################################################
	suff = "resamplestep"

	if not finalonly:
		# clean up step to move all of the PSF files to the relevant directory
		# should grab all .pngs, .fits etc.
		if not os.path.exists(savedir):
			os.makedirs(savedir)
		os.system('mv %s*_%s* %s'%(img_dir, suff, savedir)) # generated PSF models
		os.system('mv %s*_psf %s'%(img_dir, savedir))
		os.system('mv %s*.psf %s'%(img_dir, savedir))
		os.system('mv %s*_topsf* %s'%(img_dir, savedir)) # tweaked and drizzled PSF models

		## clean up other files generated in the process
		os.system('mv %s*.cat %s'%(img_dir, savedir))
		os.system('mv %s*_mask.fits %s'%(img_dir, savedir))
		# retain tweaked version in working directory for re-runs etc.
		# os.system('mv %s*_tweakregstep.fits %s'%(img_dir, savedir))

		if verbose:
			print('Moved PSF files to %s'%savedir)

	if finalonly:
		# clean up step to move all of the resampled files to the relevant directory
		if not os.path.exists(savedir):
			os.makedirs(savedir)

		os.system('mv %s*_resamplestep* %s'%(img_dir, savedir)) #move files to preserve
		os.system('mv %s*_%s* %s'%(img_dir, suff, savedir)) # generic name for flexibility

		if verbose:
			print('Moved resampled files to %s'%savedir)


		if os.path.exists(removedir):
			# raise warning if removedir exists; not an error, though since some people might create it for this purpose
			warnings.warn('%s already exists. This directory and its contents will be deleted.'%(removedir),
				Warning, stacklevel = 2)

		if not os.path.exists(removedir): #directory to remove excess files
			os.makedirs(removedir)

		os.system('mv %s*_psf %s'%(img_dir, removedir))
		os.system('mv %s*.psf %s'%(img_dir, removedir))
		os.system('mv %s*_topsf* %s'%(img_dir, removedir))

		## clean up other files generated in the process
		os.system('mv %s*.cat %s'%(img_dir, removedir))
		os.system('mv %s*_mask.fits %s'%(img_dir, removedir))

		os.system('rm -r %s'%(removedir))

		if verbose:
			print('Deleted intermediate products and removedir.')


	if out == 'asdf':
		# .asdf file read out in addition to .fits
		# defining suffix from resample output
		if savedir.split('/')[-1] != '':
			savedir += '/'

		dout = sorted(glob.glob(savedir+'*_%s.fits'%s)) 
		for di in dout:
			tools.to_asdf(di)


	if returnpsf:
		returndict = {}
		for do in drizzlelist.keys():
			returndict[do] = {}
			for dk in drizzlelist[do].keys():

				shortdec, shortra = [cc.split('.')[0] for cc in do.split(' ')]
				if ':' not in shortra:
					if int(shortra) > 0:
						shortra = "+"+shortra

				resampname = shortdec+shortra+'_'+dk
				resampname = resampname.replace(':', '').replace(' ', '')

				if savedir.split('/')[-1] != '':
					savedir += '/'

				if returnpsf == 'full':	
					dr_psf = fits.open(savedir+'%s_%s.fits'%(resampname, suff))
					returndict[do][dk] = dr_psf[1].data

				if returnpsf == 'crop':
					crop = tools.cutout(img = savedir+'%s_%s.fits'%(resampname, suff), 
									coords = tools.objloc(do), fov_pixel = cutout_fov, save = savecutout)
					returndict[do][dk] = crop

		return returndict


from astropy.nddata import NDData
from astropy.table import Table
import matplotlib.pyplot as plot
import os
from photutils.detection import DAOStarFinder, IRAFStarFinder
from photutils.psf import extract_stars, EPSFBuilder, GriddedPSFModel
from astropy.stats import sigma_clipped_stats
import pkg_resources
from spike import tools
import subprocess
import warnings
import webbpsf

def warning_on_one_line(message, category, filename, lineno, file=None, line=None):
	return '%s:%s: %s: %s\n' % (filename, lineno, category.__name__, message)

warnings.formatwarning = warning_on_one_line

CONFIG_PATH = pkg_resources.resource_filename('spike', 'configs/')

tinyparams = {}
tinyparams['imcam'] = {'WFPC1/WFC':1, 'WFPC1/PC':2, 'FOC/f48':3, 'FOC/f96':4, 
'WFPC2/WFC':5, 'WFPC2/PC':6, 'FOC/f48-COSTAR':7, 'FOC/f96-COSTAR':8, 'NICMOS/NIC1-precool':9,
'NICMOS/NIC2-precool':10, 'NICMOS/NIC3-precool':11, 'STIS/CCD':12, 'STIS/NUV':13, 'STIS/FUV':14,
'ACS/WFC':15, 'ACS/HRC':16, 'ACS/HRC-offspot':17, 'ACS/SBC':18, 'NICMOS/NIC1':19, 
'NICMOS/NIC2':20, 'NICMOS/NIC3':21, 'WFC3/UVIS':22, 'WFC3/IR':23}
# listing all options here, though not all are explicitly included in the spike code
tinyparams['specparam'] = {'O5':1, 'O8F':2, 'O6':3, 'B1V':4, 'B3V':5, 'B6V':6, 'A05':7, 'A5V':8, 
'F6V':9, 'F8V':10, 'G2V':11, 'G5V':12, 'G8V':13, 'K4V':14, 'K7V':15, 'M1.5V':16, 'M3V':17}

try:
	TINY_PATH = os.environ['TINYTIM']
except:
	TINY_PATH = None


stdpsf_jwdet = {'NRCA1':1, 'NRCA2':2, 'NRCA3':3, 'NRCA4':4, 
'NRCB1':5, 'NRCB2':6, 'NRCB3':7, 'NRCB7':8} #for STDPSFs

plate_scale = {'ACS/WFC':0.05, 'ACS/HRC':0.025 , 'WFC3/IR':0.13, 'WFC3/UVIS':0.039, 'WFPC_wf':0.1016 , 
'WFPC_pc':0.0439, 'WFPC1_wf':0.1016, 'WFPC1_pc':0.0439, 'WFPC2_wf':0.1, 'WFPC2_pc':0.046, 
'NIRCAM_long':0.063, 'NIRCAM_short':0.031, 'MIRI':0.11, 'NIRISS/Imaging':0.066, 
'WFI':0.11, 'CGI':0.0218} #arseconds/pixel -- some are averaged across filter/position
# including both WFPC1 and WFPC so that either name can be used

##########
# * * * *
##########


def tinypsf(coords, img, imcam, pos, plot = False, verbose = False, writeto = True,
	ebmv = None, av = None, wmag = None,
	jitter = None, major = None, minor = None, angle = None,
	specchoice = 'blackbody', listchoice = 'G5V', temp = 6000., 
	specalpha = 1., specbeta = 1., fov_arcsec = 6., despace = 0.):
	"""
	Generate HST PSFs using TinyTim.
	All of the options from TinyTim are easily available here *except* custom filters
	and subsampling, as they complicate use with spike. If you would like a subsampled
	Tiny Tim PSF model, please use spike.psfgen.tinygillispsf() instead.

	Parameters:
		coords (astropy skycoord object): Coordinates of object of interest or list of skycoord objects.
		img (str): Path to image for which PSF is generated.
		imcam (str): Specification of instrument/camera used to capture the images (e.g., 'ACS/WFC', 'WFC3/IR', 'WFPC', 'WFPC2').
			For 'WFPC' and 'WFPC2', the camera is selecte by-chip and should not be specified here.
		pos (list): Location of object of interest (spatial and spectral).[X, Y, chip, filter]
		plot (bool): If True, saves .pngs of the model PSFs.
		verbose (bool): If True, prints progress messages.
		writeto (bool): If True, will write 2D model PSF (differentiated with '_topsf' 
			suffix) and will amend relevant image WCS information/remove extraneous extensions.
			This is in addition to the 2D PSF model saved by TinyTim.
		ebmv (float):
		av (float):
		wmag (float):
		jitter (float): Symmetric jitter in mas.
		major (float): Axisymmetric major axis jitter in mas.
		minor (float): Axisymmetric minor axis jitter in mas.
		angle (float): Angle of offset for axisymmetric jitter.
		specchoice (str): 'list', 'blackbody', 'plaw_nu', 'plaw_lam' -- if 'list', must also specify
			listchoice; if 'blackbody', must also specify temp; if 'plaw_nu', must also specify specalpha;
			and if 'plaw_lam', must also specify specbeta.
		listchoice (str): One of 'O5', 'O8F', 'O6', 'B1V', 'B3V', 'B6V', 'A0V', 'A5V', 'F6V', 'F8V',
			'G2V', 'G5V', 'G8V', 'K4V', 'K7V', 'M1.5V', 'M3V'
		temp (float): Temperature of blackbody spectrum in K.
		specalpha (float): Spectral index alpha for F(nu)~nu^alpha.
		specbeta (float): Spectral index alpha for F(lambda)~lambda^beta.
		fov_arcsec (float): Diameter of model PSF image in arcsec.
		despace (float): Focus, secondary mirror despace in micron. Scaled by 0.011 and added to
			the 4th Zernike polynomial.

	Returns:
		TinyTim model PSF
	"""
	if not TINY_PATH:
		# this is a warning and not an error on the off chance that the TinyTim executables are 
		# in the working directory
		warnings.warn('Tiny Tim is not in your path. Make sure that it is installed -- https://github.com/spacetelescope/tinytim/releases/tag/7.5 -- and your TINYTIM environment variable is set or select a different PSF generation mode.', Warning, stacklevel = 2)

	tiny1 = TINY_PATH+'/tiny1 tiny.param'

	if ebmv and av:
		warnings.warn("Only one of ebmv and Av can be specified. Proceeding using only ebmv.", Warning, stacklevel = 2)
		tiny1 += ' ebmv='+str(ebmv)
	
	if None in [embv, av]:
		if embv:
			tiny1 += ' ebmv='+str(ebmv)

		if av:
			tiny1 += ' av='+str(av)

	if wmag:
		tiny1 += ' wmag'+str(wmag)

	if jitter:
		tiny1 += ' jitter='+str(jitter)

	if major and minor and angle:
		tiny1 += ' major=%s minor=%s angle=%s'%(str(major), str(minor), str(angle))

	if None in [major, minor, angle]:
		warnings.warn('All of major, minor, and angle must be specified to be applied. Proceeding with no elliptical jitter.', Warning, stacklevel = 2)

	if specchoice == 'list':
		spec = 1
		specparam = tinyparams['specparam'][listchoice]

	if specchoice == 'blackbody':
		spec = 2
		specparam = temp

	if specchoice == 'plaw_fnu':
		spec = 3
		specparam = specalpha

	if specchoice == 'plaw_flam':
		spec = 4
		specparam = specbeta

	coordstring = str(coords.ra)
	if coords.dec.deg > 0:
		coordstring += '+'+str(coords.dec)
	if coords.dec.deg >= 0:
		coordstring += str(coords.dec)

	modname = img.replace('.fits', coordstring+'_%s'%pos[3]+'_psf')

	if imcam in ['ACS/WFC', 'WFC3/UVIS']:
		command_list = [tinyparams['imcam'][imcam], pos[2], '%i %i'%(pos[0], pos[1]), 
		pos[3], spec, specparam, fov_arcsec, despace, modname]
	if imcam in ['ACS/HRC', 'WFC3/IR']:
		command_list = [16, '%i %i'%(pos[0], pos[1]), pos[3], 
		spec, specparam, fov_arcsec, despace, modname]
	if imcam in ['WFPC1', 'WFPC']:
		if pos[2] <= 4:
			imcam = 'WFPC/WFC'
		if pos[2] >= 5:
			imcam = 'WFPC/PC'
		imfits = fits.open(img)
		yyyy, mm, dd = imfits[0].header['DATE'].split('T')[0].split('-')
		command_list = [tinyparams['imcam'][imcam], pos[2], '%i %i'%(pos[0], pos[1]), 
		'%i %i %i'%(dd, mm, yyyy), pos[3], spec, specparam, fov_arcsec, 'N', despace, modname]
	if (imcam == 'WFPC2') and (pos[2] == 1):
		imcam = 'WFPC2/PC'
		command_list = [tinyparams['imcam'][imcam], '%i %i'%(pos[0], pos[1]), 
		pos[3], spec, specparam, fov_arcsec, 'N', despace, modname]
	if (imcam == 'WFPC2') and (pos[2] >= 2):
		imcam = 'WFPC2/WFC'
		command_list = [tinyparams['imcam'][imcam], pos[2], '%i %i'%(pos[0], pos[1]), 
		pos[3], spec, specparam, fov_arcsec, 'N', despace, modname]



	tiny = subprocess.Popen(tiny1, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
	newline = os.linesep

	tiny.communicate(newline.join(command_list).encode())

	
	os.system(TINY_PATH+'/tiny2 tiny.param')
	if verbose:
		print("Completed PSF modeling.")

	if imcam in ['ACS/WFC', 'ACS/HRC']: 
		os.system(TINY_PATH+'/tiny3 tiny.param')
		if verbose:
			print("Completed geometric distortion correction.")

	# deal with NICMOS and STIS -- will add later
	# inclined to include NICMOS but not STIS
	# NICMOS has time complication since the cryo-cooler etc. matter
	# set date of change over at April 3, 2002: https://ui.adsabs.harvard.edu/abs/2008AIPC..985..799S/abstract

	if imcam not in  ['ACS/WFC', 'ACS/HRC']:
		psfmodel = fits.open(modname+'00_psf.fits')[0].data

	if imcam in ['ACS/WFC', 'ACS/HRC']:
		psfmodel = fits.open(modname+'00.fits')[0].data


	if plot:
		fig= plt.figure(figsize = (5, 5))
		plt.imshow(psfmodel, origin = 'lower', cmap = 'Greys_r')
		plt.colorbar()
		fig.savefig(modname+'.png', bbox_inches = 'tight', dpi = 100)

		if verbose:
			print('PSF model image written to %s.png'%(modname))

	if writeto:
		rewrite_fits(psfmodel, coords, img, imcam, pos, method = 'TinyTim')


	return psfmodel



def tinygillispsf(coords, img, imcam, pos, plot = False, keep = False, verbose = False, 
	writeto = True, specchoice = 'blackbody', listchoice = 'G5V', temp = 6000., specalpha = 1., 
	specbeta = 1., fov_arcsec = 6., despace = 0., sample = 1., linearfit = False, regrid = True):
	"""
	Generate HST PSFs using TinyTim and the parameter changes laid out in Gillis et al. (2020), 
	which were tested on ACS imaging. As such, this method is not recommended for instruments
	other than ACS or cameras other than WFC.
	

	Note that the Gillis et al. (2020) code will be downloaded to your working directory. If keep = False (default), 
	it will be removed after use.

	Parameters:
		coords (astropy skycoord object): Coordinates of object of interest or list of skycoord objects.
		img (str): Path to image for which PSF is generated.
		imcam (str): 'ACS/WFC' is the only recommended instrument/camera combination for this PSF generation method.
		pos (list): Location of object of interest (spatial and spectral).[X, Y, chip, filter]
		plot (bool): If True, saves .pngs of the model PSFs.
		keep (bool): If True, retains make_psf.py (Gillis et al. 2020)
		verbose (bool): If True, prints progress messages.
		writeto (bool): If True, will write 2D model PSF (differentiated with '_topsf' 
			suffix) and will amend relevant image WCS information/remove extraneous extensions.
			This is in addition to the 2D PSF model saved by TinyTim.
		specchoice (str): 'list', 'blackbody', 'plaw_nu', 'plaw_lam' -- if 'list', must also specify
			listchoice; if 'blackbody', must also specify temp; if 'plaw_nu', must also specify specalpha;
			and if 'plaw_lam', must also specify specbeta.
		listchoice (str): One of 'O5', 'O8F', 'O6', 'B1V', 'B3V', 'B6V', 'A0V', 'A5V', 'F6V', 'F8V',
			'G2V', 'G5V', 'G8V', 'K4V', 'K7V', 'M1.5V', 'M3V'
		temp (float): Temperature of blackbody spectrum in K.
		specalpha (float): Spectral index alpha for F(nu)~nu^alpha.
		specbeta (float): Spectral index alpha for F(lambda)~lambda^beta.
		fov_arcsec (float): Diameter of model PSF image in arcsec.
		despace (float): Focus, secondary mirror despace in micron. Scaled by 0.011 and added to
			the 4th Zernike polynomial.
		sample (float): Factor by which to undersample the PSF. Default is not to undersample.
		linearfit (bool): Use linear fit rather than Gillis et al. amended Zernike polynomials.
		regrid (bool): If True, will (interpolate and) regrid model PSF to image pixel scale.

	Returns:
		TinyTim model PSF using amended Gillis et al. (2020) parameters
	"""

	if not TINY_PATH:
		# this is a warning and not an error on the off chance that the TinyTim executables are 
		# in the working directory
		warnings.warn('Tiny Tim is not in your path. Make sure that it is installed -- https://github.com/spacetelescope/tinytim/releases/tag/7.5 -- and your TINYTIM environment variable is set or select a different PSF generation mode.', Warning, stacklevel = 2)

	if not os.path.exists('make_psf.py'):
		# download Gillis et al. (2020) code; https://bitbucket.org/brgillis/tinytim_psfs/src/master/
		rawurl = 'https://bitbucket.org/brgillis/tinytim_psfs/raw/55299ae1a9b3c299b7910a14622e88c0ffd9d8a1/make_psf.py'
		os.system('wget ' + rawurl)
		if verbose:
			print('Retrieved make_psf.py')
	
	from make_psf import make_subsampled_model_psf

	coordstring = str(coords.ra)
	if coords.dec.deg > 0:
		coordstring += '+'+str(coords.dec)
	if coords.dec.deg >= 0:
		coordstring += str(coords.dec)
		
	modname = img.replace('.fits', coordstring+'_%s'%pos[3]+'_psf')

	make_subsampled_model_psf(modname,
		    psf_position=(pos[0], pos[1]),
		    focus=despace,
		    chip=pos[2],
		    spec_type=specchoice,
		    detector=tinyparams['imcam'][imcam],
		    filter_name=pos[3],
		    psf_size=fov_arcsec,
		    tinytim_path=TINY_PATH,
		    subsampling_factor=sample,
		    linear_fit=linearfit,
		    clobber=True)


	if os.path.exists('make_psf.py') and not keep:
		os.remove('make_psf.py')
		if verbose:
			print('Removed make_psf.py')


	if imcam not in  ['ACS/WFC', 'ACS/HRC']:
		psfmodel = fits.open(modname+'00_psf.fits')[0].data

	if imcam in ['ACS/WFC', 'ACS/HRC']:
		psfmodel = fits.open(modname+'00.fits')[0].data


	if regrid:
		if sample != 1.:
			psfmodel = regrid(psfmodel, sample)

	if plot:
		fig= plt.figure(figsize = (5, 5))
		plt.imshow(psfmodel, origin = 'lower', cmap = 'Greys_r')
		plt.colorbar()
		fig.savefig(modname+'.png', bbox_inches = 'tight', dpi = 100)

		if verbose:
			print('PSF model image written to %s.png'%(modname))

	if writeto:
		rewrite_fits(psfmodel, coords, img, imcam, pos, method = 'TinyTim (Gillis+ mod)')

	return psfmodel


def stdpsf(coords, img, imcam, pos, plot = False, verbose = False, 
	writeto = True, fov_arcsec = 6, norm = 1, regrid = True):
	"""
	Coordinate-specific PSFs from STDPSF model grids for HST, JWST.

	Makes use of https://www.stsci.edu/~jayander/HST1PASS/LIB/PSFs/STDPSFs/ and 
	https://www.stsci.edu/~jayander/JWST1PASS/LIB/PSFs/STDPSFs/.

	Parameters:
		coords (astropy skycoord object): Coordinates of object of interest or list of skycoord objects.
		img (str): Path to image for which PSF is generated.
		imcam (str): Specification of instrument/camera used to capture the images (e.g., 'ACS/WFC', 'WFC3/IR', 'WFPC', 
			'WFPC2', 'MIRI', 'NIRCAM', 'NIRISS/Imaging'). For 'WFPC' and 'WFPC2', the camera is selecte by-chip and 
			should not be specified here.
		pos (list): Location of object of interest (spatial and spectral).[X, Y, chip, filter]
		plot (bool): If True, saves .pngs of the model PSFs.
		verbose (bool): If True, prints progress messages.
		writeto (bool): If True, will write 2D model PSF (differentiated with '_topsf' 
			suffix) and will amend relevant image WCS information/remove extraneous extensions.
		fov_arcsec (float): Diameter of model PSF image in arcsec.
		norm (float): Flux normalization for output PSF model.

	Returns:
		STDPSF model PSF

	"""

	# build the url that points to the STDPSF
	imcamurl = imcam.replace('/', '')
	if imcamurl == 'WFC3UVIS':
		imcamurl = 'WFC3UV'

	if imcamurl == 'NIRCAM':
		imcamurl = 'NIRCam'

	if imcamurl == 'NIRISSImaging':
		imcamurl = 'NIRISS'


	if imcam in ['WFPC', 'WFPC1']:
		raise ValueError("There is no available STDPSF grid for WFPC imaging. Please select a different PSF generation method.")

	if imcam in ['ACS/WFC', 'ACS/HRC', 'WFC3/UVIS', 'WFC3/IR', 'WFPC2']:
		baseurl = 'https://www.stsci.edu/~jayander/HST1PASS/LIB/PSFs/STDPSFs/'

		url = baseurl+imcamurl+'/STDPSF_%s_%s'%(imcamurl, pos[3])
		
		if imcam == 'ACS/WFC':
			url += '_SM3.fits'
		elif (imcam == 'WFC3/IR') and (pos[3] == 'F139M'):
			url += '_1x1.fits'
		else:
			url += '.fits'


	if imcam in ['NIRCAM', 'MIRI', 'NIRISS/Imaging']:
		baseurl = 'https://www.stsci.edu/~jayander/JWST1PASS/LIB/PSFs/STDPSFs/'

		if imcam in ['MIRI', 'NIRISS/Imaging']:
			url = baseurl+imcamurl+'/STDPSF_%s_%s.fits'%(imcamurl, pos[3])

		if imcam == 'NIRCAM':
			if pos[3] in ['F250M', 'F277W', 'F356W', 'F360M', 'F410M', 'F444W', 'F480M']:
				det = pos[2][:-1]+'L'
				url = baseurl+imcamurl+'/LWC/STDPSF_%s_%s.fits'%(det, pos[3])

			if pos[3] in ['F070W', 'F090W', 'F115W', 'F140M', 'F150W', 'F182M', 'F200W'
							'F210M', 'F212N']:
				url = baseurl+imcamurl+'/SWC/%s/STDPSF_%s_%s.fits'%(pos[3], pos[3], pos[2])

	det = None #set detector for photutils
	if imcam in ['WFPC2', 'ACS/WFC']:
		det = pos[2]
	if (imcam == 'NIRCAM') and (pos[2] not in ['NGCA5', 'NRCB5']):
		det = stdpsf_jwdet[pos[2]]

	coordstring = str(coords.ra)
	if coords.dec.deg > 0:
		coordstring += '+'+str(coords.dec)
	if coords.dec.deg >= 0:
		coordstring += str(coords.dec)

	modname = img.replace('.fits', '_'+coordstring+'_%s'%pos[3]+'_psf')


	pixkey = imcam #set pixel scale to get the dimensions of x, y
	if imcam in ['WFPC', 'WFPC1']:
		if pos[2] <= 4:
			pixkey += '_wf'
		if pos[2] >= 5:
			pixkey += '_pc'
	if (imcam == 'WFPC2') and (pos[2] == 1):
		pixkey += '_pc'
	if (imcam == 'WFPC2') and (pos[2] >= 2):
		pixkey += 'wf'
	if imcam == 'NIRCAM':
		if pos[2] in ['NRCA5', 'NRCB5', 'NRCALONG', 'NRCBLONG']:
			pixkey += '_long'
		if pos[2] not in ['NRCA5', 'NRCB5', 'NRCALONG', 'NRCBLONG']:
			pixkey += '_short'

	dimxy = fov_arcsec/plate_scale[pixkey] #make square PSF
	halfdim = dimxy//2
	xmin = int(pos[0]) - halfdim
	xmax = int(pos[0]) + halfdim
	ymin = int(pos[1]) - halfdim
	ymax = int(pos[1]) + halfdim

	x, y = np.meshgrid(np.arange(xmin, xmax+1), np.arange(ymin, ymax+1))

	#preferred equivalent to using photutils.psf.stdpsf_reader directly
	model = GriddedPSFModel.read(filename = url, detector_id = det, format= 'stdpsf')
	psfmodel = model.evaluate(x = x, y = y, flux = norm, x_0 = int(pos[0]), y_0 = int(pos[1]))

	if plot:
		fig= plt.figure(figsize = (5, 5))
		plt.imshow(psfmodel, origin = 'lower', cmap = 'Greys_r')
		plt.colorbar()
		fig.savefig(modname+'.png', bbox_inches = 'tight', dpi = 100)

	if writeto:
		rewrite_fits(psfmodel, coords, img, imcam, pos, method = 'STDPSFs')

	return psfmodel


def jwpsf(coords, img, imcam, pos, plot = False, verbose = False, writeto = True,
	fov = 6, sample = 1., regrid = True, image_mask = None, pupil_mask = None,
	**calckwargs):
	"""
	Generate JWST and Roman PSFs using WebbPSF.

	Parameters:
		coords (astropy skycoord object): Coordinates of object of interest or list of skycoord objects.
		img
		imcam
		pos
		plot
		verbose
		writeto (bool): If True, will write 2D model PSF (differentiated with '_topsf' 
			suffix) and will amend relevant image WCS information/remove extraneous extensions.
			This is in addition to the 2D PSF models saved by WebbPSF (which will be saved as img_psf.fits).
		fov
		sample
		regrid
		image_mask
		pupil_mask
		**calckwargs: Additional arguments for calc_psf() -- see 
			https://webbpsf.readthedocs.io/en/latest/api/webbpsf.JWInstrument.html#webbpsf.JWInstrument.calc_psf
			Should be fed to the spike.psf.jwst/roman in kwargs as a dictionary called calckwargs.

	Returns:
		WebbPSF model PSF

	"""
	x, y, chip, filt = post

	coordstring = str(coords.ra)
	if coords.dec.deg > 0:
		coordstring += '+'+str(coords.dec)
	if coords.dec.deg >= 0:
		coordstring += str(coords.dec)

	modname = img.replace('.fits', '_'+coordstring+'_%s'%pos[3]+'_psf')

	if imcam.upper() == 'NIRCAM':
		psf = webbpsf.NIRCam()

	if imcam.upper() == 'MIRI':
		psf = webbpsf.MIRI()

	if imcam.upper() == 'NIRISS':
		psf = webbpsf.NIRISS()

	if imcam.upper() == 'WFI':
		psf = webbpsf.roman.WFI()

	if imcam.upper() == 'CGI':
		psf = webbpsf.roman.RomanCoronagraph()
		warnings.warn("WebbPSF Roman CGI development halted in 2017. Use with caution.", Warning, stacklevel = 2) 

	if imcam.upper() in ['NIRCAM', 'WFI']:
		psf.detector = chip


	psf.filter = filt
	psf.detector_position = (x, y)

	if image_mask:
		psf.image_mask = image_mask

	if pupil_mask:
		psf.pupil_mask = pupil_mask

	#read aperture name from FITS header
	imfits = fits.open(img)
	aperturename = img[0].header['APERNAME']
	psf.aperturename = aperturename


	psfmod = psf.calc_psf(fov_arcsec = fov, ovesample = sample, **calckwargs)

	psfmodel = psfmod[3].data

	if regrid:
		if sample != 1.:
			psfmodel = regrid(psfmodel, sample)


	if plot:
		fig= plt.figure(figsize = (5, 5))
		plt.imshow(psfmodel, origin = 'lower', cmap = 'Greys_r')
		plt.colorbar()
		fig.savefig(modname+'.png', bbox_inches = 'tight', dpi = 100)

		if verbose:
			print('PSF model image written to %s.png'%(modname))


	if writeto:
		rewrite_fits(psfmodel, coords, img, imcam, pos, method = 'WebbPSF')


	return psfmodel

def effpsf(coords, img, imcam, pos, plot = False, verbose = False, mask = True,
	writeto = True, fov_arcsec = 6, norm = 1, starselect = 'DAO', starselectargs = {}, 
	epsfargs = {'oversampling':1, 'progress_bar':False}):
	"""
	Generate PSFs using the empirical photutils.epsf routine.

	Parameters:
		coords (astropy skycoord object): Coordinates of object of interest or list of skycoord objects.
		img (str): Path to image for which PSF is generated.
		imcam (str): Specification of instrument/camera used to capture the images (e.g., 'ACS/WFC', 'WFC3/IR', 'WFPC', 
			'WFPC2', 'MIRI', 'NIRCAM', 'NIRISS/Imaging'). For 'WFPC' and 'WFPC2', the camera is selecte by-chip and 
			should not be specified here.
		pos (list): Location of object of interest (spatial and spectral).[X, Y, chip, filter]
		plot (bool): If True, saves .pngs of the model PSFs.
		verbose (bool): If True, prints progress messages.
		mask (bool): If True, uses data quality array to mask some pixels.
		writeto (bool): If True, will write 2D model PSF (differentiated with '_topsf' 
			suffix) and will amend relevant image WCS information/remove extraneous extensions.
		fov_arcsec (float): Diameter of model PSF image in arcsec.
		norm (float): Flux normalization for output PSF model.
		starselect (str): 'DAO', 'IRAF', or 'peak', which use DAOStarFinder, IRAFStarFinder, and 
			find_peaks from photutils respectively.
		starselectargs (dict): Keyword arguments for the chosen star detection method.
		epsfargs (dict): Keyword arguments for the EPSFBuilder. Default in spike is to not oversample
			the PSF, but the regridding is all handled during the creation of the coord-specific model.

	Returns:
		ePSF model PSF
	
	"""

	ext = 1 #read data from relevant SCI extension
	if (imcam in ['ACS/WFC', 'WFC3/UVIS']) and (pos[2] == 1):
		ext = 4
	if (imcam in ['ACS/WFC', 'WFC3/UVIS']) and (pos[2] == 2):
		ext = 1 #yes, it's already 1, but this is to make things explicit
	if imcam in ['WFPC', 'WFPC1', 'WFPC2']:
		ext = pos[2]

	coordstring = str(coords.ra)
	if coords.dec.deg > 0:
		coordstring += '+'+str(coords.dec)
	if coords.dec.deg >= 0:
		coordstring += str(coords.dec)

	modname = img.replace('.fits', '_'+coordstring+'_%s'%pos[3]+'_psf')


	pixkey = imcam #set pixel scale to get the dimensions of x, y
	if imcam in ['WFPC', 'WFPC1']:
		if pos[2] <= 4:
			pixkey += '_wf'
		if pos[2] >= 5:
			pixkey += '_pc'
	if (imcam == 'WFPC2') and (pos[2] == 1):
		pixkey += '_pc'
	if (imcam == 'WFPC2') and (pos[2] >= 2):
		pixkey += 'wf'
	if imcam == 'NIRCAM':
		if pos[2] in ['NRCA5', 'NRCB5', 'NRCALONG', 'NRCBLONG']:
			pixkey += '_long'
		if pos[2] not in ['NRCA5', 'NRCB5', 'NRCALONG', 'NRCBLONG']:
			pixkey += '_short'

	dat = fits.open(img)[ext].data

	mean, median, std = sigma_clipped_stats(dat, sigma=3.0)

	if starselect.upper() == 'DAO':
		# take default FWHM to be 2x the detector plate scale, can overwrite with starselectargs
		find = DAOStarFinder(threshold = 5*std, fwhm = 2*plate_scale[pixkey], **starselectargs)

	if starselect.upper() == 'IRAF':
		find = IRAFStarFinder(threshold = 5*std, fwhm = 2*plate_scale[pixkey], **starselectargs)

	if mask:
		maskarr = fits.open(img)[ext+2].data
		sources = find(dat - median, mask = maskarr)

	if not mask:
		sources = find(dat - median)

	exsize = 35 #size of extraction box
	xs = sources['xcentroid']
	ys = sources['ycentroid']
	exmask = ((xs > (exsize//2)) & (xs < (dat.shape[1] -1 - (exsize//2))) &
        (ys > (exsize//2)) & (ys < (dat.shape[0] -1 - (exsize//2))))
	tab = Table()
	tab['x'] = xs[exmask]
	tab['y'] = ys[exmask]
	nddata = NDData(data = dat - median) 
	stars = extract_stars(nddata, tab, size = exsize)

	dimxy = fov_arcsec/plate_scale[pixkey] #make square PSF
	halfdim = dimxy//2
	xmin = int(pos[0]) - halfdim
	xmax = int(pos[0]) + halfdim
	ymin = int(pos[1]) - halfdim
	ymax = int(pos[1]) + halfdim

	x, y = np.meshgrid(np.arange(xmin, xmax+1), np.arange(ymin, ymax+1))

	if verbose:
		# ensure progress bar is toggled if verbose is true
		epsfargs['progress_bar'] = True

	epsfbuilder = EPSFBuilder(**epsfargs)

	model, fitstars = epsfbuilder(stars)
	psfmodel = model.evaluate(x = x, y = y, flux = norm, x_0 = int(pos[0]), y_0 = int(pos[1]))

	if plot:
		fig= plt.figure(figsize = (5, 5))
		plt.imshow(psfmodel, origin = 'lower', cmap = 'Greys_r')
		plt.colorbar()
		fig.savefig(modname+'.png', bbox_inches = 'tight', dpi = 100)

	if writeto:
		rewrite_fits(psfmodel, coords, img, imcam, pos, method = 'ePSFs')

	return psfmodel


def psfex(coords, img, imcam, pos, plot = False, verbose = False, writeto = True, 
	savepsfex = False, crclean = True, seconf = None, psfconf = None):
	"""
	Generate PSFs using PSFEx.

	Parameters:
		coords (astropy skycoord object): Coordinates of object of interest or list of skycoord objects.
		imcam
		img (str): Path to image for which PSF is generated.
		pos (list): [X, Y, chip, filter] as output from spike.tools.checkpixloc.
		plot (bool): If True, saves .pngs of the model PSFs.
		verbose (bool): If True, prints progress messages.
		writeto (bool): If True, will write 2D model PSF (differentiated with '_topsf' 
			suffix) and will amend relevant image WCS information/remove extraneous extensions. 
			This is in addition to the .psf file saved by PSFEx. No 2D PSF model is saved by PSFEx 
			by default, but this can be toggled in the tools.pypsfex arguments.
		savepsfex (str): If 'fits' or 'arr' save 2D model to that format.
		crclean (bool): If True, use CR-cleaned image as SExtractor input.
		seconf (str): Path to SExtractor configuration file if not using default.
		peconf (str): Path to PSFEx configuration file if not using default.

	Returns:
		2D PSFEx PSF model
	"""

	ext = 1 #run SExtractor only on relevant SCI extension
	if (imcam in ['ACS/WFC', 'WFC3/UVIS']) and (pos[2] == 1):
		ext = 4
	if (imcam in ['ACS/WFC', 'WFC3/UVIS']) and (pos[2] == 2):
		ext = 1 #yes, it's already 1, but this is to make things explicit
	if imcam in ['WFPC', 'WFPC1', 'WFPC2']:
		ext = pos[2]

	tools.pysextractor(img+'[%i]'%ext, config = seconf)
	if verbose:
		print('Finished SExtractor, running PSFEx')
	psfmodel = tools.pypsfex(img.replace('fits', 'cat'), config = psfconf, save = savepsfex)
	if verbose:
		print('Finished PSFEx, generating image')

	coordstring = str(coords.ra)
	if coords.dec.deg > 0:
		coordstring += '+'+str(coords.dec)
	if coords.dec.deg >= 0:
		coordstring += str(coords.dec)

	modname = img.replace('.fits', '_'+coordstring+'_%s'%pos[3]+'_psf')

	if plot:
		fig= plt.figure(figsize = (5, 5))
		plt.imshow(psfmodel, origin = 'lower', cmap = 'Greys_r')
		plt.colorbar()
		fig.savefig(modname+'.png', bbox_inches = 'tight', dpi = 100)

		if verbose:
			print('PSF model image written to %s.png'%(modname))

	if writeto:
		rewrite_fits(psfmodel, coords, img, imcam, pos, method = 'PSFEx')

	return psfmodel


	


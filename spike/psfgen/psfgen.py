import os
import subprocess
import pkg_resources
from spike import tools
import matplotlib.pyplot as plot
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
		imcam
		pos (list): Location of object of interest (spatial and spectral).[X, Y, chip, filter]
		plot (bool): If True, saves .pngs of the model PSFs.
		verbose (bool): If True, prints progress messages.
		writeto (bool): If True, will write 2D model PSF to copy of img (differentiated with '_topsf' 
			suffix) and will amend relevant WCS information/remove extraneous extensions.
		ebmv (float):
		av (float):
		wmag (float):
		jitter (float):
		major (float):
		minor (float):
		angle (float):
		specchoice (str): 'list', 'blackbody', 'plaw_nu', 'plaw_lam' -- if 'list', must also specify
			listchoice; if 'blackbody', must also specify temp, 
		listchoice (str): One of 'O5', 'O8F', 'O6', 'B1V', 'B3V', 'B6V', 'A0V', 'A5V', 'F6V', 'F8V',
			'G2V', 'G5V', 'G8V', 'K4V', 'K7V', 'M1.5V', 'M3V'
		temp (float)
		specalpha (float): Spectral index alpha for F(nu)~nu^alpha.
		specbeta (float): Spectral index alpha for F(lambda)~lambda^beta.
		fov_arcsec 
		despace (float): Focus, secondary mirror despace in micron. Scaled by 0.011 and added to
			the 4th Zernike polynomial.
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

	modname = img.replace('.fits', coordstring+'_%s_'%pos[3]+'_psf')

	if imcam in ['ACS/WFC', 'WFC3/UVIS']:
		command_list = [tinyparams['imcam'][imcam], pos[2], '%i %i'%(pos[0], pos[1]), 
		pos[3], spec, specparam, fov_arcsec, despace, modname]
	if imcam in ['ACS/HRC', 'WFC3/IR']:
		command_list = [16, '%i %i'%(pos[0], pos[1]), pos[3], 
		spec, specparam, fov_arcsec, despace, modname]
	if imcam == 'WFPC1':
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

	
	return placeholder



def tinygillispsf(coords, img, pos, plot = False, keep = False, verbose = False, writeto = True):
	"""
	Generate HST PSFs using TinyTim and the parameter changes laid out in Gillis et al (2020), 
	which were tested on ACS imaging.
	

	Note that the Gillis et al. (2020) code will be downloaded to your working directory. If keep = False (default), 
	it will be removed after use.

	Parameters:
		coords (astropy skycoord object): Coordinates of object of interest or list of skycoord objects.
		img (str): Path to image for which PSF is generated.
		pos (list): Location of object of interest (spatial and spectral).[X, Y, chip, filter]
		img_type (str): 'flc', 'flt', 'c0f', 'c1f' -- specifies which file-type to include.
		inst (str): 'ACS', 'WFC3', 'WFPC2', 'FOC', 'NICMOS'
		plot (bool): If True, saves .pngs of the model PSFs.
		keep (bool): If True, retains make_psf.py (Gillis et al. 2020)
		verbose (bool): If True, prints progress messages.
	"""

	if not os.path.exists('make_psf.py'):
		# download Gillis et al. (2020) code; https://bitbucket.org/brgillis/tinytim_psfs/src/master/
		rawurl = 'https://bitbucket.org/brgillis/tinytim_psfs/raw/55299ae1a9b3c299b7910a14622e88c0ffd9d8a1/make_psf.py'
		os.system('wget ' + rawurl)
		if verbose:
			print('Retrieved make_psf.py')
	
	from make_psf import make_subsampled_model_psf




	if os.path.exists('make_psf.py') and not keep:
		os.remove('make_psf.py')
		if verbose:
			print('Removed make_psf.py')




def stdpsf(coords, img, pretweaked = False, keeporig = True, plot = False, keep = False, verbose = False):
	"""
	Read in HST STDPSFs.

	"""

	if not os.path.exists('psf_utilities.py'):
		# download STScI code for handling Jay Anderson's STDPSFs: https://www.stsci.edu/~jayander/HST1PASS/LIB/PSFs/STDPSFs/
		rawurl = 'https://github.com/spacetelescope/hst_notebooks/blob/main/notebooks/WFC3/point_spread_function/psf_utilities.py'
		os.system('wget ' + rawurl)
		if verbose:
			print('Retrieved psf_utilities.py')
	
	from psf_utilities import download_psf_model




	if os.path.exists('psf_utilities.py') and not keep:
		os.remove('psf_utilities.py')
		if verbose:
			print('Removed psf_utilities.py')



def jwpsf(coords, img, pos, imcam, plot = False, verbose = False,
	fov = 6, oversample = 1., regrid = True, image_mask = None, pupil_mask = None,
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
		fov
		oversample
		regrid
		image_mask
		pupil_mask
		**calckwargs: Additional arguments for calc_psf() -- see 
			https://webbpsf.readthedocs.io/en/latest/api/webbpsf.JWInstrument.html#webbpsf.JWInstrument.calc_psf

	Returns:

	"""
	x, y, chip, filt = post

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


	psfmod = psf.calc_psf(fov_arcsec = fov, ovesample = oversample, **calckwargs)

	psfmodel = psfmod[3].data

	# if regrid:
	# 	if oversample != 1.:
	# 		## need to interpolate the returned values
	# 		# will just return the relevant array, which can be written to the FITS file
	# 		# for tweaking etc



	return placeholder

def effpsf():
	"""
	Generate PSFs using the empirical photutils.epsf routine.

	
	"""

# https://photutils.readthedocs.io/en/stable/api/photutils.psf.GriddedPSFModel.html#photutils.psf.GriddedPSFModel
# also relevant for STDPSFs		


	return placeholder

def sepsf(coords, img, imcam, pos, plot = False, verbose = False, seconf = None, psfconf = None):
	"""
	Generate PSFs using PSFEx.

	Parameters:
		coords (astropy skycoord object): Coordinates of object of interest or list of skycoord objects.
		imcam
		img (str): Path to image for which PSF is generated.
		pos
		plot (bool): If True, saves .pngs of the model PSFs.
		verbose (bool): If True, prints progress messages.
		seconf
		peconf

	Returns:
		2D PSFEx PSF model
	"""

	tools.pysextractor(img, config = seconf)
	if verbose:
		print('Finished SExtractor, running PSFEx')
	psfmodel = tools.pypsfex(img.replace('fits', 'cat'), config = psfconf)
	if verbose:
		print('Finished PSFEx, generating image')

	coordstring = str(coords.ra)
	if coords.dec.deg > 0:
		coordstring += '+'+str(coords.dec)
	if coords.dec.deg >= 0:
		coordstring += str(coords.dec)

	modname = img.replace('.fits', coordstring+'_%s_'%pos[3]+'_psf')

	if plot:
		fig= plt.figure(figsize = (5, 5))
		plt.imshow(psfmodel)
		plt.colorbar()
		fig.savefig(modname+'.png', bbox_inches = 'tight', dpi = 100)

		if verbose:
			print('PSF model image written to %s.png'%(modname))

	return psfmodel


	


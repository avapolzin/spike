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

##########
# * * * *
##########

tinyparams = {}
tinyparams['imcam'] = {'ACS/WFC':15, 'ACS/HRC':16}

try:
    TINY_PATH = os.environ['TINYTIM']
except:
    TINY_PATH = None


def tinypsf(coords, img, pos, plot = False, verbose = False, 
	ebmv = None, av = None, wmag = None,
	jitter = None, major = None, minor = None, angle = None):
	"""
	Generate HST PSFs using TinyTim.
	All of the options from TinyTim are easily available here *except* custom filters
	and subsampling, as they complicate use with spike. If you would like a subsampled
	Tiny Tim PSF model, please use spike.psfgen.tinygillispsf() instead.
	In addition to making model PSF, write tweak parameters to header.

	Parameters:
		coords (astropy skycoord object): Coordinates of object of interest or list of skycoord objects.
		img (str): Path to image for which PSF is generated.
		pos (list): Location of object of interest (spatial and spectral).[X, Y, chip, filter]
		plot (bool): If True, saves .pngs of the model PSFs.
		verbose (bool): If True, prints progress messages.
		ebmv (float):
		av (float):
		wmag (float):
		jitter (float):
		major (float):
		minor (float):
		angle (float):
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

	## choose your own adventure command list generation
	# this will be annoying
	# and will want to draw from image header and inputs from psf mostly
	# this is also where tinyparams comes into play
	# command_list = 

	if imcam == 'ACS/WFC':
		command_list = []


	tiny = subprocess.Popen(tiny1, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
	newline = os.linesep

	tiny.communicate(newline.join(command_list).encode())

	
	os.system(TINY_PATH+'/tiny2 tiny.param')
	if verbose:
		print("Completed PSF modeling.")

	if inst.upper() == 'ACS': 
		os.system(TINY_PATH+'/tiny3 tiny.param')
		if verbose:
			print("Completed geometric distortion correction.")

	
	return placeholder



def tinygillispsf(coords, img, pos, plot = False, keep = False, verbose = False):
	"""
	Generate HST PSFs using TinyTim and the parameter changes laid out in Gillis et al (2020).
	In addition to making model PSF, write tweak parameters to header.

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


	


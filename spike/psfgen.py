import os


##########
# * * * *
##########

def tinypsf(coords, pretweaked = False, keeporig = True, plot = False, verbose = False):
	"""
	Generate HST PSFs using TinyTim.

	Parameters:
		coords (str): Coordinates of object of interest in HH:MM:DD DD:MM:SS or degree format.
		
		img_type (str): 'flc', 'flt', 'c0f', 'c1f' -- specifies which file-type to include.
		pretweaked (bool): If True, skips TweakReg steps to include sub-pixel corrections.
		keeporig (bool): If True (and pretweaked = False), create copy of img_dir before TweakReg.
		plot (bool): If True, saves .pngs of the model PSFs.
		verbose (bool): If True, prints progress messages.
	"""


	if keeporig and not pretweaked:
		os.system('mkdir '+img_dir+'_orig')
		os.system('cp -r '+img_dir+' '+'img_dir'+'_copy')
		if verbose:
			print('Made copy of '+img_dir)



def tinygillispsf(coords, pretweaked = False, keeporig = True, plot = False, keep = False, verbose = False):
	"""
	Generate HST PSFs using TinyTim and the parameter changes laid out in Gillis et al (2020).

	Note that the Gillis et al. (2020) code will be downloaded to your working directory. If keep = False (default), 
	it will be removed after use.

	Parameters:
		coords (str): Coordinates of object of interest in HH:MM:DD DD:MM:SS or degree format.
		img_type (str): 'flc', 'flt', 'c0f', 'c1f' -- specifies which file-type to include.
		inst (str): 'ACS', 'WFC3', 'WFPC2', 'FOC', 'NICMOS'
		pretweaked (bool): If True, skips TweakReg steps to include sub-pixel corrections.
		keeporig (bool): If True (and pretweaked = False), create copy of img_dir before TweakReg.
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

def wfcpsf():
	"""
	Read in empirical HST/WFC3 PSFs. ## will really need to check instructions for how to do this

	"""


def jwpsf():
	"""
	Generate JWST and Roman PSFs using WebbPSF.

	"""


def effpsf():
	"""
	Generate PSFs using the empirical photutils.epsf routine.

	"""



def sepsf():
	"""
	Generate PSFs using PSFEx.

	"""
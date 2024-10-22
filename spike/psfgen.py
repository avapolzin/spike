import os


class Vividict(dict):
	## with thanks to https://stackoverflow.com/a/24089632
    def __missing__(self, key):
        value = self[key] = type(self)()
        return value


##########
# * * * *
##########

tinyparams = Vividict() #to index into TinyTim parameters from proper names
tinyparams['camera']['name'] = ['ACS/WFC', 'ACS/HRC']
tinyparams['camera']['value'] = [15, 16]


def tinypsf(coords, img, plot = False, verbose = False):
	"""
	Generate HST PSFs using TinyTim.
	In addition to making model PSF, write tweak parameters to header.

	Parameters:
		coords (list): Pixel coordinates of object of interest.[X, Y, chip]
		img (str): Path to image for which PSF is generated.
		
		img_type (str): 'flc', 'flt', 'c0f', 'c1f' -- specifies which file-type to include.
		plot (bool): If True, saves .pngs of the model PSFs.
		verbose (bool): If True, prints progress messages.
	"""




def tinygillispsf(coords, img, plot = False, keep = False, verbose = False):
	"""
	Generate HST PSFs using TinyTim and the parameter changes laid out in Gillis et al (2020).
	In addition to making model PSF, write tweak parameters to header.

	Note that the Gillis et al. (2020) code will be downloaded to your working directory. If keep = False (default), 
	it will be removed after use.

	Parameters:
		coords (list): Pixel coordinates of object of interest. [X, Y, chip]
		img (str): Path to image for which PSF is generated.

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



def wfcpsf():
	"""
	Read in empirical HST/WFC3 PSFs. ## will really need to check instructions for how to do this

	"""


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
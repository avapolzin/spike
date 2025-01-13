.. _spike.quickstart:

Quickstart Guide
================

``spike`` is intended to be simple to use. At minimum, one just needs to a working directory and object coordinates to begin. The working directory should be structured to include CTE-corrected, but not yet combined .fits files from a single instrument on a single telescope. For example:

.. code-block:: python

	from spike import psf

	acs_path = '/path/to/acs/data/'

	### TinyTim ###
	psf.hst(img_dir = acs_path, obj = '10:00:33.0178 +02:09:52.304', img_type = 'flc', 
		inst = 'ACS', camera = 'WFC', method='TinyTim', savedir = 'psfs_tiny', verbose = True,
		pretweaked = False)

	### TinyTim (Gillis et al. mod) ###
	psf.hst(img_dir = acs_path, obj = '10:00:33.0178 +02:09:52.304', img_type = 'flc', 
		inst = 'ACS', camera = 'WFC', method='TinyTim_Gillis', savedir = 'psfs_tinygillis', 
		verbose = True, pretweaked = True)

	### STDPSF ###
	psf.hst(img_dir = acs_path, obj = '10:00:33.0178 +02:09:52.304', img_type = 'flc', 
		inst = 'ACS', camera = 'WFC', method='stdpsf', savedir = 'psfs_stdpsf', verbose = True,
		pretweaked = True)

	### ePSF ###
	psf.hst(img_dir = acs_path, obj = '10:00:33.0178 +02:09:52.304', img_type = 'flc', 
		inst = 'ACS', camera = 'WFC', method='epsf', savedir = 'psfs_epsf', verbose = True,
		pretweaked = True)

	### PSFEx ###
	psf.hst(img_dir = acs_path, obj = '10:00:33.0178 +02:09:52.304', img_type = 'flc', 
		inst = 'ACS', camera = 'WFC', method='PSFEx', savedir = 'psfs_psfex', verbose = True,
		pretweaked = True)


In lieu of passing coordinates to obj, you can also provide an object name (as long as it's resolvable by NED/Simbad). For example:

.. code-block:: python

	from spike import psf

	acs_path = '/path/to/acs/data/'

	psf.hst(img_dir = acs_path, obj = 'M51', img_type = 'flc', inst = 'ACS', camera = 'WFC')


	nircam_path = 'path/to/nircam/data/'

	psf.jwst(img_dir = nircam_path, obj = 'M51', img_type = 'cal', inst = 'NIRCam')


The last code block shows minimal examples, which includes all of the required inputs (camera is only required for ACS and WFC3). ``spike`` handles filter and detector/chip identification automatically, and the default parameters are sufficient to produce PSFs in most cases. The top-level functions ``spike.psf.hst``, ``spike.psf.jwst``, and ``spike.psf.roman`` also take a number of keyword arguments that allow for near-complete customization of the generated PSFs.

Note that it will often be preferred to provide a savedir argument, as otherwise files with the same name may be overwritten in the default /psfs directory.

The output drizzled/resampled PSF is placed in the full spatial context of the processed frames. A convenience function is included to crop the data to the region immediately around the PSF, ``spike.tools.cutout``.


``spike.tools`` and ``spike.psfgen`` functions can also be used in isolation. Note that the PSF generation functions in ``spike.psfgen`` assume that the "coords" argument will be the output of ``spike.tools.objloc`` and the "pos" argument will be the output of ``spike.tools.checkpixloc``. An ``astropy`` SkyCoord object and a list following [X, Y, chip, filter] can be input respectively instead.
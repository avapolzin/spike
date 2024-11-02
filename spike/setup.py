import setuptools

##### Set up C bindings #####
## with thanks to https://stackoverflow.com/a/37481508
## need to see if people already have these packages installed so not re-installing/overwriting
## how can I do this in an OS agnostic way?
## best I can do for now is to install in the local working directory
## and this hard codes the version

def cinstall():
	import os

	## TinyTim
	os.system('curl -o ./tinytim7.5.zip "https://github.com/spacetelescope/tinytim/archive/refs/tags/7.5.zip"')


	## SExtractor
	os.system('curl -o ./sextractor2.25.0.zip "https://github.com/astromatic/sextractor/archive/refs/tags/2.25.0.zip"')
	os.system('unzip sextractor-2.25.0.zip')
	os.system('cd sextractor-2.25.0')
	os.system('')


#######################

setuptools.setup(
	name = "spike-psf",
	version = "0.1",
	author = "Ava Polzin",
	author_email = "apolzin@uchicago.edu",
	description = "Drizzle HST and JWST PSFs for improved analyses.",
	packages = ["spike", "spike/psf", "spike/psfgen", "spike/tools"],
	url = "https://github.com/avapolzin/spike",
	license = 'MIT',
	classifiers = [
		"Development Status :: 4 - Beta",
		"Intended Audience :: Science/Research",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
		"Programming Language :: Python",
		"Topic :: Scientific/Engineering :: Astronomy",
		"Topic :: Scientific/Engineering :: Physics"],
	python_requires = ">=3",
	install_requires = ["astropy", "drizzlepac", "matplotlib", "mpi4py", "numpy", "webbpsf"],
	cmdclass={'install': CustomInstall}
)
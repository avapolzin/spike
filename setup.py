import setuptools


setuptools.setup(
	name = "spike-psf",
	version = "0.5",
	author = "Ava Polzin",
	author_email = "apolzin@uchicago.edu",
	description = "Drizzle/resample HST, JWST, and Roman PSFs for improved analyses.",
	packages = ["spike", "spike/psf", "spike/psfgen", "spike/tools", 
	"spike/jwstcal", "spike/romancal", "spike/stcal", "spike/stpipe"],
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
	python_requires = ">=3.10",
	install_requires = ["asdf", "astropy", "crds", "drizzle", 
	"drizzlepac @ git+https://github.com/spacetelescope/drizzlepac.git", "gwcs", 
	"jsonschema", "matplotlib", "numpy", "photutils", "psutil", "pyyaml", "roman-datamodels", 
	"scipy", "spherical-geometry", "stdatamodels", "tweakwcs", "webbpsf"],
	package_data={'spike': ['configs/*/*']}
)
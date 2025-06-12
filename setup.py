import setuptools
from pathlib import Path
spike_home = Path(__file__).parent
pypi_descrip = (spike_home / "README.md").read_text()

setuptools.setup(
	name = "spike-psf",
	version = "1.1.0",
	author = "Ava Polzin",
	author_email = "apolzin@uchicago.edu",
	description = "Drizzle/resample HST, JWST, and Roman PSFs for improved analyses.",
	packages = ["spike", "spike/psf", "spike/psfgen", "spike/tools", 
	"spike/jwstcal", "spike/romancal", "spike/stcal", "spike/stpipe"],
	url = "https://github.com/avapolzin/spike",
	license = 'MIT',
	classifiers = [
		"Development Status :: 5 - Production/Stable",
		"Intended Audience :: Science/Research",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
		"Programming Language :: Python",
		"Topic :: Scientific/Engineering :: Astronomy",
		"Topic :: Scientific/Engineering :: Physics"],
	python_requires = ">=3.10",
	install_requires = ["asdf", "astropy", "crds", "drizzle", 
	# "drizzlepac @ git+https://github.com/spacetelescope/drizzlepac.git", 
	"gwcs", 
	"jsonschema", "matplotlib", "numpy", "photutils", "psutil", "pyyaml", "roman-datamodels", 
	"scipy", "spherical-geometry", "stdatamodels==2.2.0", "tweakwcs", 
	"stpsf"],
	package_data={'spike': ['configs/*/*']},
	long_description=pypi_descrip,
    long_description_content_type='text/markdown',
    project_urls={'source':"https://github.com/avapolzin/spike", 
    'documentation':"https://spike-psf.readthedocs.io"}
)

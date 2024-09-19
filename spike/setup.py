import setuptools

setuptools.setup(
	name = "spike",
	version = "0.1",
	author = "Ava Polzin",
	author_email = "apolzin@uchicago.edu",
	description = "Drizzle HST and JWST PSFs for improved analyses.",
	packages = ["spike", "spike/hst", "spike/jwst", "spike/roman"],
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
	install_requires = ["astropy", "drizzlepac", "matplotlib", "mpi4py", "numpy", "webbpsf"]
)
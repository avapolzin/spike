.. _spike/changelog:

Changelog
=========

See below for a record of salient changes to the code itself. Updates to e.g. documentation are not addressed here. The full record of detailed changes is available on `Github <https://github.com/avapolzin/spike/commits/>`_.

**Development version:**
Can be installed via GitHub (will be available on PyPI once it's formally released).
Documentation is up to date for the development version.

* Add allowance for more "coords" and "obj" types in ``spike.psfgen`` and ``spike.psf``
* Add "clobber" option (off by default, does not affect behavior of plotting or resampling)
* Create input prompt for ACS and WFC3 "camera" if not specified in ``spike.psf`` call
* Change Python version requirement (to >=3.11) in response to changes in ``drizzlepac>=3.10``
* Update ``spike.psf.hst`` "drizzleparams" defaults to be more agnostic to dither pattern
* More comprehensive cleanup of intermediate files


**v1.1.0 (June 12, 2025)**

Version that incorporates all changes from JOSS review.

* Move file suffixes in _topsf files to generate drc/drz files based on inputs
* Update naming scheme in ``spike.tools.rewrite_fits``
* Bug fix in renaming user-generated PSF models
* Updated 'F475W' -> 'F475Wx' in STDPSF url for WFC3/UVIS 


**v1.0.9 (June 2, 2025)**

* Add tolerance for sub-pixel coordinate differences in tests
* Update default sampling for ``STPSF``/``WebbPSF``
* Adopt auto setup of ``STPSF`` model from img
* Use explicit indexing of HDU in ``spike.psfgen.jwpsf``
* Fix "savefull" typo in ``spike.psfgen.jwpsf``
* Add support for PSFs near frame edges to ``spike.tools.rewrite_fits`` and ``spike.tools.cutout``


**v1.0.8 (May 14, 2025)**

* Fix path to "removedir" when "finalonly = True"


**v1.0.7 (May 12, 2025)**

* Update output filename post-drizzling in ``spike.psf``
* Add option to only retain drizzled products ("finalonly = True")
* Add "maskval" keyword argument as user option for ``spike.psfgen.effpsf``
* Adopt nanmedian instead of median for masked data in same module
* Change STDPSF link format for WFC3/UVIS
* Add support for floats in extension versions in ``spike.tools.rewrite_fits``
* Switch to ``STPSF`` as default from ``WebbPSF``; retain support for ``WebbPSF``
* Fix bug in ``astropy.wcs.utils.pixel_to_skycoords`` call for some cutouts


**v1.0.6 (May 8, 2025)**

* Add example notebooks
* Force format input path
* Update ``spike.psf`` to use same "modname" everywhere
* Fix unnecessary "+" in filenames for objects with negative declination
* Re-index loops across multiple files


**v1.0.5 (April 2, 2025)**

* Add explicit extension number in ``spike.tools.rewrite_fits``
* Fix bug that resulted in declination being duplicated in output filenames


**v1.0.4 (March 28, 2025)**

* Add error message if "Level 3" data products are used as input
* Remove temporary STDPSF naming convention fix, since addressed on STScI side


**v1.0.3 (March 22, 2025)**

* Fix inverted sampling in ``spike.tools.regridarr``
* Fix "coords" -> "coord" in loops if input is list of multiple objects


**v1.0.2 (March 18, 2025)**

* Fix to stable version of ``stdatamodel``
* Add temporary fix for differences between STDPSF naming conventions
* Update clean up steps to catch more output files


**v1.0 (March 3, 2025)**

Initial stable release.


**v0.5**

Pre-release development version.
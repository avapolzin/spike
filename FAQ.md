# FAQs

Since there are so many different codes in play, it make sense to have a centralized place to address common questions/concerns without necessitating digging through the documentation/issues. I will amend this as new considerations come up, though I've tried to project for more common questions here.

For more detailed questions/concerns about any of `spike`'s dependencies, please refer to the original documentation for that code specifically.

### Space-based Imaging

1. **The image processing steps aren't working and my data appear corrupted. Did `spike` cause this?**

Probably not. If the data appear corrupted prior to any of the processing steps (tweak or drizzle/resample), try redownloading your images. If you are using the [MAST](https://mast.stsci.edu) batch retrieval, consider using the browser download, which may be more reliable.

2. **Roman hasn't launched yet; how do I access data to play with `spike.psf.roman`?**

There are a lot of different groups dedicated to simulating data for the Roman Space Telescope. [Troxel et al. (2023)](https://ui.adsabs.harvard.edu/abs/2023MNRAS.522.2801T/abstract) has some nice examples of single detector data and you can generate your own Roman imaging with [STIPS](https://github.com/spacetelescope/STScI-STIPS) [(STIPS Development Team 2024)](https://ui.adsabs.harvard.edu/abs/2024arXiv241111978S/abstract). The pipeline is very similar to _JWST_'s, with the image from each of the detectors stored in its own file, so `spike.psf.roman` is, at its core, a modified version of `spike.psf.jwst`.

3. **Tweakreg keeps failing, noting that I'm out of memory. How should I proceed?**

This is a common issue with the WCS alignment steps, which are memory intensive, particularly for a large number of input files. The first (and easiest) solution is to simply specify pretweaked = True and skip that step altogether if the images are already sufficiently well-aligned for your purposes. Alternatively, you can alter the tweakparams input to change settings that may mitigate the load on your computational resources. You can also tweak the images yourself (which gives you more control over which files are included at any given point) and then, again, specify pretweaked = True when you run `spike`.

4. **Why am I seeing "ValueError: WCSNAME 'TWEAK' already present...", and how do I resolve it?**

Tweaking an image is a "destructive" process insofar as it irrevocably changes the FITS file. `Drizzlepac` specifically avoids overwriting this header key when it's present. You can either rerun the tweak step in `spike` using a different key (fed in via the tweakparams argument) or you can simply set pretweaked = True to skip the tweak step altogether.

5. **What file types are accepted by spike and why?**

`spike` works by generating PSFs for individual exposures and then running them through the same processing and combination steps employed by the *HST*, *JWST*, and Roman pipelines to process images. This creates a location-specific drizzled PSF that is a resampled and combined in the same way as the images are in the final drizzled/mosaiced product. Because `spike` relies on doing this image combination step, the input files should be calibrated, but not yet combined -- e.g., cal, flt, or flc files and not i2d, drz, or drc files. Similarly, because `astrodrizzle` does not work with waivered FITS files, `spike` only takes as input multi-extension FITS files. 


6. **I'm seeing an error that says "ValueError: Undefined variable 'uref' in string..." Why can't I tweak or drizzle WFPC2 imaging?**

The WFPC2 data use a prior convention/format for astrometry and WCS. You must update the WCS to be compatible with `drizzlepac`. There are [instructions on preprocessing WFPC2 data](https://spacetelescope.github.io/notebooks/notebooks/DrizzlePac/drizzle_wfpc2/drizzle_wfpc2.html) from STScI; however, in my experience, data recently downloaded from MAST should not have `stwcs.updatewcs.updatewcs` run, and instead the CRDS keywords just need to be added to your path. `spike` also handles this automatically when WFPC2 data are used.

Some other notes on this: The c0m files seem to behave more reliably than flt files as inputs. Additionally, if you are getting an error about celestial coordinates, `spike` may be reading the WCS from the header of one of the PSF models. Even with `clobber=True`, make sure that your input file directory is clear of artifacts from previous (especially aborted) runs for best performance. Tweaking WFPC2 imaging may impact how `drizzlepac` reads the data, so I recommend only tweaking if necessary.


### spike

1. **Why am I getting `NameResolveError: Unable to find coordinates for name ...` when I feed `spike.psf` an object name?**

First, check your internet connection. Name queries require access to the internet. The next most likely reason you'd get this sort of error is that the object name is not resolvable by NED. Providing coordinates will allow `spike` to proceed. If searching for that name generally works, I have found that sometimes (perhaps due to updates on the CDS side of things?) searches that have worked in the past will temporarily return an error. In that case, you can either wait a bit and try again with a name search or you can provide the coordinates yourself to run `spike` immediately.

2. **I am encountering a problem with one of the pipeline modules (`spike.jwstcal`, `spike.romancal`, or `spike.stcal`). How much has changed from the official Space Telescope releases?**

Each of `spike.jwstcal`, `spike.romancal`, and `spike.stcal` are subtly reworked versions of the STScI releases. Since namespace packages are not enabled (and would not be workable with the many interlocking dependencies) for `jwst` and `romancal`, the relevant portions of the JWST and Roman pipelines are installed directly with `spike` with pared down dependencies and install requirements. The code has been reorganized and reworked to have a more straightforward file structure and get rid of dependencies that are extraneous for the tweak and resample pipeline steps, so none of the scientific functionality has been changed. 

If your error seems to come from one of these modules, you can always start with the [`jwst`](https://jwst-pipeline.readthedocs.io/en/latest/) or [`romancal`](https://roman-pipeline.readthedocs.io/en/latest/) documentation to better understand the problem. Most interaction with these pipeline commands is through other `spike` functions, though, so it will also serve to toggle `verbose = True` and confirm that all prior steps are proceeding as expected (confirming the outputs look as you expect may help, as well). If the problem actually occurs at an intermediate step and the pipeline error is due to missing inputs, you can fix this by resolving the concern with that intermediate step (see the [`spike` documentation](https://spike-psf.readthedocs.io) or the other FAQ sections).

If you encounter a bug that ultimately traces back to `spike.jwstcal`, `spike.romancal`, or `spike.stcal`, and you would like to open an issue, please tag your issue with the "pipeline" label.

Note that `spike.jwstcal` and `spike.romancal` are dependent on `crds`, which means that the two environment variables CRDS_PATH and CRDS_SERVER_URL must be set according to the instructions [here](https://jwst-pipeline.readthedocs.io/en/latest/jwst/user_documentation/reference_files_crds.html).

3. **I'm encountering an AttributeError when I enable parallelization and define my own function to generate PSFs. How do I fix this?**

As it turns out, `multiprocessing` specifically requires that functions be *imported*. It is possible that you will have to create a dummy script that houses your custom PSF generation function. There's a good example of this on [StackOverflow](https://stackoverflow.com/a/42383397) and in the [`spike` tests](https://github.com/avapolzin/spike/blob/master/tests/tests.py).

4. **I'm working in Jupyter Lab/Notebook, and my environment variables are not loaded/not found. How do I access them from Jupyter?**

There are several ways to make sure that your environment variables are accessible. The various options are discussed in this [StackOverflow thread](https://stackoverflow.com/questions/37890898/how-to-set-env-variable-in-jupyter-notebook). I recommend following the example laid out in the `spike` [example_notebooks README](https://github.com/avapolzin/spike/blob/master/example_notebooks/README.md), which amends your kernel.json to consistently read your environment variables directly from your startup file.

5. **Why am I getting some version of `OSError: 8388608 requested and 0 written`?**

This error pops up when your computer is out of storage. The imaging files that `spike` uses are already quite large, and the various PSF generation and drizzling steps create additional files that can take up quite a bit of space. There is little to do for this while `spike` is running, but you can toggle `finalonly = True` from `spike.psf.hst`, `spike.psf.jwst`, and `spike.psf.roman` to only retain the drizzled/resampled PSFs after the last step. By default, though, `spike` saves all intermediate products.

6. **Can I still use `spike` with Python 3.10?**

In short, yes, though this is not recommended. In response to the deprecation of Python 3.10 support in `drizzlepac >= 3.10`, beginning in v1.1.1, `spike` was updated to require Python >= 3.11 by default. If you would like to use Python 3.10, earlier versions of `spike` will work. You may also wish to handle things on an ad hoc basis (at your own risk) and install `drizzlepac<=3.9.1` via [GitHub](https://github.com/spacetelescope/drizzlepac/releases) with a more recent version of `spike`. In that case, dependencies from [spike/docs/requirements_version.txt](https://github.com/avapolzin/spike/blob/master/docs/requirements_version.txt), which includes specified versions for all required packages in a working Python 3.10.16 environment (last tested with `spike` version 1.1.0), may be a useful guide. You may need to update your local `spike` setup.py in this case.

### TinyTim

*If you plan to use TinyTim PSFs (for HST), TinyTim must be downloaded and installed separately following the instructions [here](https://github.com/spacetelescope/tinytim/releases).* 

1. **Why does `tiny1` result in a path error (`Open_pupil_table : Could not open ~/tinytim-7.5/*.pup`)?**

First, confirm that the .pup file actually exists in your tinytim-7.5 directory. Assuming it does, this error is likely due to the syntax you used to set your `$TINYTIM` path variable. For bash shells, the quick fix _should be_ to swap out '\~/' with an absolute path like '/Users/username/'.

2. **Why am I getting an HTTPS error when my PSF generation method is 'TinyTim_Gillis'?**

If you don't already have the [Gillis et al. (2020)](https://bitbucket.org/brgillis/tinytim_psfs/src/master/) code downloaded, the first thing that `spike.psfgen` tries to do is download the relevant script. An HTTPS error may come about if BitBucket is down or if there's a problem with your connection. If you have the Gillis et al. script downloaded locally, simply copy it to your working directory and the issue should resolve.


### STDPSF 

1. **Why am I getting an HTTPS error when my PSF generation method is 'STDPSF'?**

The STDPSFs are read into `photutils` as URLs as needed, so there could be an issue connecting to the Space Telescope website for [HST](https://www.stsci.edu/~jayander/HST1PASS/LIB/PSFs/STDPSFs/) or [JWST](https://www.stsci.edu/~jayander/JWST1PASS/LIB/PSFs/STDPSFs/) STDPSFs.

If you can connect to the site through the link above, there may have been a change in the filename or path as those directories are not static and are sometimes updated. In that case, please either open an [issue](https://github.com/avapolzin/spike/issues) or send me an [email](mailto:apolzin@uchicago.edu) so that I can amend the code accordingly.

2. **No STDPSF grid exists for my chosen WFC3 filter. Can I still use a pre-computed empirical PSF?**

Yes, you can. You can download pre-computed empirical WFC3 PSFs from [MAST](https://mast.stsci.edu) (under "Select a Collection" > "WFC3 PSF"). Once you download these locally, you can feed `spike.psf.hst` `method = 'USER'` where `usermethod` will be the path to the directory where you downloaded those PSFs. If there are point sources in your image, you always have the option to compute empirical PSFs via `spike` with `PSFEx` or the `photutils` effective PSF.


### PSFEx

*If you plan to use PSFEx to generate empirical PSFs, both SExtractor and PSFEx must be downloaded and installed separately following the instructions [here](https://github.com/astromatic/sextractor) and [here](https://github.com/astromatic/psfex) respectively.* 

Some notes on PSFEx installation for Macs: You can use `brew install automake, libtool` to add the GNU functions that PSFEx requires for installation. If FFTW is not already installed on your machine, you will need to follow the instructions for both single- and double-point versions (see these [instructions](http://www.fftw.org/fftw2_doc/fftw_6.html#SEC69)). If ATLAS is not already installed, you can bypass that installation altogether by downloading and installing OpenBLAS. Even with a successful install, I found that PSFEx could not find the correct directories for OpenBLAS, so in your PSFEx directory, you will run some variation of `./configure --enable-openblas --with-openblas-incdir=/opt/OpenBLAS/include --with-openblas-libdir=/opt/OpenBLAS/lib
`.

There is also a bug in the PSFEx installation code -- discussed nicely [here](https://trac.macports.org/ticket/71003) -- within PSFEx/src/levmar/compiler.h, you will need to change "finite" to "isfinite" before attempting to run `make`.

1. **My output single-image PSFs look funny/there's an issue with my SExtractor catalog. How do I fix this?**

The first step if you aren't happy with your PSFEx output is to try adjusting the SExtractor and PSFEx parameters in their respective config files. `spike.psfgen` uses the default settings for each of these codes unless an overriding user input is specified. As a result, the star catalog and subsequent PSF generation are not fine-tuned for any specific use case beyond the parameters that were altered for high-resolution, space-based images.

Within spike/configs, there are example configuration and parameter files for PSFEx and SExtractor. These can be used as guides and can be *copied* and directly modified. (I recommend against modifying any of the files in spike/configs themselves unless you are interested in making global changes.)

2. **Why am I getting an `ZeroDivisionError: float division by zero` error?**

PSFEx relies on being able to detect stars in your images. In my experience, in fields (and/or filters) with few stars, it is possible that `PSFEx` will still run, but return PSF_FWHM = 0 and PSF_SAMP = 0 in the header of the resultant .psf file, as it did not actually have what to fit. You should first check those keys to ascertain whether this is the issue. If it is, I recommend either changing the fit parameters in the `SExtractor` and `PSFEx` configuration files or adopting a different PSF generation method.


### STPSF/WebbPSF

*If you plan to use STPSF -- formerly WebbPSF -- PSFs (for JWST and Roman), the relevant data must be downloaded and included in your path following the instructions [here](https://stpsf.readthedocs.io/en/latest/installation.html).* 





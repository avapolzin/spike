.. _spike/faq:

FAQs
====

This file is also available on the `GitHub <https://github.com/avapolzin/spike/blob/master/FAQ.md>`_, where it will be updated along with the development version of the code (and may be more responsive to common issues).

Since there are so many different codes in play, it make sense to have a centralized place to address common questions/concerns without necessitating digging through the documentation/issues. I will amend this as new considerations come up, though I've tried to project for more common questions here.

For more detailed questions/concerns about any of ``spike``'s dependencies, please refer to the original documentation for that code specifically.


Space-based Imaging
-------------------

1. **The image processing steps aren't working and my data appear corrupted. Did spike cause this?**

Probably not. If the data appear corrupted prior to any of the processing steps (tweak or drizzle/resample), try redownloading your images. If you are using the `MAST <https://mast.stsci.edu>`_ batch retrieval, consider using the browser download, which may be more reliable.

2. **Roman hasn't launched yet; how do I access data to play with spike.psf.roman?**

There are a lot of different groups dedicated to simulating data for the Roman Space Telescope. `Troxel et al. (2023) <https://ui.adsabs.harvard.edu/abs/2023MNRAS.522.2801T/abstract>`_ has some nice examples of single detector data and you can generate your own Roman imaging with `STIPS <https://github.com/spacetelescope/STScI-STIPS>`_ (`STIPS Development Team 2024 <https://ui.adsabs.harvard.edu/abs/2024arXiv241111978S/abstract>`_) The pipeline is very similar to JWST's, with the notable exception that the image from each of the detectors is stored in its own file, so ``spike.psf.roman`` is, at its core, a modified version of ``spike.psf.jwst``.


spike
-----

1. **Why am I getting 'NameResolveError: Unable to find coordinates for name ...' when I feed spike.psf an object name?**

The most likely reason you'd get this sort of error is that the object name is not resolvable by NED. Providing coordinates will allow ``spike`` to proceed. If searching for that name generally works, I have found that sometimes (perhaps due to updates on the CDS side of things?) searches that have worked in the past will temporarily return an error. In that case, you can either wait a bit and try again with a name search or you can provide the coordinates yourself to run `spike` immediately.

2. **I am encountering a problem with one of the pipeline modules (spike.jwstcal, spike.romancal, or spike.stcal). How much has changed from the official Space Telescope release?**

Each of ``spike.jwstcal``, ``spike.romancal``, and ``spike.stcal`` are subtly reworked versions of the STScI releases. Since namespace packages aren not enabled (and would not be workable with the many interlocking dependencies) for ``jwst`` and ``romancal``, the relevant portions of the JWST and Roman pipelines are installed directly with ``spike`` with pared down dependencies and install requirements. The code has been reorganized and reworked to have a more straightforward file structure and get rid of dependencies that are extraneous for the tweak and resample pipeline steps, so none of the scientific functionality has been changed. 

If your seems to come from one of these modules, you can always start with the `jwst <https://jwst-pipeline.readthedocs.io/en/latest/>`_ or `romancal <https://roman-pipeline.readthedocs.io/en/latest/>`_ documentation to better understand the problem. Most interaction with these pipeline commands is through other ``spike`` functions, though, so it will also serve to toggle ``verbose = True`` and confirm that all prior steps are proceeding as expected (confirming the outputs look as you expect may help, as well). If the problem actually occurs at an intermediate step and the pipeline error is due to missing inputs, you can fix this by resolving the concern with that intermediate step (see the `spike documentation <https://spike-psf.readthedocs.io>`_ or the other FAQ sections).

If you encounter a bug that ultimately traces back to ``spike.jwstcal``, ``spike.romancal``, or ``spike.stcal``, and you would like to open an issue, please tag your issue with the "pipeline" label. 

3. **I'm encountering an AttributeError when I enable parallelization and define my own function to generate PSFs. How do I fix this?**

As it turns out, ``multiprocessing`` specifically requires that functions be *imported*. It is possible that you will have to create a dummy script that houses your custom PSF generation function. There's a good example of this on `StackOverflow <https://stackoverflow.com/a/42383397>`_.


TinyTim
-------

If you plan to use TinyTim PSFs (for HST), TinyTim must be downloaded and installed separately following the instructions `here <https://github.com/spacetelescope/tinytim/releases>`_. 

1. **Why does tiny1 result in a path error ('Open_pupil_table : Could not open ~/tinytim-7.5/\*.pup')?**

First, confirm that the .pup file actually exists in your tinytim-7.5 directory. Assuming it does, this error is likely due to the syntax you used to set your `$TINYTIM` path variable. For bash shells, the quick fix should be to swap out '\~/' with an absolute path like '/Users/username/'.

2. **Why am I getting an HTTPS error when my PSF generation method is 'TinyTim_Gillis'?**

If you don't already have the `Gillis et al. (2020) <https://bitbucket.org/brgillis/tinytim_psfs/src/master/>`_ code downloaded, the first thing that ``spike.psfgen`` tries to do is download the relevant script. An HTTPS error may come about if BitBucket is down or if there's a problem with your connection. If you have the Gillis et al. script downloaded locally, simply copy it to your working directory and the issue should resolve.


STDPSF
------

1. **Why am I getting an HTTPS error when my PSF generation method is 'STDPSF'?**

There are two points of potential failure here -- if you don't already have the `handling script <https://github.com/spacetelescope/hst_notebooks/blob/main/notebooks/WFC3/point_spread_function/>`_ downloaded locally, it's possible that GitHub is down or there's a problem with your connection; similarly, the STDPSFs are downloaded as needed, so there could also be an issue connecting to the `Space Telescope website <https://www.stsci.edu/~jayander/HST1PASS/LIB/PSFs/STDPSFs/>`_. If you already have psf_utilities.py downloaded locally, copying that script into your working directory should resolve an inability to connect to GitHub, as the code will preferentially use your local version.


PSFEx
-----

If you plan to use PSFEx to generate empirical PSFs, both SExtractor and PSFEx must be downloaded and installed separately following the instructions `here <https://github.com/astromatic/sextractor>`_ and `here <https://github.com/astromatic/psfex>`_ respectively.

Some notes on PSFEx/SExtractor installation for Macs: You can use ``brew install automake, libtool`` to add the GNU functions that PSFEx requires for installation. If FFTW is not already installed on your machine, you will need to follow the instructions for both single- and double-point versions (see these `instructions <http://www.fftw.org/fftw2_doc/fftw_6.html#SEC69>`_). If ATLAS is not already installed, you can bypass that installation altogether by downloading and installing OpenBLAS. Even with a successful install, my experience was that PSFEx could not find the correct directories, so in your PSFEx directory, you will want to run some variation of ``./configure --enable-openblas --with-openblas-incdir=/opt/OpenBLAS/include --with-openblas-libdir=/opt/OpenBLAS/lib
`` when configuring the Makefile for PSFEx.

There is also a bug in the PSFEx installation code -- discussed nicely `here <https://trac.macports.org/ticket/71003>`_ -- within PSFEx/src/levmar/compiler.h, you will need to change "finite" to "isfinite" before attempting to run ``make``.

1. **My output single-image PSFs look funny/there's an issue with my SExtractor catalog. How do I fix this?**

The first step if you aren't happy with your PSFEx output is to try adjusting the SExtractor and PSFEx parameters in their respective config files. ``spike.psfgen`` uses the default settings for each of these codes unless an overriding user input is specified. As a result, the star catalog and subsequent PSF generation are not fine-tuned for any specific use case.

Within spike/configs, there are example configuration and parameter files for PSFEx and SExtractor. These can be used as guides and can be *copied* and directly modified. (I recommend against modifying any of the files in spike/configs themselves unless you are interested in making global changes.)


WebbPSF
-------

If you plan to use WebbPSF PSFs (for JWST and Roman), the relevant data must be downloaded and included in your path following the instructions `here <https://webbpsf.readthedocs.io/en/latest/installation.html#data-install>`_.




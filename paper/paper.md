___
title: 'spike: A tool to drizzle _HST_, _JWST_, and Roman PSFs for improved analyses'
tags:
  - Python
  - astronomy
  - point spread functions
  - photometry
authors:
  - name: Ava Polzin
    orcid: 0000-0002-5283-933X
    corresponding = True
    affiliation: "1" # (Multiple affiliations must be quoted)
affiliations:
 - name: Department of Astronomy and Astrophysics, The University of Chicago, USA
   index: 1
date: 13 September 2024
bibliography: paper.bib
___

# Summary

Point spread functions (PSFs) describe the distribution of light for a pure point source in an astronomical image due to the instrument optics. For deconvolution, as for point source photometry and for source removal, it is key to have an accurate PSF for a particular image. Space-based telescopes can then pose a challenge as their PSFs are informed by their complex construction, geometric distortions on the detectors themselves, and the myriad of pointings and rotations used to capture deep images. These telescopes also capture the highest resolution images of astronomical sources, resolving stars around even relatively distant galaxies. Proper co-addition of PSFs at a specific source position for space-based imaging is then both critical and challenging. This code, `spike`, takes in model PSFs and runs them through the same processing pipeline used to derive deep, co-added images, providing correctly co-added PSFs for images from the _Hubble Space Telescope_, the _James Webb Space Telescope_, and the Nancy Grace Roman Space Telescope. 


# Statement of Need

The PSF of co-added images is of generic interest to both ground- and space-based instruments, as it can be impacted by differing co-addition schemes and may have an effect on the analysis of those data [@Mandelbaum.etal.2023]. The cumulative effect of the geometric distortions and offsets in angle and pixel location of space-based data are apparent in the effective PSF of the co-added and resampled (drizzled; CITE) image, making a PSF modeled on uncombined images insufficient for careful photometric analyses. This is a recognized limitation of existing PSF models, and `DrizzlePac` recently added functionality to use drizzled pre-computed model PSFs in their native photometric catalog generator [@DrizzlePac3.3.0]. This drizzled PSF uses generic `TinyTim` [@Krist.etal.2011] models, which do not account for source position on the chip and do not allow the user to set model parameters without overwriting the existing grid of model PSFs. Simultaneously, the resultant co-added PSF is not output, and there is not an existing, simple way to generate drizzled PSFs for use in other analyses. Instead, an empirical PSF may be taken from the data or unsaturated stars near the object of interest may be selected as an proxy for the PSF. For particularly crowded fields, or those where most stars are saturated, these alternatives pose a real problem.

For analyses to be consistent, mock PSFs may be used, but the proper treatment of them involves generating model PSFs and then co-adding them in the same way as the parent images are co-added. Given the number of steps between the selection of an object and the creation of a cumulative mock PSF in the region of that object, it can be onerous to generate "realistic" PSFs for application to data. The code presented here, `spike`, streamlines the process, taking images and coordinates and directly outputting correctly co-added model PSFs for either the _Hubble Space Telescope_, the _James Webb Space Telescope_, or the upcoming Nancy Grace Roman Space Telescope. Model PSFs can be generated using different industry-standard packages, including `TinyTim` [@Krist.etal.2011] and `WebbPSF` [@Perrin.etal.2012; @Perrin.etal.2014; @Perrin_WebbPSF], or users can provide model PSFs associated with individual images. As a result, `spike` is both easy to use and flexible. 

# Workflow

The premise of `spike` is that, given reduced, but not yet co-added, .fits files from _HST_, _JWST_, or _Roman_ and the coordinates of an object of interest, detector/chip-specifc model PSFs themselves can be directly "drizzled". The code can be run using images that have been "tweaked" or images that have not yet undergone any `astrodrizzle` post-processing.

The package relies on `astropy`[@AstropyCollaboration.2013; @AstropyCollaboration.2018; @AstropyCollaboration.2022] for conversion of objects' astronomical coordinates (in right ascension and declination) to pixel coordinates (in X, Y), using the images' world coordinate system information. A model PSF is then generated for each unique input image and coordinates combination. Instrument information, including camera, filter, and, if necessary, chip, is automatically read directly from the header of each .fits file by default, but can be overridden by user choice. Similarly, users can generate PSF models using pre-defined defaults, update model parameters, or upload their own model PSFs to be drizzled.

Though a generic empirical PSF can be computed from the drizzled image, `spike` includes the ability for users to generate and drizzle empirical PSFs via a number of different codes. Computation of these PSFs may require more user input (such as selecting good stars for which to measure light profiles) and may take more time. The empirical models included here are chosen for relevance to high-resolution space-based data; user-generated PSFs from other tools may be used with `spike.psf`, but are not shipped as part of `spike.psfgen`.

In most cases, users will only ever interact with the top-level functions `spike.psf.hst`, `spike.psf.jwst`, and `spike.psf.roman`. However, PSF model creation can be accessed directly via the functions in `spike.psfgen`, and this feature may be of added value to users on its own, as `spike` smoothes over some of the complication of individual tools as an all-in-one means of accessing model PSFs via simple Python functions.

`spike` is also parallelized for use with large sets of coordinates using `multiprocess`, and the option to run the code in parallel is togglable. 

In addition to .fits outputs, users can specify whether they would like a .asdf file returned, too, and it is possible to write .png images of the individual PSF models and the final co-add, which allows users to do quick visual inspection.


# Preparation for Future Observatories

Right now, the Roman pipeline uses the same drizzling implementation as _JWST_, and `WebbPSF` includes a module to simulate Roman PSFs. As a forward looking step, a module is included here to handle the proper co-addition of Roman PSFs. The `spike.psf.roman` module does not include a separate step for subpixel alignment, as has been done for _HST_ and _JWST_ by "tweaking" images. Instead, model Roman PSFs are directly drizzled. When the observatory is actually launched and data become available, `spike` will be updated to reflect the most current version of the Nancy Grace Roman Space Telescope pipeline. Due to the anticipated single pointing file size, `spike.psf.roman` takes as input a dictionary containing pixel locations, filters, etc. which are used with `spike.psfgen`. Convenience functions are provided to derive these quantities from images. Since Roman is not yet collecting data, all testing has been done on simulated data from CITE.

Raw data are not yet available for the European Space Agency's _Euclid_ mission, which was launched in 2023. Initial analyses of the combined and processed _Euclid_ Early Release Observations rely on empirical PSFs, carefully measured from co-added data CITE. A new _Euclid_ function will be added to `spike` as data and PSF modeling tools become available over the next years. Proper PSF co-addition is of particular importance to _Euclid_ to enable carefully calibrated measurements of cosmic shear. 

# Software and Packages Used
 - `astropy` [@AstropyCollaboration.2013; @AstropyCollaboration.2018; @AstropyCollaboration.2022]
 - `drizzlepac` [@Hoffmann.etal.2021]
 - `matplotlib` [@Hunter.2007]
 - `numpy` [@harris2020array]
 - `photutils` [@Bradley.etal]
 - `PSFEx` [@Bertin.2011; @Bertin.2013]
 - `SExtractor` [@Bertin.Arnauts.1996]
 - `TinyTim` [@Krist.etal.2011] -- including the option to use the @Gillis.etal.2020 parameters [@Gillis.2019]
 - `webbpsf` [@@Perrin.etal.2012; @Perrin.etal.2014; @Perrin_WebbPSF]

# Acknowledgments

AP is supported by the Quad Fellowship administered by IIE.



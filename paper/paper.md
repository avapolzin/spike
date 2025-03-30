---
title: '`spike`: A tool to drizzle _HST_, _JWST_, and Roman PSFs for improved analyses'
tags:
  - Python
  - astronomy
  - point spread functions
  - photometry
authors:
  - name: Ava Polzin
    orcid: 0000-0002-5283-933X
    corresponding: true
    affiliation: 1
affiliations:
 - name: Department of Astronomy and Astrophysics, The University of Chicago, USA
   index: 1
date: 5 December 2024
bibliography: paper.bib
---

# Summary

Point spread functions (PSFs) describe the distribution of light for a pure point source in an astronomical image due to the instrument optics. For deconvolution, as for point source photometry and for source removal, it is key to have an accurate PSF for a particular image. Space-based telescopes can then pose a challenge as their PSFs are informed by their complex construction, and the myriad of pointings and rotations used to capture deep images. These telescopes also capture the highest resolution images of astronomical sources, resolving stars around even relatively distant galaxies. Proper co-addition of PSFs at a specific source position for space-based imaging is then both critical and challenging. This code, `spike`, generates model PSFs and runs them through the same processing pipeline used to derive deep, co-added images, providing correctly co-added and resampled PSFs for images from the _Hubble Space Telescope_, the _James Webb Space Telescope_, and the Nancy Grace Roman Space Telescope. 


# Statement of Need

The PSF of co-added images is of generic interest to both ground- and space-based instruments, as it can be impacted by differing co-addition schemes and may have an effect on the analysis of those data [@Mandelbaum.etal.2023]. The cumulative effect of the geometric distortions and offsets in angle and pixel location of space-based data are apparent in the effective PSF of the co-added and resampled [drizzled, @Fruchter.Hook.2002] image, making a PSF modeled on uncombined images insufficient for careful photometric analyses. This is a recognized limitation of existing PSF models, and `DrizzlePac` recently added functionality to use drizzled pre-computed model PSFs in their native photometric catalog generator [@DrizzlePac3.3.0]. This drizzled PSF uses generic `TinyTim` [@Krist.etal.2011] models, which do not account for source position on the chip and do not allow the user to set model parameters without overwriting the existing grid of model PSFs. Simultaneously, the resultant co-added PSF is not output, and there is not an existing, simple way to generate drizzled PSFs for use in other analyses. Instead, an empirical PSF may be taken from the data or unsaturated stars near the object of interest may be selected as an proxy for the PSF. For particularly crowded fields, or those where most stars are saturated, these alternatives pose a real problem.

For analyses to be consistent, mock PSFs may be used, but the proper treatment of them involves generating model PSFs and then co-adding and processing them in the same way as the parent images are co-added and processed. Workflows have been created for some instruments, [^1] and individual packages have tried to address this in their own data handling, with e.g.,  `Grizli` [@Brammer_grizli] returning drizzled standard empirical PSFs, but, similar to the drizzled PSFs computed by `DrizzlePac`, such solutions leave little room for users to define the method or specifics of model PSF generation. Given the number of steps between the selection of an object and the creation of a cumulative mock PSF in the region of that object, it can be onerous to generate "realistic" PSFs for application to data. The code presented here, `spike`, streamlines the process, taking images and coordinates and directly outputting correctly co-added model PSFs for the _Hubble Space Telescope_ (_HST_), the _James Webb Space Telescope_ (_JWST_), and the upcoming Nancy Grace Roman Space Telescope. Model PSFs can be generated using different industry-standard packages, including `TinyTim` [@Krist.etal.2011] and `WebbPSF` [@Perrin.etal.2012; @Perrin.etal.2014; @Perrin_WebbPSF], empirical PSFs can be computed from input images, or users can provide model PSFs associated with the individual images. The code is designed to work with any calibrated space telescope imaging. As a result, `spike` [^2] is both easy to use and flexible. 

[^1]: <https://github.com/spacetelescope/hst_notebooks/tree/main/notebooks/WFC3/point_spread_function>; <https://github.com/spacetelescope/wfc3_photometry>
[^2]: <https://github.com/avapolzin/spike>

# Workflow

The premise of `spike` is that, given a directory containing reduced and calibrated, but not yet co-added, .fits files from _HST_, _JWST_, or Roman and the coordinates of an object of interest, detector/chip-specifc model PSFs themselves can be directly "drizzled". The code can be run using images that have been "tweaked" or images that have not yet undergone any resampling or post-processing.

The package relies on `astropy` [@AstropyCollaboration.2013; @AstropyCollaboration.2018; @AstropyCollaboration.2022] for conversion of objects' astronomical coordinates (in right ascension and declination) to pixel coordinates (in X, Y), using the images' world coordinate system information. A model PSF is then generated for each unique input image and coordinates combination. Instrument information, including camera, filter, and, if necessary, chip, is automatically read directly from the header of each .fits file by default, but can be overridden by user choice. Similarly, users can generate PSF models using pre-defined defaults, update model parameters, or upload their own model PSFs to be drizzled.

Though a generic empirical PSF can be computed from the drizzled image, `spike` includes the ability for users to generate and drizzle empirical PSFs via a number of different codes. Computation of these PSFs may require more user input (such as selecting good stars for which to measure light profiles) and may take more time. The empirical models included here are chosen for relevance to high-resolution space-based data; user-generated PSFs from other tools may be used with `spike.psf`, but are not shipped as part of `spike.psfgen`.

![Comparison of drizzled PSFs generated for _HST_ images using the default parameters for different methods included in `spike`. All panels use the same ACS/WFC imaging of the COSMOS field in F475W. Note that the ePSF panel (second from right) shows some artifacts; the robustness of the effective PSF method is heavily dependent on the number of stars in the chosen field and may be changed by altering the star detection threshold. \label{fig:hstcomparison}](spike_psf_hstcompare.png)

The built-in PSF generation options are `TinyTim` [@Krist.etal.2011] and the @Gillis.etal.2020 modification [@Gillis.2019], `WebbPSF` [@Perrin.etal.2012; @Perrin.etal.2014; @Perrin_WebbPSF], `photutils` effective PSFs [@Anderson.King.2000; @Anderson.2016; @Bradley.etal], `PSFEx` [@Bertin.2011; @Bertin.2013], and Space Telescope Science Institute's library of empirical STDPSFs [^3] [@Anderson.2016; @Libralato.etal.2023; @Libralato.etal.2024], all of which are included for having the ability to generate a model PSF for an arbitrary detector location. \autoref{fig:hstcomparison} compares output drizzled PSFs from the different methods for _HST_ and \autoref{fig:jwstcomparison} compares output drizzled PSFs for _JWST_. 

[^3]: <https://www.stsci.edu/~jayander/HST1PASS/LIB/PSFs/STDPSFs/>; <https://www.stsci.edu/~jayander/JWST1PASS/LIB/PSFs/STDPSFs/>

![Same as \autoref{fig:hstcomparison} for \textit{JWST}/NIRCam imaging in F115W. Note that the ePSF model shown here was generated using a lower detection threshold and a different star selection algorithm due to a paucity of stars in this field. \label{fig:jwstcomparison}](spike_psf_jwstcompare.png)

In most cases, users will only ever interact with the top-level functions `spike.psf.hst`, `spike.psf.jwst`, and `spike.psf.roman`. However, PSF model creation can be accessed directly via the functions in `spike.psfgen`, and this feature may be of added value to users on its own, including for use with telescopes/instruments not explicitly mentioned here, as `spike` smoothes over some of the complication of individual tools as an all-in-one means of accessing model PSFs via simple Python functions. One can, in principle, specify only minimal information (data directory, object name/coordinates, instrument/camera, and PSF generation method) and return a drizzled PSF from the default remaining default settings/arguments.


# Preparation for Future Observatories

When the Nancy Grace Roman Space Telescope is launched and data become available, `spike` will be updated to reflect the most current version of the pipeline and the detailed considerations of the real data. `spike.psf.roman` currently takes as input single detector images, which can be used with `spike.psfgen` -- the working directory need not be local; it just needs to have read/write access. Since Roman is not yet collecting data, `spike.psf.roman` is based on the structure of simulated single detector data from [e.g., @Troxel.etal.2023].


# Managing Restrictive Dependencies

Since drizzled `spike` PSFs are intended for use with calibrated and resampled data products from these original pipelines, it is imperative that the processing done on the PSFs is the same as the processing of those data products. Both `jwst` [@Bushouse.etal.2024] and `romancal` [@romancal] are complex packages that house the entire _James Webb Space Telescope_ and Nancy Grace Roman Space Telescope pipelines. As such, they have complicated functionality that relies on modules with more stringent installation requirements. Using `jwst` and `romancal` out of the box places strict limitations on the allowed operating systems. To address this, making `spike` more flexible, there are stripped down versions of the necessary "tweak" and resample scripts included with `spike` as `spike.jwstcal`, `spike.romancal`, `spike.stcal`, and `spike.stpipe`. Each module is only subtly changed from `jwst`, `romancal`, and their underlying `STCAL` [@stcal] and `stpipe` [@stpipe] to avoid unnecessary dependencies that restrict installation.

# Software and Packages Used
 - `asdf` [@graham.etal]
 - `astropy` [@AstropyCollaboration.2013; @AstropyCollaboration.2018; @AstropyCollaboration.2022]
 - `crds` [@crds]
 - `drizzle` [@Simon.etal.2024]
 - `drizzlepac` [@Hoffmann.etal.2021]
 - `gwcs` [@Dencheva.etal]
 - `jsonschema` [@jsonschema]
 - `jwst` [@Bushouse.etal.2024]
 - `matplotlib` [@Hunter.2007]
 - `numpy` [@harris2020array]
 - `photutils` [@Bradley.etal]
 - `PSFEx` [@Bertin.2011; @Bertin.2013]
 - `psutil` [@psutil]
 - `PyYAML` [@pyyaml]
 - `roman_datamodels` [@roman_datamodels]
 - `romancal` [@romancal]
 - `scipy` [@2020SciPy-NMeth]
 - `SExtractor` [@Bertin.Arnouts.1996]
 - `spherical_geometry` [@spherical_geometry]
 - `STCAL` [@stcal]
 - `stdatamodels` [@stdatamodels]
 - `stpipe` [@stpipe]
 - `TinyTim` [@Krist.etal.2011] -- including the option to use the @Gillis.etal.2020 parameters [@Gillis.2019]
 - `tweakwcs` [@cara.etal]
 - `WebbPSF` [@Perrin.etal.2012; @Perrin.etal.2014; @Perrin_WebbPSF]

# Acknowledgments

AP is supported by the Quad Fellowship administered by IIE and thanks Hsiao-Wen Chen and Juan Guerra for their comments. This work makes use of observations made with the NASA/ESA Hubble Space Telescope and the NASA/ESA/CSA James Webb Space Telescope obtained from the Mikulski Archive for Space Telescopes at the Space Telescope Science Institute, which is operated by the Association of Universities for Research in Astronomy, Inc., under NASA contract NAS 5–26555 for HST and NASA contract NAS 5-03127 for JWST.


# References

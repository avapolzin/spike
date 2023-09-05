___
title: 'spike: A tool to drizzle _HST_ and _JWST_ PSFs for improved analyses'
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
date: 20 June 2022
bibliography: paper.bib
___

# Summary

Point spread functions (PSFs) describe the 


# Statement of Need

The PSF of co-added images is of generic interest to both ground- and space-based instruments, as it can be impacted by differing co-addition schemes and may have an effect on the analysis of those data [@Mandelbaum2023]. The cumulative effect of the geometric distortions and offsets in angle and pixel location of space-based data are apparent in the effective PSF of the drizzled image, making a PSF modeled on uncombined images insufficient for careful photometric analyses. This is a recognized limitation of existing PSF models, and `DrizzlePac` recently added functionality to use drizzled PSFs in their native photometric catalog generator [@DrizzlePac3.3.0]. This drizzled PSF is not output (CHECH THIS?!) and there is not an existing, simple way to generate drizzled PSFs for use in other analyses.


MAKE TINY.config with all of the general PSF parameters not including chip location etc


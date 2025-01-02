![spike_logo 004](https://github.com/user-attachments/assets/bc7dd19e-1fe8-4c06-ae36-3501b9aa8fc5)

All-in-one tool to generate, and correctly drizzle, _HST_, _JWST_, and Roman PSFs.

**Under construction -- come back in a couple of days!**

## Installation

To install:
```bash
cd ~

git clone https://github.com/avapolzin/spike.git

cd spike

sudo pip install .

````
or (which does not work yet because I need to figure out what to do with the c bindings and direct dependencies)
```bash
pip install spike-psf
```

*Note that `spike.psfgen.tinypsf` and `spike.psfgen.tinygillispsf` require `TinyTim` for simulated PSFs. To use that module, please download [`TinyTim` version 7.5](https://github.com/spacetelescope/tinytim/releases) and follow the install instructions. Since that software is now unmaintained, refer to the [STScI site](https://www.stsci.edu/hst/instrumentation/focus-and-pointing/focus/tiny-tim-hst-psf-modeling) for details and caveats.*

*If you plan to use the `PSFEx` empirical PSF modeling, that will similarly need to be downloaded from the [GitHub repository](https://github.com/astromatic/psfex) and installed, as will [`SExtractor`](https://github.com/astromatic/sextractor).*

*If you are using `WebbPSF`, you will need to install the relevant data and include it in your path. Instructions to do this are available [here](https://webbpsf.readthedocs.io/en/latest/installation.html#data-install).*


## Getting Started

To get a drizzled PSF, ...

fairly simple and can require as little as a working directory for images and the coordinates of an object of interest.


Ultimately, some of the other functions included in `spike`, may be useful. For instance, the functions in `spike.psfgen` are methods to compute and save (to .fits) various model PSFs for a variety of telescopes/instruments which share similar syntax and required inputs and are callable from python directly. Similarly, `spike.tools` houses generic functions, which may be broadly applicable, including a python wrapper for `SExtractor` (not to be confused with `sep`), a utility to convert between `PSFEx` .psf files and images, and a means of rewriting FITS files to an ASDF format. Please refer to [spike-psf.readthedocs.io](https://spike-psf.readthedocs.io) for details.

## Testing `spike`

Since `spike` has utility for working with data, the most useful test of the code is to actually generate and drizzle PSFs from imaging. The code to generate Figures 1 and 2 from Polzin in prep is in test_outputs.py, which can be used to confirm the package works. Note that the input file structure is such that each instrument's data should be partitioned in its own directory, where all included data may be included in the final drizzled product. 

An example file structure:

*working_directory*
- test_outputs.py
- *acswfc_imaging*
- *wfc3uvis_imaging*
- *wfpc2_imaging*
- *nircam_imaging*
- *miri_imaging*
- *niriss_imaging*

test_outputs.py includes the information for the datasets used and can also serve as a guide for testing other data. Note that different user inputs may be required based on data used (as for PSF generation and drizzling).

Data-independent utilities included in `spike` can be tested via the scripts included in the "tests" directory here. To run these tests follow the below steps from your locally installed `spike` directory.

```bash
pip install pytest #necessary if pytest is not installed or in your working environment
python3 -m pytest tests/tests.py
```

All tests should pass by default, *but, if you are not intending to use `spike` without `TinyTim`, `SExtractor`, `PSFEx`, or `WebbPSF` and do not have them installed, the final test may fail*. In that case, the arguments in 


## Issues and Contributing

If you encounter a bug, first check the [documatnation](https://spike-psf.readthedocs.io) or the [FAQ](https://github.com/avapolzin/spike/blob/master/FAQ.md); if you don't find a solution there, please feel free to open an issue (or a PR with a fix). If you have a question, please feel free to email me at apolzin at uchicago dot edu.

If you would like to contribute to `spike`, either enhancing what already exists here or working to add features (as for other telescopes/PSF models), please make a pull request. If you are unsure of how your enhancement will work with the existing code, reach out and we can discuss it.
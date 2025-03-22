![spike_logo 004](https://github.com/user-attachments/assets/bc7dd19e-1fe8-4c06-ae36-3501b9aa8fc5)

[![Documentation Status](https://readthedocs.org/projects/spike-psf/badge/?version=latest)](https://spike-psf.readthedocs.io/en/latest/?badge=latest) [![arXiv](https://img.shields.io/badge/arXiv-2503.02288-b31b1b)](https://arxiv.org/abs/2503.02288) [![status](https://joss.theoj.org/papers/744ad03a43040debb962391d1668ea5c/status.svg)](https://joss.theoj.org/papers/744ad03a43040debb962391d1668ea5c)

All-in-one tool to generate, and correctly drizzle, _HST_, _JWST_, and Roman PSFs.

## Installation

To install:
```bash
cd ~

git clone https://github.com/avapolzin/spike.git

cd spike

pip install .

````
or 
```bash
pip install spike-psf
```

If you install from PyPI, you will also need to install `DrizzlePac` from the [GitHub distribution](https://github.com/spacetelescope/drizzlepac.git).

*Note that `spike.psfgen.tinypsf` and `spike.psfgen.tinygillispsf` require `TinyTim` for simulated PSFs. To use that module, please download [`TinyTim` version 7.5](https://github.com/spacetelescope/tinytim/releases) and follow the install instructions. Since that software is now unmaintained, refer to the [STScI site](https://www.stsci.edu/hst/instrumentation/focus-and-pointing/focus/tiny-tim-hst-psf-modeling) for details and caveats.*

*If you plan to use the `PSFEx` empirical PSF modeling, that will similarly need to be downloaded from the [GitHub repository](https://github.com/astromatic/psfex) and installed, as will [`SExtractor`](https://github.com/astromatic/sextractor).*

*If you are using `WebbPSF`, you will need to install the relevant data and include it in your path. Instructions to do this are available [here](https://webbpsf.readthedocs.io/en/latest/installation.html#data-install).*

*The `jwst` and `romancal` pipelines -- which house the tweak/resample steps for JWST and Roman -- require the setup of CRDS_PATH and CRDS_SERVER_URL environment variables. The amended version of the code also relies on `crds`, so it is necessary to set these environment variables according to the instructions [here](https://jwst-pipeline.readthedocs.io/en/latest/jwst/user_documentation/reference_files_crds.html) if you plan to use `spike` with JWST or Roman data.*

If you install all of the optional dependencies described above, your shell's startup file will look something like:

``` bash

export TINYTIM="/path/to/tinytim-7.5"
alias tiny1="$TINYTIM/tiny1"
alias tiny2="$TINYTIM/tiny2"
alias tiny3="$TINYTIM/tiny3"

export WEBBPSF_PATH="/path/to/webbpsf-data"

export CRDS_PATH="/path/to/crds_cache/"
# export CRDS_SERVER_URL="https://jwst-crds.stsci.edu"
# export CRDS_SERVER_URL="https://roman-crds.stsci.edu"
```

Since both JWST and Roman CRDS servers may be defined, these variables are added directly within `spike.jwstcal` and `spike.romancal` and do not need to be added to your startup file. 


## Getting Started

To get a drizzled PSF, only minimal inputs are required:

``` python

from spike import psf

acs_path = '/path/to/acs/data/'

psf.hst(img_dir = acs_path, obj = 'M79', img_type = 'flc', inst = 'ACS', camera = 'WFC')


nircam_path = 'path/to/nircam/data/'

psf.jwst(img_dir = nircam_path, obj = 'M79', img_type = 'cal', inst = 'NIRCam')

```

`spike` is intended to be fairly simple and can require as little as a working directory for images, the coordinates of an object of interest (where the PSF will be generated), the suffix used to identify relevant data (e.g., 'flc', crf', 'cal'), and the instrument used to take the data. For ACS and WFC3, a camera should also be specified. `spike` handles filter and detector/chip identification automatically, and the default parameters are sufficient to produce PSFs in most cases. The top-level functions `spike.psf.hst`, `spike.psf.jwst`, and `spike.psf.roman` also take a number of keyword arguments that allow for near-complete customization of the generated PSFs.


Ultimately, some of the other functions included in `spike` may be useful. For instance, the functions in `spike.psfgen` are methods to compute and save (to .fits) various model PSFs for a variety of telescopes/instruments which share similar syntax and required inputs and are callable from python directly. Similarly, `spike.tools` houses generic functions, which may be broadly applicable, including a python wrapper for `SExtractor` (not to be confused with `sep`), a utility to convert `PSFEx` .psf files to images, and a means of rewriting FITS files to an ASDF format. Please refer to [spike-psf.readthedocs.io](https://spike-psf.readthedocs.io) for details.

## Testing `spike`

Since `spike` has utility for working with data, the most useful test of the code is to actually generate and drizzle PSFs from imaging. The code to generate Figures 1 and 2 from [Polzin (2025)](https://arxiv.org/abs/2503.02288) is in tests/test_outputs.py, which can be used to confirm the package works. Note that the input file structure is such that each instrument's data should be partitioned in its own directory, where all included data may be part of the final drizzled product. 

An example file structure:

*working_directory*
- test_outputs.py
- *acswfc_imaging*
- *wfc3uvis_imaging*
- *wfpc2_imaging*
- *nircam_imaging*
- *miri_imaging*
- *niriss_imaging*

test_outputs.py includes the information for the datasets used and can also serve as a guide for testing other data. Note that different user inputs may be required based on data used (as for PSF generation and drizzling). Each run generates quite a few files, so I recommend moving test_outputs.py into its own directory rather than running it in the cloned `spike` one.

Data-independent utilities included in `spike` can be tested via the scripts included in the "tests" directory here. To run these tests follow the below steps from your locally installed `spike` directory.

```bash
pip install pytest #necessary if pytest is not installed or in your working environment
python -m pytest tests/tests.py
```

All tests should pass by default.


## Issues and Contributing

If you encounter a bug, first check the [documentation](https://spike-psf.readthedocs.io) or the [FAQ](https://github.com/avapolzin/spike/blob/master/FAQ.md); if you don't find a solution there, please feel free to open an issue that details what you ran and what error you are encountering (or a PR with a fix). If you have a question, please feel free to email me at apolzin at uchicago dot edu.

If you would like to contribute to `spike`, either enhancing what already exists here or working to add features (as for other telescopes/PSF models), please make a pull request. If you are unsure of how your enhancement will work with the existing code, reach out and we can discuss it.

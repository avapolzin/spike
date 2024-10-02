![spike_logo 004](https://github.com/user-attachments/assets/bc7dd19e-1fe8-4c06-ae36-3501b9aa8fc5)

All-in-one tool to generate and correctly drizzle _HST_, _JWST_, and Roman PSFs.

## Installation

To install:
```bash
cd ~

git clone https://github.com/avapolzin/spike.git

cd spike

sudo python3 setupy.py install

````
or (which does not work yet because I need to figure out the c bindings...)
```bash
pip install spike-psf
```

*Note that `spike.psfgen.tinypsf` and `spike.psfgen.tinygillispsf` require `TinyTim` for simulated PSFs. To use that module, please download [`TinyTim` version 7.5](https://github.com/spacetelescope/tinytim/releases) and follow the install instructions. Since that software is now unmaintained, we refer to the STScI [site](https://www.stsci.edu/hst/instrumentation/focus-and-pointing/focus/tiny-tim-hst-psf-modeling) for details and caveats.*

*If you plan to use the `PSFEx` empirical PSF modeling, that will similarly need to be downloaded from the [GitHub repository](https://github.com/astromatic/psfex) and installed, as will [`SExtractor`](https://github.com/astromatic/sextractor).*

## Getting Started

To get a drizzled PSF, ...

fairly simple and can require as little as a working directory for images and the coordinates of an object of interest.


Ultimately, some of the other functions included in `spike`, may be useful. For instance, the functions in `spike.psfgen` are methods to compute and save (to .fits) various model PSFs for a variety of telescopes/instruments which share similar syntax and required inputs and are callable from python directly. Similarly, `spike.tools` houses generic functions, which may be broadly applicable, including a python wrapper for `SExtractor` (not to be confused with `sep`). Please refer to [spike.readthedocs.io](https://spike.readthedocs.io) for details.

## Issues and Contributing

If you encounter a bug, please feel free to open an issue or a PR. If you have a question, please feel free to email me at apolzin at uchicago dot edu.

If you would like to contribute to `spike`, either enhancing what already exists here or working to add features (as for other telescopes/PSF models), please make a pull request. If you are unsure of how your enhancement will work with the existing code, reach out and we can discuss it.
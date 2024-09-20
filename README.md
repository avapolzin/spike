![spike_logo 004](https://github.com/user-attachments/assets/bc7dd19e-1fe8-4c06-ae36-3501b9aa8fc5)

Tool to generate correctly drizzled _HST_, _JWST_, and Roman PSFs, accounting for geometric corrections.

## Installation

To install:
```bash
cd ~

git clone git@github.com:avapolzin/spike.git

cd spike

sudo python3 setupy.py install

````
or (which does not work yet because I need to figure out the c bindings...)
```bash
pip install spike
```

*Note that `spike.psfgen.tinypsf` and `spike.psfgen.tinygillispsf` require `TinyTim` for simulated PSFs. To use that module, please download [`TinyTim` version 7.5](https://github.com/spacetelescope/tinytim/releases) and follow the install instructions. Since this software is now unmaintained, we refer to the STScI [site](https://www.stsci.edu/hst/instrumentation/focus-and-pointing/focus/tiny-tim-hst-psf-modeling) for details and caveats.*

*If you plan to use the `PSFEx` empirical PSF modeling, that will similarly need to be downloaded from the [GitHub repository](https://github.com/astromatic/psfex) and installed, as will [`SExtractor`](https://github.com/astromatic/sextractor).*
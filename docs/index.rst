.. image:: images/spike_logo.004.png

Easily generated and resampled space-based PSFs.
================================================

To install ``spike``, either ``pip install spike-psf`` or install the development version from the distribution on `GitHub <https://github.com/avapolzin/spike>`_.

Note that ``spike.psfgen.tinypsf`` and ``spike.psfgen.tinygillispsf`` require ``TinyTim`` for simulated PSFs. To use that module, please download `TinyTim version 7.5 <https://github.com/spacetelescope/tinytim/releases>`_ and follow the install instructions. Since that software is now unmaintained, refer to the `STScI site <https://www.stsci.edu/hst/instrumentation/focus-and-pointing/focus/tiny-tim-hst-psf-modeling>`_ for details and caveats.

If you plan to use the ``PSFEx`` empirical PSF modeling, that will similarly need to be downloaded from the `GitHub repository <https://github.com/astromatic/psfex>`_ and installed, as will `SExtractor <https://github.com/astromatic/sextractor>`_.

If you are using ``WebbPSF``, you will need to install the relevant data and include it in your path. Instructions to do this are available `here <https://webbpsf.readthedocs.io/en/latest/installation.html#data-install>`_.

.. toctree::
	:maxdepth: 1
	:caption: Contents:

	quickstart.rst
	psf.rst
	psfgen.rst
	tools.rst
	faq.rst
	citation.rst

For detailed questions related to the HST, JWST, or Roman calibration pipelines, or any of the individual PSF models, please refer to the original documentation for each software as it will be more comprehensive than what is offered here.

Some common questions related to the functionality of ``spike`` are also covered by the `FAQ <https://github.com/avapolzin/spike/blob/master/FAQ.md>`_. 

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
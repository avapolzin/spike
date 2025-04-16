.. image:: images/spike_logo.004.png

Easily generated and resampled space-based PSFs.
================================================
.. image:: https://readthedocs.org/projects/spike-psf/badge/?version=latest
    :target: https://spike-psf.readthedocs.io/en/latest/?badge=latest
.. image:: https://img.shields.io/badge/arXiv-2503.02288-b31b1b
    :target: https://arxiv.org/abs/2503.02288
.. image:: https://joss.theoj.org/papers/744ad03a43040debb962391d1668ea5c/status.svg
    :target: https://joss.theoj.org/papers/744ad03a43040debb962391d1668ea5c

To install ``spike``, either ``pip install spike-psf`` or install the development version from the distribution on `GitHub <https://github.com/avapolzin/spike>`_.

If you install ``spike`` via PyPI, you will need to separately install ``DrizzlePac`` from the distribution on `GitHub <https://github.com/spacetelescope/drizzlepac>`_, as PyPI does not handle direct dependencies.

Note that ``spike.psfgen.tinypsf`` and ``spike.psfgen.tinygillispsf`` require ``TinyTim`` for simulated PSFs. To use that module, please download `TinyTim version 7.5 <https://github.com/spacetelescope/tinytim/releases>`_ and follow the install instructions. Since that software is now unmaintained, refer to the `STScI site <https://www.stsci.edu/hst/instrumentation/focus-and-pointing/focus/tiny-tim-hst-psf-modeling>`_ for details and caveats.

If you plan to use the ``PSFEx`` empirical PSF modeling, that will similarly need to be downloaded from the `GitHub repository <https://github.com/astromatic/psfex>`_ and installed, as will `SExtractor <https://github.com/astromatic/sextractor>`_.

If you are using ``WebbPSF``, you will need to install the relevant data and include it in your path. Instructions to do this are available `here <https://webbpsf.readthedocs.io/en/latest/installation.html#data-install>`_.

The ``jwst`` and ``romancal`` pipelines -- which house the tweak/resample steps for JWST and Roman -- require the setup of the CRDS_PATH environment variable. The amended version of the code also relies on ``crds``, so it is necessary to set these environment variables according to the instructions `here <https://jwst-pipeline.readthedocs.io/en/latest/jwst/user_documentation/reference_files_crds.html>`_ if you plan to use ``spike`` with JWST or Roman data. 

If you install all of the optional dependencies described above, your shell's startup file will look something like:

.. code-block:: bash

	export TINYTIM="/path/to/tinytim-7.5"
	alias tiny1="$TINYTIM/tiny1"
	alias tiny2="$TINYTIM/tiny2"
	alias tiny3="$TINYTIM/tiny3"

	export WEBBPSF_PATH="/path/to/webbpsf-data"

	export CRDS_PATH="/path/to/crds_cache/"
	# export CRDS_SERVER_URL="https://jwst-crds.stsci.edu"
	# export CRDS_SERVER_URL="https://roman-crds.stsci.edu"

Since both JWST and Roman CRDS servers may be defined, these variables are added directly within ``spike.psf.jwst`` and ``spike.psf.roman`` and do not need to be added to your startup file.

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

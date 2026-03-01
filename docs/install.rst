.. _spike/install:

Installation & Setup
====================

Installation
------------

To install ``spike``, either ``pip install spike-psf`` or install the development version from the distribution on `GitHub <https://github.com/avapolzin/spike>`_:

.. code-block:: bash

	cd ~
	git clone https://github.com/avapolzin/spike.git
	cd spike
	pip install .

If you prefer to use the JWST and Roman pipeline steps directly from STScI (which do not explicitly support Windows computers), you should add the extras flag ``-e .[stdep]`` to your pip install command (e.g., ``pip install spike-psf -e .[stdep]``). This is currently an *experimental* option.

If you install ``spike`` via PyPI, you will need to separately install ``DrizzlePac`` from the distribution on `GitHub <https://github.com/spacetelescope/drizzlepac>`_, as PyPI does not handle direct dependencies.

To receive updates about ``spike``, including notice of improvements and bug fixes, please fill out `this form <https://forms.gle/q7oCeD7gdVeVTPuTA>`_ with your email.

Note that ``spike.psfgen.tinypsf`` and ``spike.psfgen.tinygillispsf`` require ``TinyTim`` for simulated PSFs. To use that module, please download `TinyTim version 7.5 <https://github.com/spacetelescope/tinytim/releases>`_ and follow the install instructions. Since that software is now unmaintained, refer to the `STScI site <https://www.stsci.edu/hst/instrumentation/focus-and-pointing/focus/tiny-tim-hst-psf-modeling>`_ for details and caveats.

If you plan to use the ``PSFEx`` empirical PSF modeling, that will similarly need to be downloaded from the `GitHub repository <https://github.com/astromatic/psfex>`_ and installed, as will `SExtractor <https://github.com/astromatic/sextractor>`_.

If you are using ``STPSF`` (formerly ``WebbPSF``), you will need to install the relevant data and include it in your path. Instructions to do this are available `here <https://stpsf.readthedocs.io/en/latest/installation.html>`_.

The ``jwst`` and ``romancal`` pipelines -- which house the tweak/resample steps for JWST and Roman -- require the setup of the CRDS_PATH environment variable. The amended version of the code also relies on ``crds``, so it is necessary to set these environment variables according to the instructions `here <https://jwst-pipeline.readthedocs.io/en/latest/jwst/user_documentation/reference_files_crds.html>`_ if you plan to use ``spike`` with JWST or Roman data. 

If you install all of the optional dependencies described above, your shell's startup file will look something like:

.. code-block:: bash

	export TINYTIM="/path/to/tinytim-7.5"
	alias tiny1="$TINYTIM/tiny1"
	alias tiny2="$TINYTIM/tiny2"
	alias tiny3="$TINYTIM/tiny3"

	# export WEBBPSF_PATH="/path/to/webbpsf-data"
	export STPSF_PATH="/path/to/STPSF-data"

	export CRDS_PATH="/path/to/crds_cache/"
	# export CRDS_SERVER_URL="https://jwst-crds.stsci.edu"
	# export CRDS_SERVER_URL="https://roman-crds.stsci.edu"

Since both JWST and Roman CRDS servers may be used, these variables are defined directly within ``spike.psf.jwst`` and ``spike.psf.roman`` and do not need to be added to your startup file. Similarly, ``spike`` does not require that the ``tiny1``, ``tiny2``, and ``tiny3`` aliases are set up, but most ``TinyTim`` users will want to add these to their startup file regardless.

Additionally, ``spike`` is written to be backwards compatible with ``WebbPSF`` installations.


Environments
------------

As with any specialized package, it is recommended that you install ``spike`` to a new environment, which will help avoid any conflict between its dependencies and any other packages that are already installed. 

To do this in conda, for example, simply run ``conda create -n spike``. Then, to access this new environment, you will use ``conda activate spike``. Once the environment is activated, you can follow your preferred installation method detailed above. 

Note that you will need to activate the environment on accessing a new terminal window in order to run ``spike`` or other packages that exist only in that environment. To return to your root environment, run ``conda deactivate``.


Working with Jupyter
--------------------

If you have created a new environment for ``spike``, you will need to generate a corresponding kernel to run .ipynb files with that environment. If you are using conda, this will look like the following:

.. code-block:: bash

	conda activate spike
	python -m ipykernel install --user --name spike --display-name "spike"


If your ``spike`` environment does not include ``jupyter``, you will need to install it before running the above command. Otherwise you will get a "No module named ipykernel" error.

The syntax will be similar with other environment managers. The kernel only needs to be generated *once*. Subsequent usage of notebooks will just require selecting the ``spike`` kernel.

One common issue with ipython kernels is that they do not inherit the environment variables from your global startup file. You can list all of your available kernels with ``jupyter kernelspec list`` run from the command line. Your kernel.json file can be accessed at the path listed for the ``spike`` kernel + '/share/jupyter/kernels/kernel.json'. To update your environment variables, simply add an "env" stanza to the .json file, specifying which variables to include:

.. code-block:: json

	{
	 "argv": [
	  "python",
	  "-m",
	  "ipykernel_launcher",
	  "-f",
	  "{connection_file}"
	 ],
	 "display_name": "Python 3 (ipykernel)",
	 "language": "python",
	 "metadata": {
	  "debugger": true
	 },
	 "env": {
	    "TINYTIM": "${TINYTIM}",
	    "STPSF_PATH": "${STPSF_PATH}",
	    "CRDS_PATH": "${CRDS_PATH}"
	 }
	}

If you are still using ``WebbPSF`` instead of ``STPSF``, your key/value pair will be ``"WEBBPSF_PATH": "${WEBBPSF_PATH}"`` instead of ``"STPSF_PATH": "${STPSF_PATH}"``.

In my experience, this works for notebooks instantiated from the command line or an IDE, but does not consistently work with, e.g., the JupyterLab application. See also `this discussion <https://stackoverflow.com/questions/37890898/how-to-set-env-variable-in-jupyter-notebook>`_ for other ways to set up environment variables with Jupyter kernels.

One alternative that discussion raises is to use ``os`` to set environment variables before importing ``spike`` as follows:

.. code-block:: python

	import os

	os['TINYTIM'] = '/path/to/tinytim'
	os['STPSF_PATH'] = '/path/to/stpsf'
	os['CRDS_PATH'] = '/path/to/crds/cache'

	import spike

If, instead, you have installed ``spike`` to your root environment, you can simply use your standard python kernel.
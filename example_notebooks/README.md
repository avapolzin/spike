You may notice that the example notebooks in this directory are all fairly similar -- this is a function of `spike` using common syntax across modules for both PSF drizzling and PSF generation, which makes the code very simple to use. 

The data used in these examples is available for download from [MAST](https://mast.stsci.edu/portal/Mashup/Clients/Mast/Portal.html) (via search) or [here](https://uchicago.box.com/s/1a0ip1q4dsdoswpi86630m02275z95j1).

If you have created a new environment for `spike`, you will need to generate a corresponding kernel to run .ipynb files with that environment. If you are using conda, this will look like the following:

```bash
conda activate spike
python -m ipykernel install --user --name spike --display-name "spike"
````

If your `spike` environment does not include `jupyter`, you will need to install it before running the above command. Otherwise you will get a "No module named ipykernel" error.

The syntax will be similar with other environment managers. The kernel only needs to be generated _once_. Subsequent usage of notebooks will just require selecting the `spike` kernel.

One common issue with ipython kernels is that they do not inherit the environment variables from your global startup file. You can list all of your available kernels with `jupyter kernelspec list` run from the command line. Your kernel.json file can be accessed at the path listed for the `spike` kernel + '/share/jupyter/kernels/kernel.json'. To update your environment variables, simply add an "env" stanza to the .json file, specifying which variables to include:

```json
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
```

If you are still using `WebbPSF` instead of `STPSF`, your key/value pair will be `"WEBBPSF_PATH": "${WEBBPSF_PATH}"` instead of `"STPSF_PATH": "${STPSF_PATH}"`.

In my experience, this works for notebooks instantiated from the command line or an IDE, but does not consistently work with, e.g., the JupyterLab application. See also [this discussion](https://stackoverflow.com/questions/37890898/how-to-set-env-variable-in-jupyter-notebook) for other ways to set up environment variables with Jupyter kernels.

One alternative that discussion raises is to use `os` to set environment variables before importing `spike` as follows:

```python
import os

os['TINYTIM'] = '/path/to/tinytim'
os['STPSF_PATH'] = '/path/to/stpsf'
os['CRDS_PATH'] = '/path/to/crds/cache'

import spike
```

If, instead, you have installed `spike` to your root environment, you can simply use your standard python kernel.
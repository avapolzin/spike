If you have created a new environment for `spike`, you will need to generate a corresponding kernel to run .ipynb files with that environment. If you are using conda, this will look like the following:

```bash
conda activate spike
python -m ipykernel install --user --name spike --display-name "spike"
````

If your `spike` environment does not include `jupyter`, you will need to install it before running the aobve command. Otherwise you will get a "No module named ipykernel" error.

The syntax will be similar with other environment managers. The kernel only needs to be generated _once_. Subsequent usage of notebooks will just require selecting the `spike` kernel.

One common issue with Jupyter kernels is that they do not inherit the environment variables from your global startup file. You can list all of your available kernels with `jupyter kernelspec list` run from the command line. Your kernel.json file can be accessed at the path listed for the `spike` kernel + '/share/jupyter/kernels/kernel.json'. To update your environment variables, simply add an "env" stanza to the .json file, specifying which variables to include:

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
    "WEBBPSF_PATH": "${WEBBPSF_PATH}",
    "CRDS_PATH": "${CRDS_PATH}"
 }
}
```

In my experience, this works for notebooks instantiated from the command line or an IDE, but does not consistently work with, e.g., the JupyterLab application. See also [this discussion](https://stackoverflow.com/questions/37890898/how-to-set-env-variable-in-jupyter-notebook) for other ways to set up environment variables with Jupyter kernels.

If, instead, you have installed `spike` to your root environment, you can simply use your standard python kernel.
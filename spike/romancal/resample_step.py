"""
This module is designed to make romancal tweakreg and resample functions accessible without
installing the original package due to their complex dependencies. As such, it is only subtly modified from
the original to accommodate the less stringent install requirements.


romancal copyright notice:

Copyright (C) 2010 Association of Universities for Research in Astronomy (AURA)

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

    1. Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.

    2. Redistributions in binary form must reproduce the above
      copyright notice, this list of conditions and the following
      disclaimer in the documentation and/or other materials provided
      with the distribution.

    3. The name of AURA and its representatives may not be used to
      endorse or promote products derived from this software without
      specific prior written permission.

THIS SOFTWARE IS PROVIDED BY AURA ``AS IS'' AND ANY EXPRESS OR IMPLIED
WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL AURA BE LIABLE FOR ANY DIRECT, INDIRECT,
INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR
TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
DAMAGE.

Original: https://github.com/spacetelescope/romancal/blob/main/romancal/resample/resample_step.py
"""

from __future__ import annotations

import logging
import os
from copy import deepcopy
from typing import TYPE_CHECKING

import asdf
import numpy as np
from astropy.extern.configobj.configobj import ConfigObj
from astropy.extern.configobj.validate import Validator
from roman_datamodels import datamodels
import spike.stcal.alignment_util as util

from spike.romancal.datamodels_library import ModelLibrary
from spike.romancal.stpipe_core import RomanStep
from spike.romancal import resample

if TYPE_CHECKING:
    from typing import ClassVar

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

__all__ = ["ResampleStep"]

# conversion factor from steradian to squared arcsec
SR_TO_ARCSEC2 = 4.254517e10


class ResampleStep(RomanStep):
    """
    Resample input data onto a regular grid using the drizzle algorithm.

    .. note::
        When supplied via ``output_wcs``, a custom WCS overrides other custom
        WCS parameters such as ``output_shape`` (now computed from by
        ``output_wcs.bounding_box``), ``crpix``

    Parameters
    -----------
    input : str, `roman_datamodels.datamodels.DataModel`, or `~romancal.datamodels.ModelLibrary`
        If a string is provided, it should correspond to either a single ASDF filename
        or an association filename. Alternatively, a single DataModel instance can be
        provided instead of an ASDF filename. Multiple files can be processed via
        either an association file or wrapped by a
        `~romancal.datamodels.ModelLibrary`.

    Returns
    -------
    : `roman_datamodels.datamodels.MosaicModel`
        A mosaic datamodel with the final output frame.
    """

    class_alias = "resample"

    spec = """
        pixfrac = float(default=1.0) # change back to None when drizpar reference files are updated
        kernel = string(default='square') # change back to None when drizpar reference files are updated
        fillval = string(default='INDEF' ) # change back to None when drizpar reference files are updated
        weight_type = option('ivm', 'exptime', None, default='ivm')  # change back to None when drizpar ref update
        output_shape = int_list(min=2, max=2, default=None)  # [x, y] order
        crpix = float_list(min=2, max=2, default=None)
        crval = float_list(min=2, max=2, default=None)
        rotation = float(default=None)
        pixel_scale_ratio = float(default=1.0) # Ratio of input to output pixel scale
        pixel_scale = float(default=None) # Absolute pixel scale in arcsec
        output_wcs = string(default='')  # Custom output WCS.
        single = boolean(default=False)
        blendheaders = boolean(default=True)
        allowed_memory = float(default=None)  # Fraction of memory to use for the combined image.
        in_memory = boolean(default=True)
        good_bits = string(default='~DO_NOT_USE+NON_SCIENCE')  # The good bits to use for building the resampling mask.
    """

    reference_file_types: ClassVar = []

    def process(self, input):
        if isinstance(input, datamodels.DataModel):
            input_models = ModelLibrary([input])
            # set output filename from meta.filename found in the first datamodel
            output = input.meta.filename
            self.blendheaders = False
        elif isinstance(input, str):
            # either a single asdf filename or an association filename
            try:
                # association filename
                input_models = ModelLibrary(input)
            except Exception:
                # single ASDF filename
                input_models = ModelLibrary([input])
            output = input_models.asn["products"][0]["name"]
        elif isinstance(input, ModelLibrary):
            input_models = input
            if "name" in input_models.asn["products"][0]:
                output = input_models.asn["products"][0]["name"]
            else:
                # set output filename using the common prefix of all datamodels
                output = f"{os.path.commonprefix([x['expname'] for x in input_models.asn['products'][0]['members']])}.asdf"
                if len(output) == 0:
                    # set default filename if no common prefix can be determined
                    output = "resample_output.asdf"
        else:
            raise TypeError(
                "Input must be an ASN filename, a ModelLibrary, "
                "a single ASDF filename, or a single Roman DataModel."
            )

        # Check that input models are 2D images
        with input_models:
            example_model = input_models.borrow(0)
            data_shape = example_model.data.shape
            input_models.shelve(example_model, 0, modify=False)
            if len(data_shape) != 2:
                # resample can only handle 2D images, not 3D cubes, etc
                raise RuntimeError(f"Input {input_models[0]} is not a 2D image.")

        self.wht_type = self.weight_type
        self.log.info("Setting drizzle's default parameters...")
        kwargs = self.set_drizzle_defaults()
        kwargs["allowed_memory"] = self.allowed_memory

        # Issue a warning about the use of exptime weighting
        if self.wht_type == "exptime":
            self.log.warning("Use of EXPTIME weighting will result in incorrect")
            self.log.warning("propagated errors in the resampled product")

        # Custom output WCS parameters.
        # Modify get_drizpars if any of these get into reference files:
        kwargs["output_shape"] = self._check_list_pars(
            self.output_shape, "output_shape", min_vals=[1, 1]
        )
        kwargs["output_wcs"] = self._load_custom_wcs(
            self.output_wcs, kwargs["output_shape"]
        )
        kwargs["crpix"] = self._check_list_pars(self.crpix, "crpix")
        kwargs["crval"] = self._check_list_pars(self.crval, "crval")
        kwargs["rotation"] = self.rotation
        kwargs["pscale"] = self.pixel_scale
        kwargs["pscale_ratio"] = self.pixel_scale_ratio
        kwargs["in_memory"] = self.in_memory

        # Call the resampling routine
        resamp = resample.ResampleData(input_models, output=output, **kwargs)
        result = resamp.do_drizzle()

        with result:
            for i, model in enumerate(result):
                self._final_updates(model, input_models, kwargs)
                result.shelve(model, i)
            if len(result) == 1:
                model = result.borrow(0)
                result.shelve(model, 0, modify=False)
                return model

        return result

    def _final_updates(self, model, input_models, kwargs):
        model.meta.cal_step["resample"] = "COMPLETE"
        model.meta.wcsinfo.s_region = util.compute_s_region_imaging(
            model.meta.wcs, model.data.shape
        )

        # if pixel_scale exists, it will override pixel_scale_ratio.
        # calculate the actual value of pixel_scale_ratio based on pixel_scale
        # because source_catalog uses this value from the header.
        model.meta.resample.pixel_scale_ratio = (
            self.pixel_scale / np.sqrt(model.meta.photometry.pixel_area * SR_TO_ARCSEC2)
            if self.pixel_scale
            else self.pixel_scale_ratio
        )
        model.meta.resample.pixfrac = kwargs["pixfrac"]
        self.update_phot_keywords(model)
        model.meta.resample["good_bits"] = kwargs["good_bits"]

    @staticmethod
    def _check_list_pars(vals, name, min_vals=None):
        """
        Check if a specific keyword parameter is properly formatted.

        Parameters
        ----------
        vals : list or tuple
            A list or tuple containing a pair of values currently assigned to the
            keyword parameter `name`. Both values must be either `None` or not `None`.
        name : str
            The name of the keyword parameter.
        min_vals : list or tuple, optional
            A list or tuple containing a pair of minimum values to be assigned
            to `name`, by default None.

        Returns
        -------
        None or list
            If either `vals` is set to `None` (or both of its elements), the
            returned result will be `None`. Otherwise, the returned result will be
            a list containing the current values assigned to `name`.

        Raises
        ------
        ValueError
            This error will be raised if any of the following conditions are met:
            - the number of elements of `vals` is not 2;
            - the currently assigned values of `vals` are smaller than the
            minimum value provided;
            - one element is `None` and the other is not `None`.
        """
        if vals is None:
            return None
        if len(vals) != 2:
            raise ValueError(f"List '{name}' must have exactly two elements.")
        n = sum(x is None for x in vals)
        if n == 2:
            return None
        elif n == 0:
            if (
                min_vals
                and sum(x >= y for x, y in zip(vals, min_vals, strict=False)) != 2
            ):
                raise ValueError(
                    f"'{name}' values must be larger or equal to {list(min_vals)}"
                )
            return list(vals)
        else:
            raise ValueError(f"Both '{name}' values must be either None or not None.")

    @staticmethod
    def _load_custom_wcs(asdf_wcs_file, output_shape):
        if not asdf_wcs_file:
            return None

        with asdf.open(asdf_wcs_file) as af:
            wcs = deepcopy(af.tree["wcs"])

        if output_shape is not None:
            wcs.array_shape = output_shape[::-1]
        elif wcs.pixel_shape is not None:
            wcs.array_shape = wcs.pixel_shape[::-1]
        elif wcs.bounding_box is not None:
            wcs.array_shape = tuple(
                int(axs[1] - axs[0] + 0.5)
                for axs in wcs.bounding_box.bounding_box(order="C")
            )
        elif wcs.array_shape is None:
            raise ValueError(
                "Step argument 'output_shape' is required when custom WCS "
                "does not have neither of 'array_shape', 'pixel_shape', or "
                "'bounding_box' attributes set."
            )

        return wcs

    def update_phot_keywords(self, model):
        """Update pixel scale keywords"""
        if model.meta.photometry.pixel_area is not None:
            model.meta.photometry.pixel_area *= model.meta.resample.pixel_scale_ratio**2

    def set_drizzle_defaults(self):
        """Set the default parameters for drizzle."""
        configspec = self.load_spec_file()
        config = ConfigObj(configspec=configspec)
        if config.validate(Validator()):
            kwargs = config.dict()

        if self.pixfrac is None:
            self.pixfrac = 1.0
        if self.kernel is None:
            self.kernel = "square"
        if self.fillval is None:
            self.fillval = "INDEF"
        # Force definition of good bits
        kwargs["good_bits"] = self.good_bits
        kwargs["pixfrac"] = self.pixfrac
        kwargs["kernel"] = str(self.kernel)
        kwargs["fillval"] = str(self.fillval)
        #  self.weight_type has a default value of None
        # The other instruments read this parameter from a reference file
        if self.wht_type is None:
            self.wht_type = "ivm"

        kwargs["wht_type"] = str(self.wht_type)
        kwargs["pscale_ratio"] = self.pixel_scale_ratio
        kwargs.pop("pixel_scale_ratio")

        for k, v in kwargs.items():
            if k in [
                "pixfrac",
                "kernel",
                "fillval",
                "wht_type",
                "pscale_ratio",
            ]:
                log.info("  using: %s=%s", k, repr(v))

        return kwargs
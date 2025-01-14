"""
This module is designed to make jwst tweakreg and resample functions accessible without
installing the original package due to their complex dependencies. As such, it is only subtly modified from
the original to accommodate the less stringent install requirements.


jwst copyright notice:

Copyright (C) 2020 Association of Universities for Research in Astronomy (AURA)

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

Original: https://github.com/spacetelescope/jwst/blob/main/jwst/lib/pipe_utils.py
"""

import logging

import numpy as np
from stdatamodels.properties import ObjectNode
from stdatamodels.jwst.datamodels import dqflags, JwstDataModel

from spike.jwstcal.associations_lib_dms_base import TSO_EXP_TYPES


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def is_tso(model):
    """Is data Time Series Observation data?

    Parameters
    ----------
    model : `~jwst.datamodels.JwstDataModel`
        Data to check

    Returns
    -------
    is_tso : bool
       `True` if the model represents TSO data
    """
    is_tso = False

    # Check on JWST-specific TSOVISIT flag
    try:
        is_tso = model.meta.visit.tsovisit
    except AttributeError:
        pass

    # Check on exposure types
    try:
        is_tso = is_tso or model.meta.exposure.type.lower() in TSO_EXP_TYPES
    except AttributeError:
        pass

    # Check on number of integrations
    try:
        if model.meta.exposure.nints is not None and model.meta.exposure.nints < 2:
            is_tso = False
    except AttributeError:
        pass

    # We've checked everything.
    return is_tso


def is_irs2(model):
    """Check whether the data are in IRS2 format.

    This currently assumes that only full-frame, near-infrared data can be
    taken using the IRS2 readout pattern.

    Parameters
    ----------
    model : `~jwst.datamodels.JwstDataModel` or ndarray
        Data to check

    Returns
    -------
    bool
       `True` if the data are in IRS2 format
    """

    if isinstance(model, np.ndarray):
        shape = model.shape
    else:
        try:
            shape = model.data.shape
        except AttributeError:
            return False

    max_length = 2048

    irs2_axis_length = max(shape[-1], shape[-2])

    if irs2_axis_length > max_length:
        return True
    else:
        return False


def match_nans_and_flags(input_model):
    """Ensure data, error, variance, and DQ are marked consistently for invalid data.

    Invalid data is assumed to be any pixel set to NaN in any one of the
    data, error, or variance arrays, or else set to the DO_NOT_USE flag
    in the DQ array.

    The input model is updated in place with NaNs or DO_NOT_USE flags, as
    appropriate, at all invalid data locations.

    Parameters
    ----------
    input_model : DataModel
        Input model containing some combination of data, dq, err, var_rnoise,
        var_poisson, and var_flat extensions. These extensions must all have
        matching dimensions if present.
    """
    # Check for datamodel input or slit instance
    if (not isinstance(input_model, JwstDataModel)
            and not isinstance(input_model, ObjectNode)):
        raise ValueError(f"Input {type(input_model)} is not a datamodel.")

    # Build up the invalid data flags from each available data extension.
    is_invalid = None
    data_shape = None
    nan_extensions = ['data', 'err', 'var_rnoise', 'var_poisson', 'var_flat']
    for extension in nan_extensions:
        if not hasattr(input_model, extension):
            continue
        data = getattr(input_model, extension)
        if is_invalid is None:
            is_invalid = np.isnan(data)
            data_shape = data.shape
        else:
            if data.shape != data_shape:
                log.warning(f"Mismatched data shapes; skipping invalid data "
                            f"updates for extension '{extension}'")
                continue
            is_invalid |= np.isnan(data)

    # Nothing to do if no extensions were found to update
    if is_invalid is None:
        return

    # Add in invalid flags from the DQ extension if present
    if hasattr(input_model, 'dq'):
        do_not_use = (input_model.dq & dqflags.pixel['DO_NOT_USE']).astype(bool)
        if input_model.dq.shape != data_shape:
            log.warning("Mismatched data shapes; skipping invalid data "
                        "updates for extension 'dq'")
        else:
            is_invalid |= do_not_use

    # Update all the data extensions
    for extension in nan_extensions:
        if not hasattr(input_model, extension):
            continue
        data = getattr(input_model, extension)
        if data.shape != data_shape:
            continue
        data[is_invalid] = np.nan

    # Update the DQ extension
    if input_model.dq.shape == data_shape:
        input_model.dq[is_invalid] |= dqflags.pixel['DO_NOT_USE']
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

Original: https://github.com/spacetelescope/romancal/blob/main/romancal/stpipe/core.py
"""

import importlib.metadata
import logging
import time
from pathlib import Path

import roman_datamodels as rdm
from roman_datamodels.datamodels import ImageModel, MosaicModel
# from stpipe import Pipeline, Step, crds_client
from spike.stpipe.step import Step
from spike.stpipe.pipeline import Pipeline
from spike.stpipe import crds_client

from spike.romancal.datamodels_library import ModelLibrary

from spike.romancal.lib_suffix import remove_suffix

_LOG_FORMATTER = logging.Formatter(
    "%(asctime)s.%(msecs)03dZ :: %(name)s :: %(levelname)s :: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
_LOG_FORMATTER.converter = time.gmtime


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class RomanStep(Step):
    """
    Base class for Roman calibration pipeline steps.
    """

    spec = """
    output_ext =  string(default='.asdf')    # Default type of output
    """

    _log_records_formatter = _LOG_FORMATTER

    @classmethod
    def _datamodels_open(cls, init, **kwargs):
        """
        Provide access to this package's datamodels.open function
        so that the stpipe infrastructure knows how to instantiate
        models and containers.
        """
        if isinstance(init, str):
            init = Path(init)
        if isinstance(init, Path):
            ext = init.suffix.lower()
            if ext == ".asdf":
                return rdm.open(init, **kwargs)
            if ext in (".json", ".yaml"):
                return ModelLibrary(init, **kwargs)
        if isinstance(init, rdm.DataModel):
            return rdm.open(init, **kwargs)
        if isinstance(init, ModelLibrary):
            return ModelLibrary(init)
        raise TypeError(f"Invalid input: {init}")

    def finalize_result(self, model, reference_files_used):
        """
        Hook that allows the Step to set metadata on the output model
        before save.

        Parameters
        ----------
        model : roman_datamodels.datamodels.DataModel
            Output model.

        reference_files_used : list of tuple(str, str)
            List of reference files used.  The first element of each tuple
            is the reftype code, the second element is the filename.
        """

        model.meta.calibration_software_version = importlib.metadata.version("romancal")

        # FIXME: should cal_logs be brought back into meta for a MosaicModel?
        if isinstance(model, ImageModel):
            # convert to model.cal_logs type to avoid validation errors
            model.meta.cal_logs = type(model.meta.cal_logs)(self.log_records)
        if isinstance(model, MosaicModel):
            model.cal_logs = type(model.cal_logs)(self.log_records)

        if len(reference_files_used) > 0:
            for ref_name, ref_file in reference_files_used:
                if hasattr(model.meta.ref_file, ref_name):
                    setattr(model.meta.ref_file, ref_name, ref_file)
                    # getattr(model.meta.ref_file, ref_name).name = ref_file
            model.meta.ref_file.crds.version = crds_client.get_svn_version()
            model.meta.ref_file.crds.context = crds_client.get_context_used(
                model.crds_observatory
            )

            # this will only run if 'parent' is none, which happens when an individual
            # step is being run or if self is a RomanPipeline and not a RomanStep.
            if self.parent is None:
                log.info(
                    f"Results used CRDS context: {model.meta.ref_file.crds.context}"
                )

    def record_step_status(self, model, step_name, success=True):
        """
        Record step completion status in the model's metadata.

        Parameters
        ----------
        model : roman_datamodels.datamodels.DataModel
            Output model.
        step_name : str
            Calibration step name.
        success : bool
            If True, then the step was run successfully.
        """
        # JWST sets model.meta.cal_step.<step name> here.  Roman
        # may do the same, depending on how the metadata format
        # turns out.  Seems like we might be able to combine this
        # with finalize_result somehow.
        pass

    def remove_suffix(self, name):
        """
        Remove any Roman step-specific suffix from the given filename.

        Parameters
        ----------
        name : str
            Filename.

        Returns
        -------
        str
            Filename with step suffix removed.
        """
        # JWST maintains a list of relevant suffixes that is monitored
        # by tests to be up-to-date.  Roman will likely need to do
        # something similar.
        return remove_suffix(name)


# RomanPipeline needs to inherit from Pipeline, but also
# be a subclass of RomanStep so that it will pass checks
# when constructing a pipeline using RomanStep class methods.
class RomanPipeline(Pipeline, RomanStep):
    pass
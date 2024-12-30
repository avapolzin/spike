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

Original: https://github.com/spacetelescope/jwst/blob/main/jwst/stpipe/core.py
"""

from functools import wraps
import logging
import warnings

from stdatamodels.jwst.datamodels import JwstDataModel
from stdatamodels.jwst import datamodels
from spike.stpipe import crds_client
from spike.stpipe.step import Step
from spike.stpipe.pipeline import Pipeline

# from jwst import __version_commit__, __version__
__version_commit__ = '1.16.1' #hard coding based on released development version
__version__ = '1.16.1' # to avoid headache + keep track
from spike.jwstcal.lib_suffix import remove_suffix


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class JwstStep(Step):

    spec = """
    output_ext = string(default='.fits')  # Output file type
    """

    @classmethod
    def _datamodels_open(cls, init, **kwargs):
        return datamodels.open(init, **kwargs)


    def load_as_level2_asn(self, obj):
        """Load object as an association

        Loads the specified object into a Level2 association.
        If necessary, prepend `Step.input_dir` to all members.

        Parameters
        ----------
        obj : object
            Object to load as a Level2 association

        Returns
        -------
        association : jwst.associations.lib.rules_level2_base.DMSLevel2bBase
            Association
        """
        # Prevent circular import:
        from ..associations.load_as_asn import LoadAsLevel2Asn
        from ..associations.lib.update_path import update_key_value

        asn = LoadAsLevel2Asn.load(obj, basename=self.output_file)
        update_key_value(asn, 'expname', (), mod_func=self.make_input_path)
        return asn

    def load_as_level3_asn(self, obj):
        """Load object as an association

        Loads the specified object into a Level3 association.
        If necessary, prepend `Step.input_dir` to all members.

        Parameters
        ----------
        obj : object
            Object to load as a Level3 association

        Returns
        -------
        association : jwst.associations.lib.rules_level3_base.DMS_Level3_Base
            Association
        """
        # Prevent circular import:
        from ..associations.load_as_asn import LoadAsAssociation
        from ..associations.lib.update_path import update_key_value

        asn = LoadAsAssociation.load(obj)
        update_key_value(asn, 'expname', (), mod_func=self.make_input_path)
        return asn

    def finalize_result(self, result, reference_files_used):
        if isinstance(result, JwstDataModel):
            result.meta.calibration_software_revision = __version_commit__ or 'RELEASE'
            result.meta.calibration_software_version = __version__

            if len(reference_files_used) > 0:
                for ref_name, filename in reference_files_used:
                    if hasattr(result.meta.ref_file, ref_name):
                        getattr(result.meta.ref_file, ref_name).name = filename
                result.meta.ref_file.crds.sw_version = crds_client.get_svn_version()
                result.meta.ref_file.crds.context_used = crds_client.get_context_used(result.crds_observatory)
                if self.parent is None:
                    log.info(f"Results used CRDS context: {result.meta.ref_file.crds.context_used}")


    def remove_suffix(self, name):
        return remove_suffix(name)

    @wraps(Step.run)
    def run(self, *args, **kwargs):
        result = super().run(*args, **kwargs)
        if not self.parent:
            log.info(f"Results used jwst version: {__version__}")
        return result

    @wraps(Step.__call__)
    def __call__(self, *args, **kwargs):
        if not self.parent:
            warnings.warn(
                "Step.__call__ is deprecated. It is equivalent to Step.run "
                "and is not recommended. See "
                "https://jwst-pipeline.readthedocs.io/en/latest/jwst/"
                "user_documentation/running_pipeline_python.html"
                "#advanced-use-pipeline-run-vs-pipeline-call for more details.",
                UserWarning
            )
        return super().__call__(*args, **kwargs)


# JwstPipeline needs to inherit from Pipeline, but also
# be a subclass of JwstStep so that it will pass checks
# when constructing a pipeline using JwstStep class methods.
class JwstPipeline(Pipeline, JwstStep):
    def finalize_result(self, result, reference_files_used):
        if isinstance(result, JwstDataModel):
            log.info(f"Results used CRDS context: {crds_client.get_context_used(result.crds_observatory)}")
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

Original: https://github.com/spacetelescope/romancal/blob/main/romancal/datamodels/library.py
"""

import asdf
from roman_datamodels import open as datamodels_open
from spike.stpipe.library import AbstractModelLibrary, NoGroupID

# from romancal.associations import AssociationNotValidError, load_asn
from spike.romancal.associations_exceptions import AssociationNotValidError
from spike.romancal.associations_load_asn import load_asn

__all__ = ["ModelLibrary"]


class ModelLibrary(AbstractModelLibrary):
    @property
    def crds_observatory(self):
        return "roman"

    def _model_to_filename(self, model):
        model_filename = model.meta.filename
        if model_filename is None:
            model_filename = "model.asdf"
        return model_filename

    def _datamodels_open(self, filename, **kwargs):
        return datamodels_open(filename, **kwargs)

    @classmethod
    def _load_asn(cls, asn_path):
        try:
            with open(asn_path) as asn_file:
                asn_data = load_asn(asn_file)
        except AssociationNotValidError as e:
            raise OSError("Cannot read ASN file.") from e
        return asn_data

    def _filename_to_group_id(self, filename):
        """
        Compute a "group_id" without loading the file as a DataModel

        This function will return the meta.group_id stored in the ASDF
        extension (if it exists) or a group_id calculated from the
        ASDF headers.
        """
        meta = asdf.util.load_yaml(filename)["roman"]["meta"]
        if group_id := meta.get("group_id"):
            return group_id
        if "observation" in meta:
            return _mapping_to_group_id(meta["observation"])
        raise NoGroupID(f"{filename} missing group_id")

    def _model_to_group_id(self, model):
        """
        Compute a "group_id" from a model using the DataModel interface
        """
        if (group_id := getattr(model.meta, "group_id", None)) is not None:
            return group_id
        if hasattr(model.meta, "observation"):
            return _mapping_to_group_id(model.meta.observation)
        raise NoGroupID(f"{model} missing group_id")

    def _assign_member_to_model(self, model, member):
        # roman_datamodels doesn't allow assignment of meta.group_id
        # (since it's not in the schema). To work around this use
        # __setitem__ calls here instead of setattr
        for attr in ("group_id", "tweakreg_catalog", "exptype"):
            if attr in member:
                model.meta[attr] = member[attr]
        if not hasattr(model.meta, "asn"):
            model.meta["asn"] = {}

        if "table_name" in self.asn:
            model.meta.asn["table_name"] = self.asn["table_name"]
        if "asn_pool" in self.asn:
            model.meta.asn["pool_name"] = self.asn["asn_pool"]


def _mapping_to_group_id(mapping):
    """
    Combine a number of file metadata values into a ``group_id`` string
    """
    return "{observation_id}".format_map(mapping)
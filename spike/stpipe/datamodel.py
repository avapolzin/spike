"""
This module is designed to make stpipe functions accessible without
installing the original package due to their complex dependencies. As such, it is only subtly modified from
the original to accommodate the less stringent install requirements.


stpipe copyright notice:

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

Original: https://github.com/spacetelescope/stpipe/blob/main/src/stpipe/datamodel.py
"""

import abc


class AbstractDataModel(abc.ABC):
    """
    This Abstract Base Class is intended to cover multiple implementations of
    data models so that each will be considered an appropriate subclass of this
    class without requiring that they inherit this class.

    Any datamodel class instance that desires to be considered an instance of
    AbstractDataModel must implement the following methods.

    In addition, although it isn't yet checked (the best approach for supporting
    this is still being considered), such instances must have a meta.filename
    attribute.
    """

    @classmethod
    def __subclasshook__(cls, c_):
        """
        Pseudo subclass check based on these attributes and methods
        """
        if cls is AbstractDataModel:
            mro = c_.__mro__
            if (
                any(hasattr(CC, "crds_observatory") for CC in mro)
                and any(hasattr(CC, "get_crds_parameters") for CC in mro)
                and any(hasattr(CC, "save") for CC in mro)
            ):
                return True
        return False

    @property
    @abc.abstractmethod
    def crds_observatory(self):
        """This should return a string identifying the observatory as CRDS expects it"""

    @abc.abstractmethod
    def get_crds_parameters(self):
        """
        This should return a dictionary of key/value pairs corresponding to the
        parkey values CRDS is using to match reference files. Typically it returns
        all metadata simple values.
        """

    @abc.abstractmethod
    def save(self, path, dir_path=None, *args, **kwargs):
        """
        Save to a file.

        Parameters
        ----------
        path : string or callable
            File path to save to.
            If function, it takes one argument that is
            model.meta.filename and returns the full path string.

        dir_path : str
            Directory to save to. If not None, this will override
            any directory information in the ``path``

        Returns
        -------
        output_path: str
            The file path the model was saved in.
        """
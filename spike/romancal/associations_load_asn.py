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

Original: https://github.com/spacetelescope/romancal/blob/main/romancal/associations/load_asn.py
"""

from inspect import isclass

from spike.romancal.associations_association import Association
from spike.romancal.associations_registry import AssociationRegistry


def load_asn(
    serialized,
    format=None,
    first=True,
    validate=True,
    registry=AssociationRegistry,
    **kwargs,
):
    """Load an Association from a file or object

    Parameters
    ----------
    serialized : object
        The serialized form of the association.

    format : str or None
        The format to force. If None, try all available.

    validate : bool
        Validate against the class' defined schema, if any.

    first : bool
        A serialization potentially matches many rules.
        Only return the first succesful load.

    registry : AssociationRegistry or None
        The `AssociationRegistry` to use.
        If None, no registry is used.
        Can be passed just a registry class instead of instance.

    kwargs : dict
        Other arguments to pass to the `load` methods defined
        in the `Association.IORegistry`

    Returns
    -------
    The Association object

    Raises
    ------
    AssociationNotValidError
        Cannot create or validate the association.

    Notes
    -----
    The `serialized` object can be in any format
    supported by the registered I/O routines. For example, for
    `json` and `yaml` formats, the input can be either a string or
    a file object containing the string.

    If no registry is specified, the default `Association.load`
    method is used.
    """
    if registry is None:
        return Association.load(serialized, format=format, validate=validate)

    if isclass(registry):
        registry = registry()
    return registry.load(
        serialized, format=format, first=first, validate=validate, **kwargs
    )
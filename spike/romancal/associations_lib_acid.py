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

Original: https://github.com/spacetelescope/romancal/blob/main/romancal/associations/lib/acid.py
"""

import re
from ast import literal_eval

from spike.romancal.associations_lib_counter import Counter

__all__ = ["ACID"]

# Start of the discovered association ids.
_DISCOVERED_ID_START = 3001


class ACID:
    """Association Candidate Identifer

    Parameters
    ----------
    input : str or 2-tuple
        The string representation or 2-tuple containing the
        candidate ID and TYPE. The string should be itself
        the 2-tuple representation when evaluated. The 2-tuple
        will have the form:
            (id, type)

    Attributes
    ----------
    id : str
        The id number.

    type : str
        The type of candidate. Some, but not all
        possibilities include 'OBSERVATION',
        'MOSAIC', 'DISCOVERED'

    __str__ : str
        The DMS-specified string representation of
        a candidate identifier. Possibilities include
        'oXXX' for OBSERVATION, 'c1XXX' for 'MOSAIC' or
        other PPS-defined candidates, and 'a3XXX' for
        'DISCOVERED' associations.
    """

    def __init__(self, input):
        try:
            self.id, self.type = literal_eval(input)
        except (ValueError, SyntaxError):
            self.id, self.type = input

    def __str__(self):
        return self.id


class ACIDMixin:
    """Enable ACID for rules"""

    def __init__(self, *args, **kwargs):
        # Initialize discovered association ID
        self.discovered_id = Counter(_DISCOVERED_ID_START)

        super().__init__(*args, **kwargs)

    def acid_from_constraints(self):
        """Determine ACID from constraints"""
        for constraint in self.constraints:
            if getattr(constraint, "is_acid", False):
                value = re.sub("\\\\", "", "-".join(constraint.found_values))
                try:
                    acid = ACID(value)
                except ValueError:
                    pass
                else:
                    break
        else:
            id = f"a{self.discovered_id.value:0>3}"
            acid = ACID((id, "DISCOVERED"))

        return acid

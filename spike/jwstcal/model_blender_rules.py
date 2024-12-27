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

Original: https://github.com/spacetelescope/jwst/blob/main/jwst/model_blender/rules.py
"""

import numpy as np


__all__ = ['RULE_FUNCTIONS', 'AttributeBlender', 'make_blender']


def _multi(vals):
    """
    This will either return the common value from a list of identical values
    or 'MULTIPLE'
    """
    uniq_vals = list(set(vals))
    num_vals = len(uniq_vals)
    if num_vals == 0:
        return None
    if num_vals == 1:
        return uniq_vals[0]
    if num_vals > 1:
        return "MULTIPLE"


RULE_FUNCTIONS = {
    'multi': _multi,
    'mean': np.mean,
    'sum': np.sum,
    'max': np.max,
    'min': np.min,

     # retained date/time names for backwards compatibility
     # as these all assume ISO8601 format the lexical and
     # chronological sorting match
    'mintime': min,
    'maxtime': max,
    'mindate': min,
    'maxdate': max,
    'mindatetime': min,
    'maxdatetime': max
}
"""
Mapping of rule names to functions.

Used for `make_blender`.

The following rules are considered deprecated
and should not be used for new schemas.

  - mintime
  - maxtime
  - mindate
  - maxdate
  - mindatetime
  - maxdatetime
"""


class AttributeBlender:
    """
    Single attribute metadata blender
    """
    def __init__(self, blend_function):
        """
        Create a new metadata attribute blender.

        Parameters
        ----------
        blend_function: callable
            Function to blend accumulated metadata values
        """
        self.blend_function = blend_function
        self.values = []

    def accumulate(self, value):
        """
        Add a metadata value for blending.

        Parameters
        ----------
        value:
            Value for this metadata attribute to use
            when blending.
        """
        self.values.append(value)

    def finalize(self):
        """
        Blend the accumulated metadata values.

        Returns
        -------
        value:
            The blended result.
        """
        if not self.values:
            return None
        return self.blend_function(self.values)


def make_blender(rule):
    """
    Make a `AttributeBlender` instance using the provided rule

    Parameters
    ----------
    rule: string
        Name of the blending rule. Must be in `RULE_FUNCTIONS`.

    Returns
    -------
    attr_blender: `AttrBlender`
        Blender instance using the provided rule.
    """
    return AttributeBlender(RULE_FUNCTIONS[rule])
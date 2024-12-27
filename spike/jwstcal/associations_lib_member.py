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

Original: https://github.com/spacetelescope/jwst/blob/main/jwst/associations/lib/member.py
"""

from collections import UserDict
from copy import copy


class Member(UserDict):
    """Member of an association

    Parameters
    ----------
    initialdata: Dict-like or Member
        Initialization data. Any type of initialization that
        `collections.UserDict` allows or `Member` itself.

    item: obj
        The item to initialize with. This will override
        any `Member.item` given in `initialdata`.

    Attributes
    ----------
    item: obj
        The original item that created this member.
    """
    def __init__(self, initialdata=None, item=None):
        self.item = None

        if isinstance(initialdata, Member):
            self.data = copy(initialdata.data)
            self.item = copy(initialdata.item)
        else:
            super(Member, self).__init__(initialdata)

        if item is not None:
            self.item = copy(item)

    def __eq__(self, other):
        """Compare members

        If both Members have attributes `expname` and `exptype`,
        compare only those attributes. Otherwise, use the default
        comparison.
        """
        hasexpkeys = all(k in data
                         for k in ('expname', 'exptype')
                         for data in (self, other))
        if hasexpkeys:
            return all(self[k] == other[k] for k in ('expname', 'exptype'))
        else:
            return super().__eq__(other)
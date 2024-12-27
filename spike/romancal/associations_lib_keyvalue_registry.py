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

Original: https://github.com/spacetelescope/romancal/blob/main/romancal/associations/lib/keyvalue_registry.py
"""

from collections import UserDict

__all__ = [
    "KeyValueRegistry",
    "KeyValueRegistryError",
    "KeyValueRegistryNoKeyFound",
    "KeyValueRegistryNotSingleItemError",
]


class KeyValueRegistry(UserDict):
    """Provide a dict-like registry

    Differences from just a `dict`:
        - Can be given single item or a 2-tuple.
          If an item, attempts to read the `__name__` attribute
          and use that as the key.

        - If None is given as a key, a default key can
          be specified.

        - Instances can be used as decorators.

    Parameters
    ----------
    items : object or (str, object) or dict
        Initializing items.

    default : str or object
        The default to use when key is `None`
    """

    def __init__(self, items=None, default=None):
        super_args = ()
        if items is not None:
            super_args = (make_dict(items),)
        super().__init__(*super_args)

        self.default = None
        if default is not None:
            default_dict = make_dict(default)
            if len(default_dict) > 1:
                raise KeyValueRegistryNotSingleItemError
            default_dict = make_dict(default)
            self.update(default_dict)
            self.default = next(iter(default_dict.keys()))
            self.update({None: default_dict[self.default]})

    def update(self, item):
        """Add item to registry"""
        item_dict = make_dict(item)
        super().update(item_dict)

    def __call__(self, item):
        """Add item by calling instance

        This allows an instance to be used as a decorator.
        """
        self.update(item)
        return item


# ******
# Errors
# ******
class KeyValueRegistryError(Exception):
    def __init__(self, *args):
        if len(args) == 0:
            args = (self.msg,)
        super().__init__(*args)


class KeyValueRegistryNotSingleItemError(KeyValueRegistryError):
    msg = "Item cannot be a list"


class KeyValueRegistryNoKeyFound(KeyValueRegistryError):
    msg = "Cannot deduce key from given value"


# *********
# Utilities
# *********
def make_dict(item):
    """Create a dict from an item

    Parameters
    ----------
    item : object or (name, object) or dict
        If dict, just return dict.
        If 2-tuple, return dict with the key/value pair
        If just object, use `__name__` as key
    """
    try:
        item_dict = dict(item)
    except (TypeError, ValueError):
        try:
            key, value = item
        except (TypeError, ValueError):
            try:
                key = item.__name__
            except (AttributeError, SyntaxError):
                raise KeyValueRegistryNoKeyFound
            else:
                value = item

        # At they point we have a key/value pair
        item_dict = {key: value}

    return item_dict
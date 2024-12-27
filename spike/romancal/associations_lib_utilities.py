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

Original: https://github.com/spacetelescope/romancal/blob/main/romancal/associations/lib/utilities.py
"""


import logging
from ast import literal_eval
from functools import wraps

from numpy.ma import masked

# Configure logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def return_on_exception(exceptions=(Exception,), default=None):
    """Decorator to force functions raising exceptions to return a value

    Parameters
    ----------
    exceptions: (Exception(,...))
        Tuple of exceptions to catch

    default: obj
        The value to return when a specified exception occurs
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exceptions as err:
                logger.debug(
                    "Caught exception %s in function %s, forcing return value of %s",
                    err,
                    func,
                    default,
                )
                return default

        return wrapper

    return decorator


def evaluate(value):
    """Evaluate a value

    Parameters
    ----------
    value : str
        The string to evaluate.

    Returns
    -------
    type or str
        The evaluation. If the value cannot be
        evaluated, the value is simply returned
    """
    try:
        evaled = literal_eval(value)
    except (ValueError, SyntaxError):
        evaled = value
    return evaled


def getattr_from_list(adict, attributes, invalid_values=None):
    """Retrieve value from dict using a list of attributes

    Parameters
    ----------
    adict : dict
        dict to retrieve from

    attributes : list
        List of attributes

    invalid_values : set
        A set of values that essentially mean the
        attribute does not exist.

    Returns
    -------
    (attribute, value)
        Returns the value and the attribute from
        which the value was taken.

    Raises
    ------
    KeyError
        None of the attributes are found in the dict.
    """
    if invalid_values is None:
        invalid_values = set()

    for attribute in attributes:
        try:
            result = adict[attribute]
        except KeyError:
            continue
        else:
            if result is masked:
                continue
            if result not in invalid_values:
                return attribute, result
            else:
                continue
    else:
        raise KeyError(f"Object has no attributes in {attributes}")


@return_on_exception(exceptions=(KeyError,), default=None)
def getattr_from_list_nofail(*args, **kwargs):
    """Call getattr_from_list without allows exceptions.

    If the specified exceptions are caught, return `default`
    instead.

    Parameters
    ----------
    See `getattr_from_list`
    """
    return getattr_from_list(*args, **kwargs)


def is_iterable(obj):
    """General iterator check"""
    return (
        not isinstance(obj, str)
        and not isinstance(obj, tuple)
        and hasattr(obj, "__iter__")
    )
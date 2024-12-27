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

Original: https://github.com/spacetelescope/stpipe/blob/main/src/stpipe/utilities.py
"""

import inspect
import os
import sys
import types

from spike.stpipe import entry_points

def resolve_step_class_alias(name):
    """
    If the input is a recognized alias, return the
    corresponding fully-qualified class name.  Otherwise
    return the input unmodified.

    Parameters
    ----------
    name : str
        If name contains "::" only the package with
        a name matching the characters before "::"
        will be searched for the matching step.

    Returns
    -------
    str
    """
    # check if the name contains a package name
    if "::" in name:
        scope, class_name = name.split("::", maxsplit=1)
    else:
        scope, class_name = None, name

    # track all found steps keyed by package name
    found_class_names = {}
    for info in entry_points.get_steps():
        if scope and info.package_name != scope:
            continue
        if info.class_alias is not None and class_name == info.class_alias:
            found_class_names[info.package_name] = info

    if not found_class_names:
        return name

    if len(found_class_names) == 1:
        return found_class_names.popitem()[1].class_name

    # class alias resolved to several possible steps
    scopes = list(found_class_names.keys())
    msg = (
        f"class alias {name} matched more than 1 step. Please provide "
        "the package name along with the step name. One of:\n"
    )
    for scope in scopes:
        msg += f"  {scope}::{name}\n"
    raise ValueError(msg)


def import_class(full_name, subclassof=object, config_file=None):
    """
    Import the Python class `full_name` given in full Python package format,
    e.g.::

        package.another_package.class_name

    Return the imported class. Optionally, if `subclassof` is not None
    and is a Python class, make sure that the imported class is a
    subclass of `subclassof`.
    """
    # Understand which class we need to instantiate. The class name is given in
    # full Python package notation, e.g.
    #   package.subPackage.subsubpackage.className
    # in the input parameter `full_name`. This means that
    #   1. We HAVE to be able to say
    #       `from package.subPackage.subsubpackage import className`
    #   2. If `subclassof` is defined, the newly imported Python class MUST be a
    #      subclass of `subclassof`, which HAS to be a Python class.

    if config_file is not None:
        sys.path.insert(0, os.path.dirname(config_file))

    try:
        full_name = full_name.strip()
        package_name, _, class_name = full_name.rpartition(".")
        if not package_name:
            raise ImportError(f"{full_name} is not a Python class")
        imported = __import__(
            package_name,
            globals(),
            locals(),
            [
                class_name,
            ],
            level=0,
        )

        step_class = getattr(imported, class_name)

        if not isinstance(step_class, type):
            raise TypeError(
                f"Object {class_name} from package {package_name} is not a class"
            )

        if not issubclass(step_class, subclassof):
            raise TypeError(
                f"Class {class_name} from package {package_name} is not a subclass of"
                f" {subclassof.__name__}"
            )
    finally:
        if config_file is not None:
            del sys.path[0]

    return step_class


def import_func(full_name):
    """
    Import the Python class `full_name` given in full Python package format,
    e.g.::

        package.subpackage.subsubpackage.function_name

    Return the imported function.
    """
    full_name = full_name.strip()
    package_name, _, func_name = full_name.rpartition(".")
    if not package_name:
        raise ImportError(f"{full_name} is not a fully qualified path to function")
    imported = __import__(
        package_name,
        globals(),
        locals(),
        [
            func_name,
        ],
        level=0,
    )

    step_func = getattr(imported, func_name)

    if not isinstance(step_func, types.FunctionType):
        raise TypeError(
            f"Object {func_name} from package {package_name} is not a function"
        )

    return step_func


def get_spec_file_path(step_class):
    """
    Given a Step (sub)class, divine and return the full path to the
    corresponding spec file. Use the fact that by convention, the spec
    file is in the same directory as the `step_class` source file. It
    has the name of the Step (sub)class and extension .spec.
    """
    try:
        step_source_file = inspect.getfile(step_class)
    except TypeError:
        return None
    step_source_file = os.path.abspath(step_source_file)

    # Since `step_class` could be defined in a file called whatever,
    # we need the source file basedir and the class name.
    dir_ = os.path.dirname(step_source_file)
    return os.path.join(dir_, step_class.__name__ + ".spec")


def find_spec_file(step_class):
    """
    Return the full path of the given Step subclass `step_class`, if
    it exists or None if it does not.
    """
    spec_file = get_spec_file_path(step_class)
    if spec_file is not None and os.path.exists(spec_file):
        return spec_file
    return None


def get_fully_qualified_class_name(cls_or_obj):
    """
    Return an object's fully-qualified class name.

    Parameters
    ----------
    cls_or_obj : type or object

    Returns
    -------
    str
        For type input, the fully-qualified name of the type.
        For other input, the fully-qualified name of the input's class.
    """
    cls = cls_or_obj if inspect.isclass(cls_or_obj) else cls_or_obj.__class__
    module = cls.__module__
    if module is None or module == str.__class__.__module__:
        return cls.__name__  # Avoid reporting __builtin__

    return module + "." + cls.__name__


class _NotSet:
    """
    Special value indicating that a parameter is not set.  Distinct
    from None. Instead of using this class use the _not_set instance
    below
    """


_not_set = _NotSet()
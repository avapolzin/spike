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

Original: https://github.com/spacetelescope/stpipe/blob/main/src/stpipe/entry_points.py
"""

import warnings
from collections import namedtuple

import importlib_metadata

STEPS_GROUP = "stpipe.steps"


StepInfo = namedtuple(
    "StepInfo",
    ["class_name", "class_alias", "is_pipeline", "package_name", "package_version"],
)


def get_steps():
    """
    Get the list of steps registered with stpipe's entry point group.  Each entry
    point is expected to return a list of tuples, where the first tuple element
    is a fully-qualified Step subclass name, the second element is an optional
    class alias, and the third is a bool indicating whether the class is to be
    listed as a pipeline in the CLI output.

    Returns
    -------
    list of StepInfo
    """
    steps = []

    for entry_point in importlib_metadata.entry_points(group=STEPS_GROUP):
        package_name = entry_point.dist.name
        package_version = entry_point.dist.version
        package_steps = []

        try:
            elements = entry_point.load()()
            package_steps = [
                StepInfo(*element, package_name, package_version)
                for element in elements
            ]

        except Exception as e:
            warnings.warn(
                f"{STEPS_GROUP} plugin from package {package_name}=={package_version} "
                "failed to load:\n\n"
                f"{e.__class__.__name__}: {e}",
                stacklevel=2,
            )

        steps.extend(package_steps)

    return steps
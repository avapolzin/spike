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

Original: https://github.com/spacetelescope/romancal/blob/main/romancal/stpipe/utilities.py
"""

import inspect
import logging
from importlib import import_module
from pkgutil import walk_packages

# Configure logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# Step classes that are not user-api steps
NON_STEPS = [
    "EngDBLogStep",
    "FunctionWrapper",
    "RomancalPipeline",
    "RomanPipeline",
    "ExposurePipeline",
    "MosaicPipeline",
    "RomanStep",
    "Pipeline",
    "Step",
    "SystemCall",
]


def all_steps():
    """List all classes subclassed from Step

    Returns
    -------
    steps : dict
        Key is the classname, value is the class
    """
    from spike.romancal.stpipe_core import RomanStep as Step

    romancal = import_module("romancal")

    steps = {}
    for module in load_sub_modules(romancal):
        more_steps = {
            klass_name: klass
            for klass_name, klass in inspect.getmembers(
                module, lambda o: inspect.isclass(o) and issubclass(o, Step)
            )
            if klass_name not in NON_STEPS
        }
        steps.update(more_steps)

    return steps


def load_sub_modules(module):
    """
    Recursively loads all submodules of a module (this is not a local import).

    Parameters
    ----------
    module : module
        A python module to walk, load

    Returns
    -------
    generator
        A generator of all submodules of module recursively until no more sub modules are found
    """

    for package_info in walk_packages(module.__path__):
        if package_info.module_finder.path.startswith(module.__path__[0]):
            package = import_module(f"{module.__name__}.{package_info.name}")

            if package_info.ispkg:
                yield from load_sub_modules(package)

            yield package
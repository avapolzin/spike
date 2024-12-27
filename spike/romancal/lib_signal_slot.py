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

Original: https://github.com/spacetelescope/romancal/blob/main/romancal/lib/signal_slot.py
"""

import inspect
import logging
from collections import namedtuple

__all__ = ["Signal", "Signals", "SignalsNotAClass"]

# Configure logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

"""Slot data structure
"""
Slot = namedtuple("Slot", ["func", "single_shot"])


class Signal:
    """Signal

    A Signal, when triggered, call the connected slots.

    Parameters
    ----------
    funcs: func[, ...]
        Remaining arguments will be functions to connect
        to this signal.

    Attributes
    ----------
    enabled: bool
        If True, the slots are called. Otherwise, nothing
        happens when triggered.

    """

    def __init__(self, *funcs):
        self._slots = list()
        self._enabled = True
        self._states = list()

        for func in funcs:
            self.connect(func)

    def emit(self, *args, **kwargs):
        """Invoke slots attached to the signal

        No return of results is expected.

        Parameters
        ----------
        args: (arg[, ...])
            Positional arguments to pass to the slots.

        kwargs: {key: value[, ...]}
            Keyword arguments to pass to the slots.
        """
        for _ in self.call(*args, **kwargs):
            pass

    __call__ = emit

    def call(self, *args, **kwargs):
        """Generator returning result of each slot connected.

        Parameters
        ----------
        args: (arg[, ...])
            Positional arguments to pass to the slots.

        kwargs: {key: value[, ...]}
            Keyword arguments to pass to the slots.

        Returns
        -------
        generator
            A generator returning the result from each slot.
        """
        for slot in self.slots:
            try:
                yield slot(*args, **kwargs)
            except Exception as exception:
                logger.debug(
                    f"Signal {self.__class__.__name_}: Slot {slot} raised {exception}"
                )

    def reduce(self, *args, **kwargs):
        """Return a reduction of all the slots

        Parameters
        ----------
        args: (arg[, ...])
            Positional arguments to pass to the slots.

        kwargs: {key: value[, ...]}
            Keyword arguments to pass to the slots.

        Returns
        -------
        result: object or (object [,...])
            The result or tuple of results. See `Notes`.


        Notes
        -----

        Each slot is given the results of the previous
        slot as a new positional argument list. As such, if multiple
        arguments are required, each slot should return a tuple that
        can then be passed as arguments to the next function.

        The keyword arguments are simply passed to each slot unchanged.

        There is no guarantee on order which the slots are invoked.

        """
        result = None
        for slot in self.slots:
            result = slot(*args, **kwargs)
            args = result
            if not isinstance(args, tuple):
                args = (args,)
        return result

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, state):
        self.set_enabled(state, push=False)

    def set_enabled(self, state, push=False):
        """Set whether signal is active or not

        Parameters
        ----------
        state: boolean
            New state of signal

        push: boolean
            If True, current state is saved.
        """
        if push:
            self._states.append(self._enabled)
        self._enabled = state

    def reset_enabled(self):
        self._enabled = self._states.pop()

    def connect(self, func, single_shot=False):
        """Connect a function to the signal
        Parameters
        ----------
        func: function or method
            The function/method to call when the signal is activated

        single_shot: bool
            If True, the function/method is removed after being called.
        """
        slot = Slot(func=func, single_shot=single_shot)
        self._slots.append(slot)

    def disconnect(self, func):
        self._slots = [slot for slot in self._slots if slot.func != func]

    def clear(self, single_shot=False):
        """Clear slots

        Parameters
        ----------
        single_shot: bool
            If True, only remove single shot
            slots.
        """
        logger.debug(f"Signal {self.__class__.__name__}: Clearing slots")
        if not single_shot:
            self._slots.clear()
        else:
            self._slots = [slot for slot in self._slots if not slot.single_shot]

    @property
    def slots(self):
        """Generator returning slots"""
        if not self.enabled:
            return

        # No recursive signalling
        self.set_enabled(False, push=True)

        try:
            for slot in self._slots:
                yield slot.func
        finally:
            # Clean out single shots
            self._slots = [slot for slot in self._slots if not slot.single_shot]
            self.reset_enabled()


class SignalsErrorBase(Exception):
    """Base Signals Error"""

    default_message = ""

    def __init__(self, *args):
        if len(args):
            super().__init__(*args)
        else:
            super().__init__(self.default_message)


class SignalsNotAClass(SignalsErrorBase):
    """Must add a Signal Class"""

    default_message = "Signal must be a class."


class Signals(dict):
    """Manage the signals."""

    def __setitem__(self, key, value):
        if key not in self:
            super().__setitem__(key, value)
        else:
            logger.warning(f'Signals: signal "{key}" already exists.')

    def __getattr__(self, key):
        for signal in self:
            if signal.__name__ == key:
                return self[signal]
        raise KeyError(f"{key}")

    def add(self, signal_class, *args, **kwargs):
        if inspect.isclass(signal_class):
            self.__setitem__(signal_class, signal_class(*args, **kwargs))
        else:
            raise SignalsNotAClass
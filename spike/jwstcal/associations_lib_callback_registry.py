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

Original: https://github.com/spacetelescope/jwst/blob/main/jwst/associations/lib/callback_registry.py
"""

from spike.jwstcal.lib_signal_slot import Signal

__all__ = ['CallbackRegistry']


class CallbackRegistry():
    """Callback registry"""

    def __init__(self):
        self.registry = dict()

    def add(self, event, callback):
        """Add a callback to an event"""
        try:
            signal = self.registry[event]
        except KeyError:
            signal = Signal()
        signal.connect(callback)
        self.registry[event] = signal

    def reduce(self, event, *args):
        """Perform a reduction on the event args

        Parameters
        ----------
        args : [arg[,...]]
            The args to filter

        Returns
        -------
        The reduced results.
        If no results can be determined,
        such as if no callbacks were registered,
        `None` is returned.

        Notes
        -----
        Each function is given the results of the previous
        function. As such, if the data has more than one
        object, the return of each function should be a tuple that can
        then be passed as arguments to the next function.

        There is no guarantee on order which the registered
        callbacks are made. Currently, the callbacks are in a list.
        Hence, the callbacks will be called in the order registered.

        """
        result = self.registry[event].reduce(*args)
        return result

    def add_decorator(self, event):
        """Add callbacks by decoration

        Parameters
        ----------
        event : str
            The name of event to attach the object to.
        """
        def decorator(func):
            self.add(event, func)
            return func
        return decorator

    __call__ = add_decorator
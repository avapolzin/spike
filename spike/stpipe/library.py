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

Original: https://github.com/spacetelescope/jwst/blob/main/jwst/datamodels/library.py
"""

import abc
import copy
import json
import os.path
import tempfile
import warnings
from collections.abc import Iterable, MutableMapping
from pathlib import Path
from types import MappingProxyType

import asdf

from spike.stpipe.datamodel import AbstractDataModel

__all__ = [
    "LibraryError",
    "BorrowError",
    "ClosedLibraryError",
    "NoGroupID",
    "AbstractModelLibrary",
]


class LibraryError(Exception):
    """
    Generic ModelLibrary related exception
    """


class BorrowError(LibraryError):
    """
    Exception indicating an issue with model borrowing
    """


class ClosedLibraryError(LibraryError):
    """
    Exception indicating a library method was used outside of a
    ``with`` context (that "opens" the library).
    """


class NoGroupID(LibraryError):
    """
    Exception to use when a model has no "group_id".
    """


class _Ledger(MutableMapping):
    """
    A "ledger" used for tracking borrowed out models.

    Each model has a unique "index" in the library because
    the order of the models in the library never changes.
    This "index" can be used to track the model.

    For ease-of-use this ledger maintains 2 mappings:

        - id (the id(model) result) to model index
        - index to model

    The "index to model" mapping keeps a reference to every
    model in the ledger (which allows id(model) to be consistent).

    The ledger is a MutableMapping that supports look up of:
        - index for a model
        - model for an index
    """

    def __init__(self):
        self._id_to_index = {}
        self._index_to_model = {}

    def __getitem__(self, model_or_index):
        if isinstance(model_or_index, int):
            return self._index_to_model[model_or_index]
        return self._id_to_index[id(model_or_index)]

    def __setitem__(self, index, model):
        self._index_to_model[index] = model
        self._id_to_index[id(model)] = index

    def __delitem__(self, model_or_index):
        if isinstance(model_or_index, int):
            index = model_or_index
            model = self._index_to_model[index]
        else:
            model = model_or_index
            index = self._id_to_index[id(model)]
        del self._id_to_index[id(model)]
        del self._index_to_model[index]

    def __iter__(self):
        # only return indexes
        return iter(self._index_to_model)

    def __len__(self):
        return len(self._id_to_index)


class AbstractModelLibrary(abc.ABC):
    """
    A "library" of models (loaded from an association file).

    Do not anger the librarian!

    The library owns all models from the association and it will handle
    opening and closing files.

    Models can be "borrowed" from the library (by iterating through the
    library or "borrowing" a specific model). However the library must be
    "open" (used in a ``with`` context)  to borrow a model and the model
    must be "shelved" before the library "closes" (the ``with`` context exits).

    >>> with library:   # doctest: +SKIP
            model = library.borrow(0)  # borrow the first model
            # do stuff with the model
            library.shelve(model, 0)  # return the model

    Failing to "open" the library will result in a `ClosedLibraryError`.

    Failing to "return" a borrowed model will result in a `BorrowError`.
    """

    def __init__(
        self,
        init,
        asn_exptypes=None,
        asn_n_members=None,
        on_disk=False,
        temp_directory=None,
        **datamodels_open_kwargs,
    ):
        """
        Create a new ModelLibrary based on the provided "init".

        Parameters
        ----------
        init : str or Path or list (of DataModels)
            If a string or Path this should point to a valid
            association file. If a list of models consider continuing
            to use the list instead of making a library (the list will
            be more efficient and easier to use).

        asn_exptypes : list of str, optional
            List of "exptypes" to load from the "init" value. Any
            association member with a "exptype" that matches (case
            insensitive) a value in this list will be available
            through the library.

        asn_n_members : int, optional
            Number of association members to include in the library.
            This filtering will occur after "asn_exptypes" is applied.
            By default all members will be included.

        on_disk : bool, optional, default=False
            When enabled, keep the models in the library "on disk",
            writing out temporary files when the models are "shelved".
            This option is only compatible with models loaded from
            an association (not a list of models).

        temp_directory : str or Path, optional
            The temporary directory in which to store models when
            "on_disk" is enabled. By default a
            ``tempfile.TemporaryDirectory`` will be created in the
            working directory.

        **datamodels_open_kwargs : dict
            Keyword arguments that will provided to ``_datamodels_open``
            when models are opened.
        """
        self._on_disk = on_disk
        self._open = False
        self._ledger = _Ledger()
        self._loaded_models = {}

        self._datamodels_open_kwargs = datamodels_open_kwargs

        if on_disk:
            if temp_directory is None:
                self._temp_dir = tempfile.TemporaryDirectory(dir="")
                self._temp_path = Path(self._temp_dir.name)
            else:
                self._temp_path = Path(temp_directory)
            self._temp_filenames = {}

        if asn_exptypes is not None:
            # if a single string, treat this as a single item list
            if isinstance(asn_exptypes, str):
                asn_exptypes = [asn_exptypes]
            # convert these to lower case to allow case insensitive matching below
            asn_exptypes = [exptype.lower() for exptype in asn_exptypes]

        if isinstance(init, (str, Path)):
            # init is an association filename (or path)
            asn_path = os.path.abspath(os.path.expanduser(os.path.expandvars(init)))
            self._asn_dir = os.path.dirname(asn_path)

            # load association
            asn_data = self._load_asn(asn_path)

            # store the basename of the input file as the table_name
            asn_data["table_name"] = os.path.basename(asn_path)
        elif isinstance(init, MutableMapping):
            # init is an association "dictionary"
            # we will modify the asn below so do a deep copy
            asn_data = copy.deepcopy(init)
            self._asn_dir = os.path.abspath(".")
        elif isinstance(init, self.__class__):
            raise ValueError(f"Invalid init {init}")
        elif isinstance(init, Iterable):  # assume a list of models
            if on_disk:
                raise ValueError("on_disk cannot be used for a list of models")

            # init is a list of models, this type of input ignores much of
            # the benefits of this class but is common in test code.

            # make a fake asn from the models
            members = []
            for index, model_or_filename in enumerate(init):
                if asn_n_members is not None and len(members) == asn_n_members:
                    break
                if isinstance(model_or_filename, (str, Path)):
                    # Supporting a list of filenames by opening them as models
                    # has issues, if this is a widely supported mode (vs providing
                    # an association) it might make the most sense to make a fake
                    # association with the filenames at load time.
                    model = self._datamodels_open(
                        model_or_filename, **self._datamodels_open_kwargs
                    )
                else:
                    model = model_or_filename

                exptype = self._model_to_exptype(model)

                if asn_exptypes is not None and exptype.lower() not in asn_exptypes:
                    continue

                members.append(
                    {
                        "expname": self._model_to_filename(model),
                        "exptype": exptype,
                        "group_id": self._to_group_id(model, len(members)),
                    }
                )

                self._loaded_models[len(self._loaded_models)] = model

            # since we've already filtered by asn type and n members reset these values
            asn_exptypes = None
            asn_n_members = None

            # make a very limited fake association
            asn_data = {
                "products": [
                    {
                        "members": members,
                    }
                ],
            }
            self._asn_dir = None
        else:
            raise ValueError(f"Invalid init {init}")

        if asn_exptypes is not None:
            asn_data["products"][0]["members"] = [
                m
                for m in asn_data["products"][0]["members"]
                if m["exptype"] in asn_exptypes
            ]

        if asn_n_members is not None:
            asn_data["products"][0]["members"] = asn_data["products"][0]["members"][
                :asn_n_members
            ]

        self._asn = asn_data
        self._members = self._asn["products"][0]["members"]

        for index, member in enumerate(self._members):
            if "group_id" not in member:
                filename = os.path.join(self._asn_dir, member["expname"])
                member["group_id"] = self._to_group_id(filename, index)

        if not on_disk:
            # if models were provided as input, assign the members here
            # now that the fake asn data is complete
            for i in self._loaded_models:
                self._assign_member_to_model(self._loaded_models[i], self._members[i])

    def __del__(self):
        if hasattr(self, "_temp_dir"):
            self._temp_dir.cleanup()

    @property
    def asn(self):
        """
        Association dictionary used to create the library.

        Note that changes to the models may cause this information
        to fall "out-of-sync" with the models. For example, borrowing
        and changing a models "group_id" metadata will not change
        the "group_id" entry for the member at the same index in the
        association dictionary returned for this property.

        This is "read-only" to reduce the chances that the
        information in this dictionary will conflict with
        the model metadata.
        """

        # return a "read only" association
        def _to_read_only(obj):
            if isinstance(obj, dict):
                return MappingProxyType(obj)
            if isinstance(obj, list):
                return tuple(obj)
            return obj

        return asdf.treeutil.walk_and_modify(self._asn, _to_read_only)

    @property
    def group_names(self):
        """
        A ``set`` of association member "group_id" values

        This property (similar to ``asn``) can fall "out-of-sync"
        with the model metadata. The names returned here will
        only reflect the "group_id" at the time of library creation.
        """
        names = set()
        for member in self._members:
            names.add(member["group_id"])
        return names

    @property
    def group_indices(self):
        """
        A ``dict`` with "group_id" as keys. Each value contains
        a ``list`` of indices of members that shared that "group_id".

        Note that this is based on the member entries in the association
        used to create the ModelLibrary. Updating the "group_id" of a model
        in the library will NOT change the values returned by this property
        (and will not change the association data available at ``asn``).
        """
        group_dict = {}
        for i, member in enumerate(self._members):
            group_id = member["group_id"]
            if group_id not in group_dict:
                group_dict[group_id] = []
            group_dict[group_id].append(i)
        return group_dict

    def __len__(self):
        return len(self._members)

    def borrow(self, index):
        """
        "borrow" a model from the library.

        Every model "borrowed" from the library must be returned before
        the library is closed (see the exceptions described below).

        For an "on_disk" library a calling this function will cause
        the corresponding model to be loaded from disk.

        Parameters
        ----------
        index : int
            The index of the model within the library. As the library
            size does not change this is unique to this model for this
            library.

        Returns
        -------
        model : DataModel

        Raises
        ------
        `ClosedLibraryError`
            If the library is not "open" (used in a ``with`` context).

        `BorrowError`
            If the model at this index is already "borrowed".
        """
        if not self._open:
            raise ClosedLibraryError("ModelLibrary is not open")

        # if model was already borrowed, raise
        if index in self._ledger:
            raise BorrowError("Attempt to double-borrow model")

        if self._on_disk:
            if index in self._temp_filenames:
                model = self._datamodels_open(
                    self._temp_filenames[index], **self._datamodels_open_kwargs
                )
            else:
                model = self._load_member(index)
        else:
            if index in self._loaded_models:
                # if this model is in memory, return it
                model = self._loaded_models[index]
            else:
                model = self._load_member(index)
                self._loaded_models[index] = model

        self._ledger[index] = model
        return model

    def _temp_path_for_model(self, model, index):
        """
        Determine the temporary path to use to save a model
        at the provided index in the library.
        """
        model_filename = self._model_to_filename(model)
        subpath = self._temp_path / f"{index}"
        if not os.path.exists(subpath):
            os.makedirs(subpath)
        return subpath / model_filename

    def shelve(self, model, index=None, modify=True):
        """
        "shelve" a model, returning it to the library.

        All borrowed models must be "shelved" before the library is
        closed (see notes about exceptions below).

        For an "on_disk" model shelving a model may cause
        a temporary file to be written (see "modify" below).

        Parameters
        ----------
        model : DataModel
            DataModel to return to the library at the provided index.

        index : int, optional
            The index within the library where the model will be stored.
            If the same model (checked by ``id(model)``) was previously
            borrowed and the index is not provided, the borrowed index
            will be used. If providing a new DataModel (one not borrowed
            from the library) the index must be provided, and the new
            model replaces the prior model at that index.

        modify : bool, optional, default=True
            For an "on_disk" library, temporary files will only be written
            when modify is True. For a library that is not "on_disk"
            this option has no effect and any modifications made to the model
            while it was borrowed will persist.

        Raises
        ------
        `ClosedLibraryError`
            If the library is not "open" (used in a ``with`` context).

        `BorrowError`
            If an unknown model is provided (without an index) or
            if the model at the provided index has not been "borrowed"
        """
        if not self._open:
            raise ClosedLibraryError("ModelLibrary is not open")

        if index is None:
            try:
                index = self._ledger[model]
            except KeyError:
                raise BorrowError("Attempt to shelve an unknown model")

        if index not in self._ledger:
            raise BorrowError("Attempt to shelve model at a non-borrowed index")

        if modify:
            if self._on_disk:
                temp_filename = self._temp_path_for_model(model, index)
                model.save(temp_filename)

                # if we have an old model for this index that was saved
                # in the temporary directory and this model has a different
                # filename, remove the old file.
                if index in self._temp_filenames:
                    old_filename = self._temp_filenames[index]
                    if old_filename != temp_filename:
                        os.remove(old_filename)

                self._temp_filenames[index] = temp_filename
            else:
                self._loaded_models[index] = model

        del self._ledger[index]

    def __iter__(self):
        """
        Iterate through the models in an (open) library by "borrowing"
        each one, one at a time.

        Returns
        -------
        model_iter : generator
            Generator that returns "borrowed" models. Failing to "shelve"
            the models produced by this generator will result in a
            `BorrowError`.
        """
        for i in range(len(self)):
            yield self.borrow(i)

    def _assign_member_to_model(self, model, member):
        """
        Assign association member information to an opened model.

        This will be called:

            - when a model is loaded (for the first time) in ``_load_member``
            - when the library is created (if the library was provided a
              list of open models)

        This will assign the following metadata attributes (setting
        for example ``model.meta.group_id`` to the value of
        ``member["group_id"]``):

            - group_id
            - exptype
            - tweakreg_catalog

        and (when available from the association) assign the following
        metadata attributes based on the association information:

            - set ``meta.asn.table_name`` to ``asn["table_name"]``
            - set ``meta.asn.pool_name`` to ``asn["pool_name"]``

        Parameters
        ----------
        model : DataModel
            Model to be updated (in place).

        member : dict
            Dictionary containing contents of the "member" entry
            (include "exptype", "expname", "group_id", etc...)
        """
        for attr in ("group_id", "tweakreg_catalog", "exptype"):
            if attr in member:
                setattr(model.meta, attr, member[attr])

        if not hasattr(model.meta, "asn"):
            model.meta.asn = {}

        if "table_name" in self.asn:
            model.meta.asn["table_name"] = self.asn["table_name"]
        if "asn_pool" in self.asn:
            model.meta.asn["pool_name"] = self.asn["asn_pool"]

    def _load_member(self, index):
        """
        Load a model for the association member at the provided index.

        This will be called when the model at the provided index:
            - is not already loaded
            - does not have a temporary file

        Parameters
        ----------
        index : int

        Returns
        -------
        model : DataModel
        """
        member = self._members[index]
        filename = os.path.join(self._asn_dir, member["expname"])

        model = self._datamodels_open(filename, **self._datamodels_open_kwargs)

        self._assign_member_to_model(model, member)

        return model

    def _save(self, path, **kwargs):
        """
        .. warning:: This save is NOT used by Step/Pipeline. This is
                     intentional as the Step/Pipeline has special requirements.

        For now this is a very basic "save". It does not:

            - check that the library contains no duplicate filenames
            - propagate asn_pool and other non-member asn information

        It will save:
            - models with filenames determined by ``_model_to_filename``
            - a very simple association that contains only 1 product that
              lists ``expname`` ``exptype`` and ``group_id``  for each model
              in a file named "asn.json".

        Parameters
        ----------
        path : Path or str
            Directory in which to store the models and generated
            association for this library.

        Returns
        -------
        association_path : Path
            The path to the saved association file.
        """
        if isinstance(path, str):
            path = Path(path)
        if not path.exists():
            path.mkdir()
        members = []
        with self:
            for i, model in enumerate(self):
                mfn = Path(self._model_to_filename(model))
                model.save(path / mfn, **kwargs)
                members.append(
                    {
                        "expname": str(mfn),
                        "exptype": self._model_to_exptype(model),
                        "group_id": self._model_to_group_id(model),
                    }
                )
                self.shelve(model, i, modify=False)
        asn_data = {"products": [{"members": members}]}
        asn_path = path / "asn.json"
        with open(asn_path, "w") as f:
            json.dump(asn_data, f)
        return asn_path

    def get_crds_parameters(self):
        """
        Get the "crds_parameters" from either:
            - the first "science" member (based on exptype)
            - the first model (if no "science" member is found)

        If no "science" members are found in the library a ``UserWarning``
        will be issued.

        Returns
        -------
        crds_parameters : dict
            The result of ``get_crds_parameters`` called on the selected
            model.
        """
        with self:
            science_index = None
            for i, member in enumerate(self._members):
                if member["exptype"].lower() == "science":
                    science_index = i
                    break
            if science_index is None:
                warnings.warn(
                    "get_crds_parameters failed to find any science members. "
                    "The first model was used to determine the parameters",
                    UserWarning,
                )
                science_index = 0
            model = self.borrow(science_index)
            parameters = model.get_crds_parameters()
            self.shelve(model, science_index, modify=False)
        return parameters

    def finalize_result(self, step, reference_files_used):
        """
        Called from `stpipe.Step.run` after `stpipe.Step.process` has
        completed. This method will call `stpipe.Step.finalize_result`
        for each model in the library.

        Parameters
        ----------
        step : Step
            The step calling this method.

        reference_files_used : list
            List of reference files used during the execution of this
            step.
        """
        with self:
            for i, model in enumerate(self):
                step.finalize_result(model, reference_files_used)
                self.shelve(model, i)

    def __enter__(self):
        """
        "open" the library. This is required for any "borrow" and "shelve"
        calls. While the library is "open" it will track which models are
        borrowed and raise a `BorrowError` if an attempt is made to close
        the library before all borrowed models are returned.
        """
        self._open = True
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        "close" the library.

        Raises
        ------
        `BorrowError`
            If the library "closes" and one or more models have not been
            "shelved" (returned) this exception will be raised.
        """
        self._open = False
        if exc_value:
            # if there is already an exception, don't worry about checking the ledger
            # instead allowing the calling code to raise the original error to provide
            # a more useful feedback without any chained ledger exception about
            # un-returned models
            return
        if self._ledger:
            raise BorrowError(
                f"ModelLibrary has {len(self._ledger)} un-returned models"
            )

    def map_function(self, function, modify=True):
        """
        Call a function once for each model in the library.

        Similar to the built-in ``map`` function this applies the
        function "function" to each model in the library by iterating
        through the models (yielding on each function call).

        Parameters
        ----------
        function : callable
            A function that accepts 2 arguments, ``model`` and ``index``

        modify : bool, optional, default=True
            For an "on_disk" library, temporary files will only be written
            when modify is True. For a library that is not "on_disk"
            this option has no effect and any modifications made to the model
            while it was borrowed will persist.

        Returns
        -------
        result_iter : generator
            A generator that will return function results. This can be
            converted to a list ``list(result_iter)`` to get the results
            of all the function calls (ordered the same as the models in
            the library).
        """
        with self:
            for index, model in enumerate(self):
                try:
                    yield function(model, index)
                finally:
                    # this is in a finally to allow cleanup if the generator is
                    # deleted after it finishes (when it's not fully consumed)
                    self.shelve(model, index, modify)
                # remove the local reference to model here to allow it
                # to be garbage collected before the next model is generated
                del model

    def _model_to_filename(self, model):
        """
        Determine the "filename" for a model. This will be used
        when writing temporary files (if the library is "on_disk")
        and for the ``save`` method (see the method for a note about
        how this is not used for the pipeline code).

        By default this method will return ``model.meta.filename``
        or "model.asdf" (if ``model.meta.filename`` is None).

        Parameters
        ----------
        model : DataModel

        Returns
        -------
        filename : str
        """
        model_filename = model.meta.filename
        if model_filename is None:
            model_filename = "model.asdf"
        return model_filename

    def _to_group_id(self, model_or_filename, index):
        if isinstance(model_or_filename, AbstractDataModel):
            getter = self._model_to_group_id
        else:
            getter = self._filename_to_group_id

        try:
            return getter(model_or_filename)
        except NoGroupID:
            return f"exposure{index + 1:04d}"

    def _model_to_exptype(self, model):
        """
        Compute "exptype" from a model using the DataModel interface.

        This will be called for every model in the library:
            - when the library is created from a list of models
            - when _save is called
        In both cases the models are all in memory and this method
        can use the in memory DataModel to determine the "exptype"
        (likely ``model.meta.exptype``).

        Parameters
        ----------
        model : DataModel

        Returns
        -------
        exptype : str
            Exposure type (for example "SCIENCE").
        """
        return getattr(model.meta, "exptype", "SCIENCE")

    @property
    @abc.abstractmethod
    def crds_observatory(self):
        """
        Return the name of the observatory as a string

        Returns
        -------
        observatory : str
        """

    @abc.abstractmethod
    def _datamodels_open(self, filename, **kwargs):
        """
        Open a model from a filename

        Parameters
        ----------
        filename : str or Path
            Filename from which to load a model.

        **kwargs : dict, optional
            Arguments to be passed to any lower-level function that
            opens a model.
        """

    @classmethod
    @abc.abstractmethod
    def _load_asn(cls, filename):
        """
        Load an association from a filename

        Parameters
        ----------
        filename : str or Path
            Filename from which to load an association
        """

    @abc.abstractmethod
    def _filename_to_group_id(self, filename):
        """
        Compute a "group_id" for a DataModel in filename.

        This will be called for every member in the association
        when the library is created if the member entry does not
        contain a "group_id" (this is the most efficient mode).
        Ideally this method should avoid opening the filename as
        a DataModel and instead take "short-cuts" to read only
        the "group_id" (from FITS or ASDF headers).

        If no "group_id" can be determined `NoGroupID` should be
        raised (to allow the library to assign a unique "group_id").

        Parameters
        ----------
        filename : str or Path
            Filename containing a DataModel

        Returns
        -------
        group_id : str
            "group_id" (used for ``group_names`` and ``group_indices``)
            for the model in the provided filename.
        """

    @abc.abstractmethod
    def _model_to_group_id(self, model):
        """
        Compute a "group_id" from a model using the DataModel interface.

        This will be called for every model in the library:
            - when the library is created from a list of models
            - when _save is called
        In both cases the models are all in memory and this method
        can use the in memory DataModel to determine the "group_id"
        (likely ``model.meta.group_id``).

        If no "group_id" can be determined `NoGroupID` should be
        raised (to allow the library to assign a unique "group_id").

        Parameters
        ----------
        model : DataModel

        Returns
        -------
        group_id : str
            "group_id" (used for ``group_names`` and ``group_indices``)
            for the model in the provided filename.
        """
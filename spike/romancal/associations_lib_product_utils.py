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

Original: https://github.com/spacetelescope/romancal/blob/main/romancal/associations/lib/product_utils.py
"""

import copy
import logging
import warnings
from collections import Counter, defaultdict

import spike.romancal.associations_config as config
from spike.romancal.associations_lib_diff import compare_product_membership

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def sort_by_candidate(asns):
    """Sort associations by candidate

    Parameters
    ----------
    asns : [Association[,...]]
        List of associations

    Returns
    -------
    sorted_by_candidate : [Associations[,...]]
        New list of the associations sorted.

    Notes
    -----
    The current definition of candidates allows strictly lexigraphical
    sorting:
    aXXXX > cXXXX > oXXX

    If this changes, a comparison function will need be implemented
    """
    return sorted(asns, key=lambda asn: asn["asn_id"])


def get_product_names(asns):
    """Return product names from associations and flag duplicates

    Parameters
    ----------
    asns : [`Association`[, ...]]

    Returns
    -------
    product_names, duplicates : set(str[, ...]), [str[,...]]
        2-tuple consisting of the set of product names and the list of duplicates.
    """
    product_names = [asn["products"][0]["name"] for asn in asns]

    dups = [name for name, count in Counter(product_names).items() if count > 1]
    if dups:
        logger.debug("Duplicate product names: %s", dups)

    return set(product_names), dups


def prune_duplicate_associations(asns):
    """Remove duplicate associations in favor of lower level versions

    Main use case: For Level 3 associations, multiple associations with the
    same membership, but different levels, can be created. Remove duplicate
    associations of higher level.

    The assumption is that there is only one product per association, before
    merging.

    Parameters
    ----------
    asns : [Association[,...]]
        Associations to prune

    Returns
    -------
    pruned : [Association[,...]]
        Pruned list of associations

    """
    ordered_asns = sort_by_candidate(asns)
    pruned = list()
    while True:
        try:
            original = ordered_asns.pop()
        except IndexError:
            break
        pruned.append(original)
        to_prune = list()
        for asn in ordered_asns:
            try:
                compare_product_membership(original["products"][0], asn["products"][0])
            except AssertionError:
                continue
            to_prune.append(asn)
        for prune in to_prune:
            ordered_asns.remove(prune)

    return pruned


def prune_duplicate_products(asns):
    """Remove duplicate products in favor of higher level versions

    The assumption is that there is only one product per association, before
    merging

    Parameters
    ----------
    asns: [Association[,...]]
        Associations to prune

    Returns
    pruned: [Association[,...]]
        Pruned list of associations

    """
    product_names, dups = get_product_names(asns)
    if not dups:
        return asns

    warnings.warn(f"Duplicate associations exist: {dups}", RuntimeWarning)
    if config.DEBUG:
        warnings.warn(
            'Duplicate associations will have "dupXXX" prepended to their names, where'
            ' "XXX" is a 3-digit sequence.'
        )
    else:
        warnings.warn(
            "Duplicates will be removed, leaving only one of each.", RuntimeWarning
        )

    pruned = copy.copy(asns)
    to_prune = defaultdict(list)
    for asn in asns:
        product_name = asn["products"][0]["name"]
        if product_name in dups:
            to_prune[product_name].append(asn)

    dup_count = 0
    for product_name, asns_to_prune in to_prune.items():
        asns_to_prune = sort_by_candidate(asns_to_prune)
        for asn in asns_to_prune[1:]:
            if config.DEBUG:
                dup_count += 1
                asn.asn_name = f"dup{dup_count:03d}_{asn.asn_name}"
            else:
                pruned.remove(asn)

    return pruned
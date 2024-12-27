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

Original: https://github.com/spacetelescope/jwst/blob/main/jwst/associations/lib/prune.py
"""


import logging
from collections import defaultdict

import spike.jwstcal.associations_lib_diff as diff
from spike.jwstcal.associations_lib_product_utils import get_product_names, sort_by_candidate
import spike.jwstcal.associations_config as config

__all__ = ['prune']

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# Duplicate association counter
# Used in function `prune_remove`
DupCount = 0

def prune(asns):
    """Remove duplicates and subset associations

    Situations where extraneous associations can occur are:

    - duplicate memberships
    - duplicate product names

    Associations with different product names but same memberships arise when
    different levels of candidates gather the same membership, such as
    OBSERVATION vs. GROUP. Associations of the lower level candidate are preferred.

    Associations with the same product name can occur in Level 2 when both an OBSERVATION
    candidate and a BACKGROUND candidate associations are created. The association that is
    a superset of members is the one chosen.

    Parameters
    ----------
    asns : [Association[,...]]
        Associations to prune

    Returns
    -------
    pruned : [Association[,...]]
        Pruned list of associations
    """
    pruned = prune_duplicate_associations(asns)
    pruned = prune_duplicate_products(pruned)
    return pruned

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
    known_dups, valid_asns = identify_dups(asns)

    ordered_asns = sort_by_candidate(valid_asns)
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
                diff.compare_product_membership(original['products'][0], asn['products'][0])
            except AssertionError:
                continue
            to_prune.append(asn)
        prune_remove(ordered_asns, to_prune, known_dups)

    return pruned + known_dups


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
    known_dups, valid_asns = identify_dups(asns)

    product_names, dups = get_product_names(valid_asns)
    if not dups:
        return asns

    ordered_asns = sort_by_candidate(valid_asns)
    asn_by_product = defaultdict(list)
    for asn in ordered_asns:
        asn_by_product[asn['products'][0]['name']].append(asn)

    full_prune = list()
    for product in dups:
        dup_asns = asn_by_product[product]
        to_keep = dup_asns.copy()
        for asn in dup_asns:
            # Association has been removed, ignore
            if asn in full_prune:
                continue

            # Check against the set of associations to be kept.
            to_prune = list()
            for entrant in to_keep:
                if entrant == asn:
                    continue

                # Check for differences. If none, then the associations are exact duplicates.
                try:
                    diff.compare_product_membership(asn['products'][0], entrant['products'][0])
                except diff.MultiDiffError as diffs:
                    # If one is a pure subset, remove the smaller association.
                    if len(diffs) == 1 and isinstance(diffs[0], diff.SubsetError):
                        if len(entrant['products'][0]['members']) > len(asn['products'][0]['members']):
                            asn, entrant = entrant, asn
                        to_prune.append(entrant)
                        continue

                    # If the difference is only in suffix, this is an acceptable duplication of product names.
                    # Trap and do not report.
                    try:
                        diff.compare_product_membership(asn['products'][0], entrant['products'][0], strict_expname=False)
                    except diff.MultiDiffError:
                        # Something is different. Report but do not remove.
                        logger.warning('Following associations have the same product name but significant differences.')
                        logger.warning('Association 1: %s', asn)
                        logger.warning('Association 2: %s', entrant)
                        logger.warning('Diffs: %s', diffs)

                else:
                    # Associations are exactly the same. Discard the logically lesser one.
                    # Due to the sorting, this should be the current `asn`
                    to_prune.append(entrant)

            # Update lists.
            full_prune.extend(to_prune)
            for asn in to_prune:
                to_keep.remove(asn)

    prune_remove(ordered_asns, full_prune, known_dups)
    return ordered_asns + known_dups


def prune_remove(remove_from, to_remove, known_dups):
    """Remove or rename associations to be pruned

    Default behavior is to remove associations listed in the `to_remove`
    list from the `remove_from` list.

    However, if `config.DEBUG` is `True`, that association is simply
    renamed, adding the string "dupXXXXX" as a prefix to the association's
    name.

    Parameters
    ----------
    remove_from : [Association[,...]]
        The list of associations from which associations will be removed.
        List is modified in-place.

    to_remove : [Association[,...]]
        The list of associations to remove from the `remove_from` list.

    known_dups : [Association[,...]]
        Known duplicates. New ones are added by this function
        if debugging is in effect.
    """
    global DupCount

    if to_remove:
        logger.debug('Duplicate associations found: %s', to_remove)
    for asn in to_remove:
        remove_from.remove(asn)
        if config.DEBUG:
            DupCount += 1
            asn.asn_name = f'dup{DupCount:05d}_{asn.asn_name}'
            known_dups.append(asn)


def identify_dups(asns):
    """Separate associations based on whether they have already been identified as dups

    Parameters
    ----------
    asns: [Association[,...]]
        Associations to prune

    Returns
    identified, valid : [Association[,...]], [Association[,...]]
        Dup-identified and valid associations
    """
    identified = list()
    valid = list()
    for asn in asns:
        if asn.asn_name.startswith('dup'):
            identified.append(asn)
        else:
            valid.append(asn)
    return identified, valid
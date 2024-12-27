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

Original: https://github.com/spacetelescope/jwst/blob/main/jwst/model_blender/_schemautil.py
"""

from stdatamodels import schema as dm_schema

def parse_schema(schema):
    """
    Parse an ASDF schema for model blending instructions.

    Parameters
    ----------
    schema : dict
        Dictionary containing an ASDF schema.

    Returns
    -------
    attr_to_column: dict
        one-to-one mapping of metadata attributes
        (full dotted-paths) to table columns. For example
        {'meta.observation.time': 'TIME-OBS'} for storing
        the 'meta.observation.time' attributes in a 'TIME-OBS'
        column.

    attr_to_rule: dict
        mapping of metadata attribute to blend rule
        type. For example {'meta.observation.time': 'mintime'}
        will combine all 'meta.observation.time' attributes
        using the 'mintime' rule.

    schema_ignores: list
        list of attributes that will not be blended
    """
    def callback(subschema, path, combiner, ctx, recurse):
        if len(path) <= 1:
            return  # ignore top-level (non-meta) attributes
        if path[0] != 'meta':
            return  # ignore non-meta attributes
        if 'items' in path:
            return  # ignore attributes in arrays
        if subschema.get('properties'):
            return  # ignore ObjectNodes

        # strip trailing path if there's a combiner
        for schema_combiner in ['anyOf', 'oneOf']:
            if schema_combiner in path:
                path = path[:path.index(schema_combiner)]
                break

        # construct the metadata attribute path
        attr = '.'.join(path)

        if subschema.get('type') == 'array':
            ctx['ignores'].append(attr)
            return  # ignore ListNodes

        # if 'blend_rule' is defined, make a 'blend'
        if 'blend_rule' in subschema:
            ctx['blends'][attr] = subschema['blend_rule']

        # if 'blend_table' is defined (and truthy), add a column
        if subschema.get('blend_table'):
            ctx['columns'][attr] = subschema.get('fits_keyword', attr)

    ctx = {
        'columns': {},
        'blends': {},
        'ignores': [],
    }
    dm_schema.walk_schema(schema, callback, ctx)
    return ctx['columns'], ctx['blends'], ctx['ignores']
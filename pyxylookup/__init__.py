# -*- coding: utf-8 -*-

# pyxylookup

"""
pyxylookup library
~~~~~~~~~~~~~~~~~~~~~

pyxylookup is a Python client for the OBIS xylookup API.

Usage::

        # Import library
        import pyxylookup

        ## use advanced logging
        ### setup first
        import requests
        import logging
        import httplib as http_client
        http_client.HTTPConnection.debuglevel = 1
        logging.basicConfig()
        logging.getLogger().setLevel(logging.DEBUG)
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True
        ### then make request
        from pyxylookup import lookupxy
        lookup_xy([[0,0], [1,1]])
"""

__version__ = '0.1.0.0'
__title__ = 'pyxylookup'
__author__ = 'Samuel Bosch'
__license__ = 'MIT'

import umsgpack as msgpack
import numpy as np
import requests


def lookup(points, shoredistance=True, grids=True, areas=False, asdataframe=False):

    # TODO limit number of points send to 100000

    points = np.asarray(points)
    if not points or points.shape[1] == 0 or points.shape[2] == 2:
        raise ValueError("Points should be a non-empty nested array of longitude latitude coordinates")

    try:
        points = points.astype(float)
    except ValueError:
        raise ValueError("Points should be numeric")

    if not shoredistance and not grids and not areas:
        raise TypeError("At least one of shoredistance, grids or areas should be True")

    points, duplicate_indices = np.unique(points, return_inverse=True, axis=0)

    nan = np.isnan(points)
    nan = (nan[:, 0] | nan[:, 1])
    points = points[~nan]

    data = {
        'points': points,
        'shoredistance': shoredistance,
        'grids': grids,
        'areas': areas
    }
    msgdata = msgpack.dumps(data)
    headers = {'content-type': 'application/msgpack'}
    r = requests.post('http://api.iobis.org/xylookup/', data=msgdata, headers=headers)
    if r.status_code == 200:
        result = msgpack.loads(r.content)

        for nani in np.where(nan):
            result.insert(nani, {})

        result = result[duplicate_indices]
        if asdataframe:
            try:
                import pandas as pd
                df = pd.DataFrame.from_records(result)
                df_list = []
                if shoredistance:
                    df_list.append(pd.DataFrame({'shoredistance': df[b'shoredistance']}))
                if grids:
                    df_list.append(pd.DataFrame.from_records(df[b'grids']))
                if areas:
                    df_list.append(pd.DataFrame({'areas':df[b'areas']}))
                result = pd.concat(df_list, axis=1)
                return result
            except ImportError:
                raise ImportError("pandas is required for the 'asdataframe' parameter in the lookup function")
        else:
            return result
    else:
        raise Exception(r.content)

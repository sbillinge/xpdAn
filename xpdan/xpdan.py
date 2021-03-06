##############################################################################
#
# xpdan            by Billinge Group
#                   Simon J. L. Billinge sb2896@columbia.edu
#                   (c) 2016 trustees of Columbia University in the City of
#                        New York.
#                   All rights reserved
#
# File coded by:    Timothy Liu
#
# See AUTHORS.txt for a list of people who contributed.
# See LICENSE.txt for license information.
#
##############################################################################
import datetime
import os
from itertools import chain

import numpy as np
import pandas as pd
import yaml

from .glbl import an_glbl

""" helper function """


def _get_current_saf():
    bt_list = [f for f in os.listdir(an_glbl['yaml_dir']) if f.startswith('bt_')]
    if len(bt_list) != 1:
        raise RuntimeError("There are more than one beamtime objects in"
                           "{}. Please either gives specific saf or"
                           .format(an_glbl['yaml_dir']))
    with open(os.path.join(an_glbl['yaml_dir'], bt_list[0]), 'r') as f:
        bt = yaml.load(f)
        saf = bt['bt_safN']
        return saf


def _complete_shape(array):
    if len(np.shape(array)) == 1:
        output_array = np.expand_dims(array, 0)
    else:
        output_array = array
    return output_array


def _update_default_dict(default_dict, **kwargs):
    output_dict = dict(default_dict)
    output_dict.update(kwargs)
    return output_dict


def _timestampstr(timestamp):
    """ convert timestamp to strftime formate """
    timestring = datetime.datetime.fromtimestamp(float(timestamp)).strftime(
        '%Y%m%d-%H%M')
    return timestring


def get_metadata(headers):
    """ small function that returns md as a list of pd.DataFrames """
    if type(list(headers)[1]) == str:
        header_list = list()
        header_list.append(headers)
    else:
        header_list = headers
    md_df_list = []
    for h in header_list:
        md_df_list.append(pd.DataFrame.from_dict(h.start, 'index'))
    return md_df_list


######################################

class XpdAn:
    """ class that holds databroker headers/events and summarize the
    metadata
    """

    _default_dict = {'group': 'XPD'}

    def __init__(self, exp_db=an_glbl['exp_db'], *, saf_num=None, **kwargs):
        self.header_md_fields = ['sa_name', 'time']
        self.event_md_fiedls = None
        self.search_dict = None
        self._current_table = None
        self._current_search = None
        self.exp_db = exp_db
        if saf_num is None:
            # current saf
            saf_num = _get_current_saf()
            self.search_dict = _update_default_dict(self._default_dict,
                                                    bt_safN=saf_num)
            # dict for resetting
            self._reset_dict = _update_default_dict(self._default_dict,
                                                    bt_safN=saf_num)

    def __getitem__(self, ind):
        return self._current_search[ind]

    # @property
    # def search_dict(self):
    #    """ propery that returns current search key-value pair """
    #    return self._search_dict

    # @search_dict.setter
    # def search_dict(self, **kwargs):
    #    self._search_dict.update(kwargs)

    @property
    def current_search(self):
        """ property holds a list of header(s) from most recent search """
        return self._current_search

    def _set_current_search(self, headers, *, index=None):
        if index is None:
            self._current_search = headers
        else:
            self._current_search = self._current_search[index]

    @property
    def current_table(self):
        """ property that holds a pd.DataFrames from most recent search """
        return self._current_table

    def _set_current_table(self, table):
        self._current_table = table

    def reset(self):
        """ method to reset search """
        self.search_dict = self._reset_dict
        self.list()

    def list(self, *, search_dict=None, **kwargs):
        """ method that lists headers """
        if search_dict is None:
            search_dict = self.search_dict
        # allow update
        search_dict.update(kwargs)
        self._set_current_search(self.exp_db(**search_dict))
        self._table_gen(self._current_search,
                        col_name=self.header_md_fields)

    def _table_gen(self, headers, ind_name=None, col_name=None):
        """ self-maintained thin layer of pd.dataFrame, and print it.

        a more mature function is in databroker.core.get_table.
        """
        col_len = len(col_name)

        # prepare md array
        header_md = []
        for h in headers:
            _md_info = []
            for field in self.header_md_fields:
                try:
                    if field == 'time':
                        timestamp = h['start'][field]
                        _md_info.append(_timestampstr(timestamp))
                    else:
                        _md_info.append(h['start'][field])
                except KeyError:
                    _md_info.append('N/A')
            header_md.append(_md_info)
        header_md = list(chain.from_iterable(header_md))
        md_array = np.asarray(header_md)
        md_array.resize((len(header_md) / col_len, col_len))
        # complete_shape
        data = _complete_shape(md_array)
        data_dim = np.shape(data)
        col_dim = np.shape(col_name)
        # check if need transpose
        if data_dim[0] == col_dim[0] and data_dim != col_dim:
            data = np.transpose(data)
        pd_table = pd.DataFrame(data, ind_name, col_name)
        print(pd_table)
        self._set_current_table(pd_table)

# -*- encoding: utf-8 -*-
# -*- coding: utf-8 -*-
"""
    lunaport_worker.tasks.reduce
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Load test artefacts reduce functions.
"""
import pprint
pp = pprint.PrettyPrinter(indent=4).pprint
from functools import partial
from itertools import chain, izip

import pandas as pd
import numpy as np
from scipy.stats import percentileofscore as p_of_score

from .. load_cfg import time_periods_to_msec

STANDART_PERC = [50.0, 75.0, 80.0, 85.0, 90.0, 95.0, 98.0, 99.0, 99.9, 99.99, 100]
PHOUT_COLUMNS = [
    # @see:
    # http://phantom-doc-ru.readthedocs.org/en/latest/analyzing_result_data.html#phout-txt
    'epoach',
    'tags',
    'rtt',
    'connecting',
    'sending',
    'waiting',
    'receiving',
    'exec',
    'req_size',
    'resp_size',
    'errno',
    'http_status'
]

RTT_FRACTS_NAMES = [
    'connecting',
    'sending',
    'waiting',
    'receiving',
]

MICROSECOND_COLUMNS = [
    'rtt',
    'connecting',
    'sending',
    'waiting',
    'receiving',
    'exec'
]


def periods_from_test_struct(test_struct):
    """
    Extract and convert time periods load.cfg param to list of
    time stamps in milliseconds to use them as quantiles borders to
    split phout data frame.

    :param test_struct:
        `dict`, usually obtained from the Lunaport REST API.

    :return: list of ints.
    """
    try:
        perds_raw = test_struct['generator_cfg']['aggregator']['time_periods']
    except KeyError:  # *time_periods* missing, 'schema-less' Phantom test
        return None
        #raise ValueError(
        #    'Failed to extract *time_periods* param value from test')
    return time_periods_to_msec(perds_raw)


def get_tags_delimtr(test_struct):
    """
    Try to get load.cfg param.
    """
    try:
        return test_struct['generator_cfg']['lunaport']['tags_delimtr']
    except KeyError:
        return None


def get_phout_df(phout_loc):
    """
    Creates pandas.DataFrame from phout csv data.
    add column names, cast needed data types.

    :param phout_loc:
        `str`, phout location, URL or local path.

    :return: :class:`pandas.core.frame.DataFrame` obj ready to be processed.
    """
    phout_df = pd.io.parsers.read_csv(phout_loc, sep='\t', names=PHOUT_COLUMNS)
    phout_df['second'] = phout_df['epoach'].astype('int32')

    # cast rtt fractions(rtt, .., exec) dimension from micro to milliseconds
    for column in MICROSECOND_COLUMNS:
        phout_df[column] = np.divide(phout_df[column].astype('float'), 10**3)

    return phout_df

dist_standart_perc = lambda ds: np.percentile(ds, STANDART_PERC)
dist_cfg_periods = lambda ds, t_perds: map(partial(p_of_score, ds), t_perds)
f_round = lambda f: np.around(f, decimals=2)


def ds_distr(ds, columns=None):
    """
    Calc elemnts count, percentage in provided data series.

    .. note:: Some note here.

    :param ds:
        pandas.Series, one dimensional array to reduce.

    :param columns:
        list of str, columns names in result array.

    :return: :class:`numpy.core.records.recarray` - structured array.

    Example::
    """
    cnts = ds.value_counts()
    return pd.DataFrame({
        'count': cnts,
        'percentage': 100.0 * cnts/len(ds.index),
    })


def grouper(iterable):
    """
    Split iterable into overlapping segments.

    :param iterable:
        obj supporting iteration protocol.

    :return: list of tuple with elemnt pairs.

   Example::

        >>> [e for e in grouper((1, 3, 5))]
        [(0, 1), (1, 3), (3, 5)]
    """
    return izip(chain([0], iterable), iterable)


def chunk_percent(ds, chunk):
    """
    Calc count and percentage of elements in slice from whole data set.

    :param ds:
        :class:`pandas.core.series.Series`, one dimensional array of digits.

    :param chunk:
        tuple of two ints, slice first and last elemnt idx.

    :return: tuple of int and float aka (chunk length, chunk percentage)
    """
    chunk_size = np.sum((ds >= chunk[0]) & (ds <= chunk[1]))
    return chunk_size, 100 * chunk_size / float(ds.size)


def float_pp(num):
    """
    Limiting floats to two decimal points.
    """
    return '{0:.2f}'.format(num)


def compose_charts(df):
    """
    Create charts data from phout_ds or it's slice.

    :param df:
        :class:`pandas.core.frame.DataFrame`, phout or its part(slice).

    :return: `dict`, seconds as keys.
    """
    p99 = lambda (name, ds): (name, np.percentile(ds, 99))
    chart = {}
    grouped = df.groupby('second')

    for name, group in grouped:
        chart[name] = {
            'rps': len(group),
            'resp': dist_standart_perc(group['rtt']),
            'rtt_fracts': map(p99, [(n, group[n]) for n in RTT_FRACTS_NAMES]),
            # TODO: Chnage chart JSON struct.
            #'errno': itemfreq(group['errno']).tolist(),
            #'http_status': itemfreq(group['http_status']).tolist(),
        }
    return chart


def compose_stats(df, t_periods):
    """
    Create stats data  - tables with reduced phout statistic for particular df

    :param df1:
        :class:`pandas.core.frame.DataFrame`, phout or its part(slice).

    :param t_periods:
        list of ints, user defined quantiles to split phout data,
        getting from load_cfg.aggregator.time_periods. May be emplty.

    :return: `dict`, stat tables names as keys.
    """
    # Response times distr - standart
    resp_stand_q = {'percentiles':  STANDART_PERC}
    resp_stand_q['quantiles'] = dist_standart_perc(df['rtt'])
    resp_stand_q['num'], resp_stand_q['percentages'] = zip(
        *map(partial(chunk_percent, df['rtt']),
             grouper(resp_stand_q['quantiles'])))

    if t_periods:  # Response times distr - usr defined t_periods
        resp_cfg_q = {'quantiles': t_periods}
        resp_cfg_q['percentiles'] = dist_cfg_periods(df['rtt'], t_periods)
        resp_cfg_q['num'], resp_cfg_q['percentages'] = zip(
            *map(partial(chunk_percent, df['rtt']), grouper(t_periods)))

    # Phantom socket calls errno distr
    errno_distr = ds_distr(df['errno'])

    # HTTP replies status codes distr
    http_status_distr = ds_distr(df['http_status'])

    # RTT fractions percentages
    time_total = np.sum(df['rtt'])
    rtt_fracts = {}

    for fr in RTT_FRACTS_NAMES:
        rtt_fracts[fr] = (100 * np.sum(df[fr])) / time_total

    # Phantom added time overhead percentage of total time(RTT)
    phantom_exec_frac = 100 * (time_total - np.sum(df['exec'])) / time_total

    rv = {
        #'resp_cfg_q': resp_cfg_q,  # resp stats for load.cfg defined quantiles
        'resp_stand_q': resp_stand_q,  # resp stats for standart percentiles
        'errno_distr': errno_distr,
        'http_status_distr': http_status_distr,
        'rtt_fracts': rtt_fracts,
        'phantom_exec_frac': phantom_exec_frac,
    }
    if t_periods:
        rv.update({'resp_cfg_q': resp_cfg_q, })
    return rv


def reduce_phout_df(phout_df, t_periods, tags_delimtr=None):
    """
    Split whole test phantom_df by tags,
    compose stats and charts for each tag.
    Args:
        phout_df - pandas.core.frame.DataFrame, whole test phantom data frame.
        t_periods - list of ints, RTT quantiles.
        tags_delimtr - str, char to use to split each tag str.
            Not None means tag is plural.

    Returns:
        dict - tag names as keys,
            dict with 'stat' - statistics, 'chart' - charts as values.
    """
    res = {
            'all': {'stat': None, 'chart': None}
    }

    res['all']['stat'] = compose_stats(phout_df, t_periods)
    res['all']['chart'] = compose_charts(phout_df)

    if tags_delimtr:
        df_with_tags = phout_df.dropna(axis=0, subset=['tags'])  # filter out raws without tags
        df_with_tags.tags = df_with_tags.tags.apply(lambda el: el.split(','))  # str ->array of str
        tags = list(set(
            [item for sublist in df_with_tags.tags.values for item in sublist]))  # uniq tags list

        for t in tags:
            df_with_tags.cont_tag = df_with_tags.tags.apply(lambda el: t in el)
            filtrd = df_with_tags[df_with_tags.cont_tag == True]
            res.setdefault(t, {})
            res[t]['stat'] = compose_stats(filtrd, t_periods)
            res[t]['chart'] = compose_charts(filtrd)
    else:
        for tag_name, tag_group in phout_df.groupby('tags'):
            res.setdefault(tag_name, {})
            res[tag_name]['stat'] = compose_stats(tag_group, t_periods)
            res[tag_name]['chart'] = compose_charts(tag_group)
    return res


def cast_np_to_py(num):
    """
    Cast numpy types to python types suitable for JSON serialization.

    :param num:
        :`numpy.int64` or `numpy.float64`.

    :return: int or float.
    """
    if isinstance(num, np.int64):
        return int(num)
    elif isinstance(num, np.float64):
        return float(num)
    else:
        raise ValueError('Type for cast not supported:{}'.format(type(num)))


def dist_adapt(df):
    """
    Compose Lunaport distr suitable value distr format(list of dicts)
    from pandas data frame.

    :param df:
        :class:`pandas.core.frame.DataFrame`, value dist stats.

    :return: list of `dict`, code / count / percentage as keys.
    """
    return [dict(zip(['code', 'count', 'percentage'],
                     map(cast_np_to_py, row))) for row in df.itertuples()]


def stat_adapt_types(stat):
    """
    Adapt stat table data types to serialization.
    Numpy types not suitable for JSON serialization but new panas version
    will support such ops.
    """
    if 'http_status_distr' in stat:
        stat['http_status_distr'] = dist_adapt(stat['http_status_distr'])
    if 'errno_distr' in stat:
        stat['errno_distr'] = dist_adapt(stat['errno_distr'])
    if 'resp_stand_q' in stat:
        stat['resp_stand_q']['num'] = map(int, stat['resp_stand_q']['num'])
    if 'resp_cfg_q' in stat:
        stat['resp_cfg_q']['num'] = map(int, stat['resp_cfg_q']['num'])
    return stat

df_size = lambda df: (df.values.nbytes, df.values.nbytes / 1048576)

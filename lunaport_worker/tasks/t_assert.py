# -*- encoding: utf-8 -*-

"""
    lunaport_worker.tasks.assert
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Load test results validation functions.
"""

import sys
import copy
from inspect import getmembers, isfunction, getdoc, getargspec
import traceback
import pprint
pp = pprint.PrettyPrinter(indent=4).pprint

from t_reduce import RTT_FRACTS_NAMES


def exec_assert(test_id, phout_df, res, oracle, asserts, logger=None):
    """
    Execute one assert function taking args from oracle struct, compose
    returning data dict.
    """
    ora = copy.deepcopy(oracle)
    result = copy.deepcopy(oracle)
    ora['kw'].update({
        'phout_df': phout_df,
        'res': res,
    })
    try:
        passed, msg = asserts[ora['name']]['fnc_obj'](*ora['arg'],
                                                      **ora['kw'])
        result.update({
            'passed': passed,
            'msg': msg,
        })
    except Exception as e:
        if logger:
            logger.error('Test:{} | Assert func execution failed:{} | {}'.format(
                test_id, str(e), traceback.format_exc()))
        result.update({
            'passed': False,
            'msg': 'Exception: {}'.format(str(e)),
        })
    return result


def get_asserts(module_obj=None):
    """
    Getting python module factions which names starts from 'assert_',
    Returning dict with such fuctions names as keys and fucn obj as values.
    """
    module_obj = module_obj or sys.modules[__name__]
    asserts = {}
    for struct in getmembers(module_obj):
        if isfunction(struct[1]) and struct[0].startswith('assert_'):
            asserts[struct[0]] = {
                'fnc_obj': struct[1],
                'docstr': getdoc(struct[1]),
                'args': getargspec(struct[1]).args,
            }
    return asserts


def compare(sign, num0, num1):
    """
    Compare two obj getting condition from str variable.
    Need for work with JSON based comparison rules.

    Args:
        sign: str, python comparison signs.
        num0 and num1: obj to compare, in most cases will be the numbers.

    Returns:
        Boolean
    """
    allowed = ['>', '>=', '<', '<=']
    assert(sign in allowed)
    return bool(eval('num0 {} num1'.format(sign)))


def assert_resp_times_distr(perc, sign, ms, **kw):
    """
    Checks the condition of load test responce times distribution.
    Args:
        perc: float, percentile of resp series to analize.
        sign: str, python comparison signs.
        ms: float, upper quantile limit for comparison in milliseconds.
        tag: str, result slice name based in Phantom ammo tag, default:all.
        res: dict, reduced test statistic.

    Returns:
        tuple of bool and dict.
        Boolean, verdict, True mean passed.
        dict, execution metadata.
    """
    perc = float(perc)
    ms = float(ms)
    sign = str(sign)
    tag = kw.get('tag', 'all')  # Work with all test results scope by default.

    stat = kw['res'][tag]['stat']

    for k in ['resp_stand_q', 'resp_cfg_q']:
        try:
            perc_idx = stat[k]['percentiles'].index(perc)
            quant_for_percl = stat[k]['quantiles'][perc_idx]
            msg = '{}%ile have score:{} ms'.format(perc, quant_for_percl)
            return compare(sign, quant_for_percl, ms), {'msg': msg}
        except ValueError:
            raise ValueError('No such percentile:{}'.format(perc))


def assert_errno_distr(code, sign, pct, **kw):
    """
    Checks the condition of load test generator(Phantom)
    socket calls errno distribution.

    Args:
        code: int, errno code to analize. @see linux kernel src errno-base.h
        sign: str, python comparison signs.
        pct: float, percent for comparison.
        tag: str, result slice name based in Phantom ammo tag, default:all.
        res: dict, reduced test statistic.

    Returns:
        tuple of bool and dict.
        Boolean, verdict, True mean passed.
        dict, execution metadata.
    """
    code = int(code)
    pct = float(pct)
    sign = str(sign)
    tag = kw.get('tag', 'all')  # Work with all test results scope by default.

    errno_distr = kw['res'][tag]['stat']['errno_distr']
    try:
        code_pct = [d for d in errno_distr if d['code'] == code].pop()['percentage']
    except IndexError:
        msg = 'No such code:{} in errno_distr'.format(code)
        if sign in ['<', '<=']:  # nothing less than any count.
            return True, {'msg': msg}
        else:
            raise ValueError(msg)

    msg = 'code:{} is {}% of total'.format(code, code_pct)
    return compare(sign, code_pct, pct), {'msg': msg}


def assert_http_status_distr(code, sign, pct, **kw):
    """
    Checks the condition of HTTP responces status codes distribution.

    Args:
        code: int, HTTP status code to analize.
              @see http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html
        sign: str, python comparison signs.
        pct: float, percent for comparison.
        tag: str, result slice name based in Phantom ammo tag, default:all.
        res: dict, reduced test statistic.

    Returns:
        tuple of bool and dict.
        Boolean, verdict, True mean passed.
        dict, execution metadata.
    """
    code = int(code)
    pct = float(pct)
    sign = str(sign)
    tag = kw.get('tag', 'all')  # Work with all test results scope by default.

    status_distr = kw['res'][tag]['stat']['http_status_distr']
    try:
        code_pct = [d for d in status_distr if d['code'] == code].pop()['percentage']
    except IndexError:
        msg = 'No such code:{} in http_status_distr'.format(code)
        if sign in ['<', '<=']:
            return True, {'msg': msg}
        else:
            raise ValueError(msg)

    msg = 'code:{} is {}% of total'.format(code, code_pct)
    return compare(sign, code_pct, pct), {'msg': msg}


def assert_phantom_exec_fract(sign, pct, **kw):
    """
    Checks the condition of Phantom time overhead percentage
    from whole RTT. Usually overhead consists from reading ammo data
    from file system and memory allocation.

    Args:
        sign: str, python comparison signs.
        pct: float, percent for comparison.
        tag: str, result slice name based in Phantom ammo tag, default:all.
        res: dict, reduced test statistic.

    Returns:
        tuple of bool and dict.
        Boolean, verdict, True mean passed.
        dict, execution metadata.
    """
    pct = float(pct)
    sign = str(sign)
    tag = kw.get('tag', 'all')  # Work with all test results scope by default.

    ph_fract = kw['res'][tag]['stat']['phantom_exec_frac']

    msg = 'ph_fract:{}% from RTT'.format(ph_fract)
    return compare(sign, ph_fract, pct), {'msg': msg}


def assert_rtt_fract(fract_name, sign, pct, **kw):
    """
    Checks the condition of RTT fractions proportion.
    Helps to catch unexpected network degradation.

    Args:
        fract_name: str
        @see http://phantom-doc-ru.readthedocs.org/en/latest/analyzing_result_data.html#phout-txt
        sign: str, python comparison signs.
        pct: float, percent for comparison.
        tag: str, result slice name based in Phantom ammo tag, default:all.
        res: dict, reduced test statistic.

    Returns:
        tuple of bool and dict.
        Boolean, verdict, True mean passed.
        dict, execution metadata.
    """
    assert (fract_name in RTT_FRACTS_NAMES)
    pct = float(pct)
    sign = str(sign)
    tag = kw.get('tag', 'all')  # Work with all test results scope by default.

    resp_fract_pct = kw['res'][tag]['stat']['rtt_fracts'][fract_name]

    msg = 'resp_fract:{} is {}% of total RTT'.format(
        fract_name, resp_fract_pct)
    return compare(sign, resp_fract_pct, pct), {'msg': msg}

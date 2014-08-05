#!/usr/bin/env python
# -*- encoding: utf-8 -*-

"""
    load_cfg
    ~~~~~~~~

    Contains dict with schemat to use with validictory module.
"""
import ConfigParser

import validictory

SCHEMA = {
    'type': 'object',
    'properties': {
        'meta': {
            'type': 'object',
            'properties': {
                'task': {'type': 'string'},
                'job_name': {'type': 'string'},
                'job_dsc': {'type': 'string', 'required': False},
                'ver': {'type': 'string', 'required': False},
                'operator': {'type': 'string', 'required': False},
                'notify': {'type': 'string', 'required': False},
            }
        },
        'tank': {
            'type': 'object',
            'required': False,
            'properties': {
                'artifacts_base_dir': {'type': 'string', 'required': False},
            }
        },
        'phantom': {
            'type': 'object',
            'properties': {
                'rps_schedule': {'type': 'string'},
                'ammofile': {'type': 'string'},
                'address': {'type': 'string'},
                'port': {'type': 'string'},
                'ssl': {'type': 'string', 'required': False},
                'header_http': {'type': 'string', 'required': False},
                'headers': {'type': 'string', 'required': False},
                'writelog': {'type': 'string', 'required': False},
                'header_http': {'type': 'string', 'required': False},
            }
        },
        'autostop': {
            'type': 'object',
            'required': False,
            'properties': {
                'autostop': {'type': 'string', 'required': False},
            }
        },
        'monitoring': {
            'type': 'object',
            'required': False,
            'properties': {
                'config': {'type': 'string', 'required': False},
            }
        },
        'aggregator': {
            'type': 'object',
            'properties': {
                'time_periods': {'type': 'string'},
                'monitoring_config': {'type': 'string', 'required': False},
            }
        },
        'shellexec': {
            'type': 'object',
            'required': False,
            'properties': {
                'end': {'type': 'string', 'required': False},
                'postprocess': {'type': 'string', 'required': False},
            }
        },
    },
}


class Parser(ConfigParser.ConfigParser):
    """ Add dict representation to default ConfigParser.
    """
    def as_dict(self):
        d = dict(self._sections)
        for k in d:
            d[k] = dict(self._defaults, **d[k])
            d[k].pop('__name__', None)
        return d


def validate(cfg, schema=SCHEMA):
    """ Check cfg dict structure: required keys and their types.
    Args:
        cfg: dict, data to validate.
        schema: dict, validation rules.

    Returns:
        Raise exception on invalid sample.
    """
    validictory.validate(cfg, schema)
    return True

def el_to_msec(el):
    if el.endswith('s'):
        return int(el.rstrip('s')) * 1000
    elif el.endswith('m'):
        return int(el.rstrip('m')) * 1000 * 60
    return int(el)

def time_periods_to_msec(periods):
    """ Convert load.cfg time_periods parameter value dimension to seconds.
    Args:
        periods: str, Yandex tank load.cfg param.

    Returns:
        list of int, in seconds.
    """
    return sorted(map(el_to_msec, periods.split(' ')))

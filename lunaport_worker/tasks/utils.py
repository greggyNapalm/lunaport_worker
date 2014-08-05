# -*- encoding: utf-8 -*-

"""
    lunaport_worker.tasks.utils
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    A set of functions and tools to help in routine.
"""
import os
import pprint
pp = pprint.PrettyPrinter(indent=4).pprint

import pytz
import dateutil.parser
import redis
from celery import Celery
from celery.signals import task_prerun, task_failure
from raven import Client
from raven.contrib.celery import register_signal

from lunaport_client.http_client import LunaportClinetV1
from .. helpers import compose_logger, get_worker_cfg
from .. import celeryconfig

celery = Celery()
celery.config_from_object(celeryconfig)


CFG_PATH = os.environ.get('LUNAPORT_WORKER_CFG_PATH') or '/etc/lunaport/worker.yaml'
worker_cfg = get_worker_cfg(CFG_PATH)

# sentry client
if os.environ.get('LUNAPORT_ENV') == 'production':
    sentry_client = Client(worker_cfg['sentry_dsn'])
    register_signal(sentry_client)


# graylog2 adaptor and extra log params
def get_logger(**kw):
    kw.update({
        'env': os.environ.get('LUNAPORT_ENV', 'lunaport-dev')
    })
    return compose_logger(worker_cfg['logging'], extra=kw)


# Redis
redis = redis.Redis(**worker_cfg['redis'])
r_adr = {
    'monitor_finish': '3rd_monitor_finish',
    'monitor_start': '3rd_monitor_start',
}

# Clients
#lunaport_c = LunaportClinet(**worker_cfg['lunaport'])
lunaport_c1 = LunaportClinetV1(**worker_cfg['lunaport1'])


class TestStateTr(object):
    tbl = {
        'in_progress': 'RUNNING',
        #'pending': None,
        'pending': 'PREPARING',
    }

    @classmethod
    def port_by_tank(cls, tank_state):
        for p, t in cls.tbl.items():
            if t == tank_state:
                return p
        return None

    @classmethod
    def tank_by_port(cls, port_state):
        return cls.tbl.get(port_state)


def msk_iso_to_utc(date_iso_str):
    """
    Convert 'Europe/Moscow' local time stamp to UTC stamp.
    """
    local = pytz.timezone('Europe/Moscow')
    local_dt = local.localize(dateutil.parser.parse(date_iso_str), is_dst=None)
    return local_dt.astimezone(pytz.utc)


#@task_prerun.connect
#def task_prerun_handler(**kw):
#    pp(kw)
#    logger = get_logger()
#    logger.info('IN task_prerun')

#@task_failure.connect
#def sentry_logger_on_failure(**kw):
#    #def process_failure_signal(sender, task_id, args, kwargs, **kw):
#    # This signal is fired inside the stack so let raven do its magic
#    sentry_client = Client(worker_cfg['sentry_dsn'])
#    sentry_client.captureException(
#        extra={
#            'task_id': kw['task_id'],
#            'task': kw['sender'],
#            'args': kw['args'],
#            'kwargs': kw['kwargs'],
#        })

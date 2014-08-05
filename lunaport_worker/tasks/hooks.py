#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    lunaport_worker.tasks.hooks
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Functions to readct on some service events.
"""

import socket
import string
import json
import datetime as dt
import pprint
pp = pprint.PrettyPrinter(indent=4).pprint

from .. import __version__
from utils import (
    celery,
    get_logger,
    lunaport_c1,
    worker_cfg
)
from .. clients import ConductorClient, GolemClient, BaseClinetError
from lunaport_client.exceptions import LunaportClientError

@celery.task
def on_user_add(login, src_case_id=66):
    """
    Create default case for new user.
    Args:
        login - str.
    """
    t_start = dt.datetime.now()
    log_ext = {
        'task_name': 'on_user_add',
        'wroker_ver': __version__
    }
    logger = get_logger(**log_ext)
    src_case = lunaport_c1.case_get(src_case_id)
    dst_case = {
        'name': '{}_sandbox'.format(login),
        'descr': src_case['descr'],
        'oracle': src_case['oracle'],
    }
    lunaport_c1.case_post(dst_case)
 

def main():
    on_user_add('gkomissarov1')

if __name__ == '__main__':
    main()

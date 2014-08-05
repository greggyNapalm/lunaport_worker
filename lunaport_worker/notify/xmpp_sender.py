#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    lunaport_worker.notify.xmpp
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    XMPP wrapper here.
"""

import xmpp

from .. helpers import LinkComposer as lnk
from msg_templates import (
    test_xmpp_on_finish,
    test_xmpp_on_start,
    test_xmpp_on_start_failed,
)


def get_connection(jid=None, passwd=None, debug=False):
    assert all([jid, passwd])

    jid = xmpp.JID(jid)
    conn = xmpp.Client(jid.getDomain(), debug=debug)
    conn.connect()
    conn.auth(jid.getNode(), passwd)
    return conn


def send(event, test, case, t_resolution, login, xmpp_cfg, tank_msg=None):
    keys_to_fillter = [
        'load_src',
        'load_dst',
        'initiator',
        'issue',
        'name',
        'id'
    ]
    to_render = {k: test.get(k) for k in keys_to_fillter}
    to_render.update({
        'case_name': case.get('name'),
        't_resolution': t_resolution,
        'lnk_test_detail': lnk.lnk_test_detail(test.get('id')),
        'lnk_case_detail': lnk.lnk_case_detail(case.get('id')),
        'lnk_case_edit': lnk.lnk_case_edit(case.get('id')),
    })

    if event == 'on_finish':
        msg = test_xmpp_on_finish.format(**to_render)
    elif event == 'on_start':
        msg = test_xmpp_on_start.format(**to_render)
    elif event == 'on_start_failed':
        to_render['tank_msg'] = tank_msg
        msg = test_xmpp_on_start_failed.format(**to_render)
    else:
        msg = 'Error in notification system. Call support'

    dst_jid = '{login}@domain.org'.format(login=login)
    conn = get_connection(**xmpp_cfg)
    conn.send(xmpp.protocol.Message(dst_jid, msg))

#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    lunaport_worker.notify.email
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    SMTP wrapper here.
"""

import smtplib

from msg_templates import (
    test_email_body_on_finish,
    test_email_body_on_start,
    test_email_body_on_start_failed,
    test_email_subj_on_finish,
    test_email_subj_on_start,
    test_email_subj_on_start_failed,
)
from .. helpers import LinkComposer as lnk

MST_TMPL = '\r\n'.join([
    'From: {from}',
    'To: {to}',
    #'Cc: {cc}',
    #'Bcc: {bcc}',
    'Subject: {subj}',
    'Content-Type: text/html; charset=UTF-8',
    'Content-Transfer-Encoding: quoted-printable',
    '\r\n{body}',
])

DEFAULT_FROM_HDR = 'firebat@domain.ru'
DEFAULT_FROM = 'devnull@domain.ru'

COLORS = {
    True: '#E6FFE6',  # Green - test passed
    False: '#FFE6E6',  # Red - test failed
}


def get_connection(dst_host='127.0.0.1', dst_port=25, auth=None):
    s = smtplib.SMTP(dst_host, dst_port)
    if auth:
        s.login(**auth)
    return s


def send(event, test, case, t_resolution, login, smtp_cfg, tank_msg=None):
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
        'bg_color': COLORS.get(t_resolution),
    })

    meta = {
        'from': smtp_cfg.get('from_addr') or DEFAULT_FROM_HDR,
        'to': '{login}@domain.ru'.format(login=login),
        'subj': None,
        'body': None
    }
    if event == 'on_finish':
        meta['subj'] = test_email_subj_on_finish.format(**to_render)
        meta['body'] = test_email_body_on_finish.format(**to_render)
    elif event == 'on_start':
        meta['subj'] = test_email_subj_on_start.format(**to_render)
        meta['body'] = test_email_body_on_start.format(**to_render)
    elif event == 'on_start_failed':
        to_render['tank_msg'] = tank_msg
        meta['subj'] = test_email_subj_on_start_failed.format(**to_render)
        meta['body'] = test_email_body_on_start_failed.format(**to_render)
    else:
        meta['subj'] = 'Call support'
        meta['body'] = 'Error in notification system'

    msg = MST_TMPL.format(**meta)
    conn = get_connection(**smtp_cfg)
    conn.sendmail(DEFAULT_FROM, meta['to'], msg)

#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    lunaport_worker.notify.email
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    SMTP wrapper here.
"""
import pprint
pp = pprint.PrettyPrinter(indent=4).pprint

from .. clients import JIRARESTClinet, BaseClinetError
from msg_templates import test_tracker_on_finish, test_tracker_on_start
from .. helpers import LinkComposer as lnk

COLORS = {
    True: '#E6FFE6',  # Green - test passed
    False: '#FFE6E6',  # Red - test failed
}

def send(event, test, case, t_resolution, issue, trackers_cfg):
    if issue.get('provider') == 'jira':
        c = JIRARESTClinet(**trackers_cfg.get('jira'))
    else:
        raise ValueError(
            'Unknown issue provider: {}'.format(issue.get('provider')))

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
        'res_pp': '!!(green)True!!' if t_resolution else '!!(red)False!!',
        'lnk_test_detail': lnk.lnk_test_detail(test.get('id')),
        'lnk_case_detail': lnk.lnk_case_detail(case.get('id')),
        'lnk_case_edit': lnk.lnk_case_edit(case.get('id')),
        'bg_color': COLORS.get(t_resolution),
    })

    if event == 'on_finish':
        msg = test_tracker_on_finish.format(**to_render)
    elif event == 'on_start':
        msg = test_tracker_on_start.format(**to_render)
    else:
        msg = 'Error in notification system. Call support'

    c.post_comment(issue.get('name'), msg)

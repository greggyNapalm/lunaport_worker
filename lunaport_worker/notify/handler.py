#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    lunaport_worker.notify.handler
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test resource event handlers(notification related).
"""
import pprint
pp = pprint.PrettyPrinter(indent=4).pprint

from lunaport_client.exceptions import LunaportClientError

from .. tasks.utils import lunaport_c1, worker_cfg
from .. tasks.utils import get_logger
from smtp_sender import send as send_email
from xmpp_sender import send as send_xmpp
from issue_tracker_sender import send as send_to_tracker


def test(event, test, t_resolution, case, tracker_cfg=None, tank_msg=None):
    """ 
    Handle test resource related events like: start, finish.
    Fetch notification configs and send msgs them if necessary.
    """
    ext = {'test_id': test.get('id')}
    logger = get_logger(**ext)

    tracker_cfg = tracker_cfg or case.get('notification')
    if not tracker_cfg:
        msg = ''.join([
            'Can\'t fetch issue_tracker notifycation',
            'settings for case: {}'.format(case.get('name'))
        ])
        logger.warning(msg)
        return

    if tracker_cfg.get(event) or ((t_resolution is False) and tracker_cfg.get('on_failed')):
        try:
            issue = lunaport_c1.issue_get(test.get('issue'))
        except LunaportClientError as e:
            logger.error(str(e))

        try:
            send_to_tracker(event, test, case, t_resolution, issue,
                            worker_cfg.get('issue_providers'))
        except Exception as e:
            logger.warning(str(e))

    try:
        usrs_cfgs = lunaport_c1.notifctn_get(case.get('name'))
    except LunaportClientError as e:
        logger.warning(str(e))
        return

    def hndl_usr(usr_cfg):
        """ Handle particular user notification settings
            and apply to the event.
        """
        xmpp_cfg = usr_cfg.get('cfg', {}).get('xmpp')
        if xmpp_cfg and (xmpp_cfg.get(event) or (
                        (t_resolution is False) and xmpp_cfg.get('on_failed'))):
            try:
                send_xmpp(event, test, case, t_resolution,
                          usr_cfg['user']['login'], worker_cfg.get('xmpp'))
            except Exception as e:
                logger.error(str(e))

        email_cfg = usr_cfg.get('cfg').get('email')
        if email_cfg and (email_cfg.get(event) or (
                (t_resolution is False) and email_cfg.get('on_failed'))):
            try:
                send_email(event, test, case, t_resolution,
                           usr_cfg['user']['login'], worker_cfg.get('email'))
            except Exception as e:
                logger.error(str(e))

    map(hndl_usr, usrs_cfgs)

    if event != 'on_start_failed':
        return
    # Test was scheduled but execution failed on Tank side.
    # XXX: Only *initiator* user will be notified with XMPP and email.
    try:
        send_xmpp(event, test, case, None, test['initiator'],
                  worker_cfg.get('xmpp'), tank_msg=tank_msg.get('tank_msg'))
        send_email(event, test, case, None, test['initiator'],
                   worker_cfg.get('email'), tank_msg=tank_msg.get('tank_msg'))
    except Exception as e:
        logger.error(str(e))

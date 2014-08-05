# -*- encoding: utf-8 -*-

"""
    lunaport_worker.tasks.check
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Smoke test for whole system.
"""

import os
import datetime as dt
import pprint
pp = pprint.PrettyPrinter(indent=4).pprint

import msgpack
from lunapark_client.tank import TankClinet
from lunaport_client.exceptions import LunaportClientError

from .. import __version__
from utils import (
    msk_iso_to_utc,
    TestStateTr,
    celery,
    get_logger,
    redis,
    r_adr,
    #lunaport_c,
    lunaport_c1,
)
from t_reduce import (
    periods_from_test_struct,
    get_tags_delimtr,
    get_phout_df,
    reduce_phout_df,
    stat_adapt_types,
    df_size,
)
import t_assert
from ..notify.handler import test as notify_test


@celery.task
def add(x, y):
    logger = get_logger()
    logger.info('Hello world')
    return x + y


@celery.task
def monitor_lunapark_running():
    """ Read running load tests from Redis,
        launch running test processing task.
    """
    running_tests = redis.hgetall(r_adr['monitor_finish'])
    for t, v in running_tests.iteritems():
        v = msgpack.unpackb(v)
        proc_luna_running.delay(redis_value=v, **v)


@celery.task
def monitor_tank_scheduled():
    """ Read scheduled to Ynadex tank via Tank API load tests from Redis.
        React on test change. In negative case test may not be created on
        3rd party side because metadata inconsistency.
    """
    scheduled_tests = redis.hgetall(r_adr['monitor_start'])
    for t, v in scheduled_tests.iteritems():
        v = msgpack.unpackb(v)
        proc_tank_scheduled.delay(v, **v)


@celery.task
def proc_tank_scheduled(redis_msg, **kw):
    ext = {'test_id': redis_msg.get('id')}
    logger = get_logger(**ext)
    try:
    except TankClientError as e:
        logger.error('Tank API call failed: {}'.format(e))
        raise

    if tank_msg['status_code'] == 'PREPARING':
        return

    try:
        lunaport_msg = lunaport_c1.test_get(redis_msg['id'])
        case_struct = lunaport_c1.case_get(lunaport_msg.get('case_id'))
    except LunaportClientError as e:
        logger.error('Lunaport client call failed:{}'.format(e))
        raise

    if tank_msg['status_code'] == 'FINISHED' and tank_msg['exit_code'] == 1:
        # Test was scheduled but excution failed
        redis.hdel(r_adr['monitor_start'], kw['id'])
        notify_test('on_start_failed', lunaport_msg, None, case=case_struct,
                    tank_msg=tank_msg)
        return

    diff = {
        'status': TestStateTr.port_by_tank(tank_msg.get('status_code')),
    }
    t_summary = {}
    if tank_msg.get('lunapark_id'):
        try:
                l_test_id=tank_msg['lunapark_id']).json().pop()
            t_summary.update({'t_tank_id': redis_msg['t_tank_id']})
            diff.update({
                'lunapark': t_summary,
            })
            if t_summary.get('fd'):
                diff.update({
                    'started_at': msk_iso_to_utc(t_summary['fd']).isoformat(),
                })

    try:
        test_struct, test_loc = lunaport_c1.test_patch(redis_msg['id'], diff)
    except LunaportClientError as e:
        test_struct = None
        logger.error('Lunaport client call failed:{}'.format(e))
        if not 'Nothing to update' in str(e):
            raise
    redis.hdel(r_adr['monitor_start'], kw['id'])
    t_struct = test_struct or t_summary
    notify_test('on_start', t_struct, None, case=case_struct),


@celery.task
def proc_luna_running(**kw):
    """ Fetch test statuses from Redis, if test finisged notify service via API
        and call reduce job.
    """
    ext = {'test_id': kw.get('redis_value', {}).get('id')}
    logger = get_logger(**ext)

    if not ('t_fqdn' in kw and 't_tank_id' in kw):
        logger.erro('proc_luna_running call. Malformed params:{}'.format(kw))

    try:
    except TankClientError as e:
        logger.error('Tank API call failed: {}'.format(e))
        raise

    if tank_msg['status_code'] != 'FINISHED':
        if kw.get('status') and TestStateTr.tank_by_port(kw.get('status')) != tank_msg['status_code']:
            # test state changes since last check, need to notify
            port_state = TestStateTr.port_by_tank(tank_msg['status_code'])
            redis_value = kw['redis_value']
            redis_value.update({'status': port_state})
            redis.hset(r_adr['monitor_finish'], kw['id'],
                       msgpack.packb(redis_value))
            diff = {
                'status': port_state,
            }
            try:
                lunaport_c1.test_patch(kw['id'], diff)
            except LunaportClientError as e:
                logger.error('Lunaport client call failed:{}'.format(e))
                if not 'Nothing to update' in str(e):
                    raise

            logger.info('test:{} status:{}'.format(kw['id'], port_state))
        return

    if tank_msg['exit_code'] == 1:  # Test was scheduled but excution failed
        logger.error(''.join([
            'Test was scheduled,',
            ' but excution failed with error: {}']).format(
            tank_msg.get('tank_msg')))

        diff = {'status': 'failed'}

    else:
        # Test execution finished without errors, result suitable for reduce.
        try:
                l_test_id=tank_msg['lunapark_id']).json()
            raise ValueError(
                '3rd party API call failed:{}; lunapark_id:{}'.format(
                    e, tank_msg['lunapark_id']))

        diff = {
            'status': 'reducing',
            'finished_at': msk_iso_to_utc(t_summary[0]['td']).isoformat()
        }
    try:
        lunaport_c1.test_patch(kw['id'], diff)
    except LunaportClientError as e:
        logger.error('Lunaport client call failed:{}'.format(e))
        raise

    # DEBUG
    redis.hdel(r_adr['monitor_finish'], kw['id'])
    if diff['status'] != 'failed':
        reduce_test(kw.get('id'), kw.get('t_fqdn'), kw.get('t_tank_id'))


@celery.task
def reduce_test(test_id, t_fqdn, t_tank_id, eval_only=False):
    """ Fetch test statuses from Redis, if test finished notify service via API
        and call reduce job.
    """
    ext = {'test_id': test_id}
    logger = get_logger(**ext)

    try:
                                    t_test_id=t_tank_id).get('phout.log')
        reduce_phout(test_id, phout_url, eval_only=eval_only)
    except TankClientError as e:
        logger.error('3rd party API call failed: {}'.format(e))
    except IOError as e:
        logger.error(
                'IO error in phout processing: {}; phout_url:{}'.format(
                e, phout_url))

        logger.error('fqdn: {}; t_test_id: {}; arts: {}'.format(


@celery.task
def reduce_arts(test_id, files):
    """ Reduce test results without any external API calls,
        used to process result manually uploaded by user
        without any Lunapark or Jenkins connection.
    """
    ext = {'test_id': test_id}
    logger = get_logger(**ext)

    reduce_phout(test_id, files['phout'])

    started_at, finished_at = phout_time_info(files['phout'])
    diff = {
        'started_at': started_at.isoformat(),
        'finished_at': finished_at.isoformat(),
    }
    try:
        lunaport_c1.test_patch(kw['id'], diff)
    except LunaportClientError as e:
        logger.error('Lunaport client call failed:{}'.format(e))
        raise

    map(os.unlink, files.values())


def phout_time_info(path):
    """ Generate tuple with utc timestamps of first and last requests.
    """
    with open(path, 'rb') as fh:
        first = next(fh).decode()
        fh.seek(-1024, 2)
        last = fh.readlines()[-1].decode()

    parse = lambda s: dt.datetime.utcfromtimestamp(float(s.split('\t')[0]))
    return map(parse, [first, last])


def retrieve_test_status(t_fqdn, t_tank_id):
    """ Retrieve test status through Tank API.
    """
    try:
        return rv['status_code'], rv['lunapark_id']
    except TankClientError:
        return None, None


def reduce_phout(test_id, phout_loc, eval_only=False):
    """
    Calc test result metric like:
        * HTTP responses times distribution
        * HTTP responses status code distribution
        * Phantom socket calls errno distribution


    :param test_id:
        `int`, uniq lunaport test identificator.

    :param phout_loc:
        `str`, phout location, URL or local path.

    :param eval_only:
        `bool`, Only evaluate result, no stat and chart update needed.
    """
    ext = {'test_id': test_id}
    logger = get_logger(**ext)

    t_start = dt.datetime.now()
    diff = {
        'status': 'reducing'
    }
    try:
        test_struct, test_loc = lunaport_c1.test_patch(test_id, diff)
    except LunaportClientError as e:
        logger.error('Lunaport client call failed:{}'.format(e))
        raise

    # reduce
    t_periods = periods_from_test_struct(test_struct)
    tags_delimtr = get_tags_delimtr(test_struct)
    phout_df = get_phout_df(phout_loc)
    res = reduce_phout_df(phout_df, t_periods, tags_delimtr=tags_delimtr)

    for tag, val in res.iteritems():
        try:
            lunaport_c1.stat_post(test_id, tag, __version__, stat_adapt_types(val['stat']))
        except LunaportClientError as e:
            if not eval_only:
                logger.error('Lunaport client call failed:{}'.format(e))
                raise

    exec_time = str(dt.datetime.now() - t_start)
    msg = [
        'Test:{} ',
        ' Phout reduced in: {} ',
        ' phout_df size:{} bytes({} MB)',
    ]
    logger.info('|'.join(msg).format(test_id, exec_time, *df_size(phout_df)))

    # assert
    t_start = dt.datetime.now()
    try:
        case_struct = lunaport_c1.case_get(test_struct['case']['id'])
    except LunaportClientError as e:
        logger.error('Lunaport client call failed:{}'.format(e))
        raise

    asserts = t_assert.get_asserts()
    exec_wrap = lambda oracle_part: t_assert.exec_assert(
        test_id, phout_df, res, oracle_part, asserts, logger=logger)

    t_evaluation = map(exec_wrap, case_struct['oracle'])
    t_resolution = all([el['passed'] for el in t_evaluation])
    try:
        eval_struct, eval_loc = lunaport_c1.eval_post(
            test_id, case_struct['oracle'], t_evaluation, t_resolution)
    except LunaportClientError as e:
        logger.error('Lunaport client call failed:{}'.format(e))
        raise
    exec_time = str(dt.datetime.now() - t_start)
    msg = 'Test:{} | oracle evaluation done in: {} | eval loc: {}'
    logger.info(msg.format(test_id, exec_time, eval_loc))

    diff = {
        'status': 'done',
        'resolution': t_resolution,
    }
    try:
        lunaport_c1.test_patch(test_id, diff)
    except LunaportClientError as e:
        logger.error('Lunaport client call failed:{}'.format(e))
        raise
    try:
        notify_test('on_finish', test_struct, t_resolution, case=case_struct)
    except ValueError as e:
        logger.warning('test:{} notify failed:'.format(test_id, e))
    logger.info('test:{} status:{}'.format(test_id, 'done'))

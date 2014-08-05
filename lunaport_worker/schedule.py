# -*- encoding: utf-8 -*-
"""
    lunaport_worker.tasks.schedule
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Periodic tasks. Timestamps in UTC.
"""
import datetime

from celery import Celery, chain
from celery.decorators import periodic_task
from celery.schedules import crontab

from tasks.utils import celery
from tasks.check import monitor_lunapark_running, monitor_tank_scheduled
from tasks.pullHosts import put_tanks, put_hosts_placement

@periodic_task(run_every=datetime.timedelta(seconds=30))
def monitor_lunapark_wrp():
    monitor_3rd_party_running.delay()

@periodic_task(run_every=datetime.timedelta(seconds=10))
def monitor_tank_scheduled_wrp():
    monitor_tank_scheduled.delay()

@periodic_task(run_every=datetime.timedelta(seconds=13600))
def update_hosts_data():
    put_tanks.delay()
    put_hosts_placement.delay()

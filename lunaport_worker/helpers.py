# -*- encoding: utf-8 -*-

"""
    lunaport_worker.helpers
    ~~~~~~~~~~~~~~~~~~~~~~~

    A set of functions and tools to help in routine.
"""

import sys
import logging

import graypy
import yaml


class LinkComposer(object):
    base = 'http://lunaport.domain.ru/'
    @classmethod
    def lnk_test_detail(cls, test_id):
        return '{}tests/{}/all'.format(cls.base, test_id)

    @classmethod
    def lnk_case_detail(cls, case_id):
        return '{}cases/{}'.format(cls.base, case_id)

    @classmethod
    def lnk_case_edit(cls, case_id):
        return '{}cases/{}/edit'.format(cls.base, case_id)

def compose_logger(cfg, name=None, extra=None):
    log_name = name or __name__.split('.')[0]
    logger = logging.getLogger(log_name)
    if not logger.handlers:
        if 'gray_gelf' in cfg['handlers'] and cfg['handlers']['gray_gelf']:
            handler = graypy.GELFHandler(*cfg['handlers']['gray_gelf'])
            logger.addHandler(handler)
        if 'file' in cfg['handlers'] and cfg['handlers']['file']:
            handler = logging.FileHandler(cfg['handlers']['file'])
            logger.addHandler(handler)
        if 'stream' in cfg['handlers'] and cfg['handlers']['stream']:
            logger.addHandler(logging.StreamHandler())


    logger.setLevel(getattr(logging, cfg['level'].upper()))
    for h in logger.handlers:
        h.setFormatter(logging.Formatter(cfg['format']))

    if extra:
        adapter = logging.LoggerAdapter(logger, extra)
        return adapter
    return logger


def get_worker_cfg(cfg_path):
    try:
        with open(cfg_path, 'r') as conf_fh:
            config = yaml.load(conf_fh)
            return config
    except IOError, e:
        sys.stderr.write('Could not read "%s": %s\n' % (cfg_path, e))
        sys.exit(1)
    except yaml.scanner.ScannerError, e:
        sys.stderr.write('Could not parse *main* config file: %s\n%s' %\
                         (cfg_path, e))
        sys.exit(1)

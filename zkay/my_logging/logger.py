import datetime
import json
import logging.config
import os
from logging import addLevelName

# current time
from zkay.config import cfg
from zkay.my_logging.log_context import full_log_context

timestamp = '{:%Y-%m-%d_%H-%M-%S}'.format(datetime.datetime.now())


# shutdown current logger (useful for debugging, ...)
def shutdown(handler_list=None):
    if handler_list is None:
        handler_list = []
    logging.shutdown(handler_list)


##########################
# add log level for DATA #
##########################
# LOG LEVELS
# existing:
# CRITICAL = 50
# ERROR = 40
# WARNING = 30
# INFO = 20
# DEBUG = 10
DATA = 5
addLevelName(DATA, "DATA")


def data(key, value):
    """
    Log (key, value) to log-level DATA
    """
    d = {'key': key, 'value': value, 'context': full_log_context}
    return logging.log(DATA, json.dumps(d))


def get_log_dir(parent_dir, label):
    """
    Convenience function for getting a log directory
    """
    d = os.path.join(parent_dir, label)

    # ensure log directory exists
    if not os.path.exists(d):
        os.makedirs(d)

    return d


def get_log_file(label='default', parent_dir=None, filename='log', include_timestamp=True):
    if parent_dir is None:
        parent_dir = os.path.realpath(cfg.log_dir)
    if label is None:
        log_dir = parent_dir
    else:
        log_dir = get_log_dir(parent_dir, label)

    if include_timestamp:
        filename += '_' + timestamp
    log_file = os.path.join(log_dir, filename)

    return log_file


def prepare_logger(log_file=None, silent=True):
    # shutdown previous logger (if one was registered)
    shutdown()

    # set log dir and console log level
    if log_file is None:
        log_file = get_log_file()

    console_loglevel = 'WARNING'

    if not silent:
        print(f"Saving logs to {log_file}*...")

    # set default logging settings
    default_logging = {
        'version': 1,
        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)s]: %(message)s',
                'datefmt': '%Y-%m-%d_%H-%M-%S'
            },
            'minimal': {
                'format': '%(message)s'
            },
        },
        'filters': {
            'onlydata': {
                '()': OnlyData
            }
        },
        'handlers': {
            'default': {
                'level': console_loglevel,
                'formatter': 'standard',
                'class': 'logging.StreamHandler',
            },
            'fileinfo': {
                'level': 'INFO',
                'formatter': 'standard',
                'filename': log_file + '_info.log',
                'mode': 'w',
                'class': 'logging.FileHandler',
            },
            'filedebug': {
                'level': 'DEBUG',
                'formatter': 'standard',
                'filename': log_file + '_debug.log',
                'mode': 'w',
                'class': 'logging.FileHandler',
            },
            'filedata': {
                'level': 'DATA',
                'formatter': 'minimal',
                'filename': log_file + '_data.log',
                'mode': 'w',
                'class': 'logging.FileHandler',
                'filters': ['onlydata']
            }
        },
        'loggers': {
            '': {
                'handlers': ['default', 'fileinfo', 'filedebug', 'filedata'],
                'level': 0
            }
        }
    }
    logging.config.dictConfig(default_logging)


class OnlyData(logging.Filter):

    def filter(self, record):
        # print(record.__dict__)
        return record.levelno == DATA


# register a default logger (can be overwritten later)
prepare_logger()

# -*- coding: utf-8 -*-
# @Author: TC
# @Date:   2024-05-31 14:22:15
# @Last Modified by:   Your name
# @Last Modified time: 2024-06-17 15:16:57
import logging
from colorlog import ColoredFormatter
import sys

LOGFORMAT = "  %(log_color)s%(asctime)s %(levelname)-8s[%(filename)-20s:%(lineno)-04d]%(reset)s | %(log_color)s%(message)s%(reset)s"

levels = {
        'DEBUG':    'cyan',
        'INFO':     'bold_green',
        'WARNING':  'yellow',
        'ERROR':    'bold_red',
        'CRITICAL': 'bold_purple',
        }
        
logLevel = logging.INFO
formatter = ColoredFormatter(LOGFORMAT, datefmt='%Y-%m-%d %H:%M:%S', log_colors = levels)

ch = logging.StreamHandler()
ch.setLevel(logLevel)
ch.setFormatter(formatter)
# formatter = logging.Formatter('%(asctime)s | %(levelname)-8s [%(filename)-20s:%(lineno)-04d] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

logger = logging.getLogger()
logger.handlers = []
logger.setLevel(logLevel)
logger.addHandler(ch)
# log.removeHandler(stream)
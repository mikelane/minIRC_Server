#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Set up the logging environment

Copied from Stack Overflow:
http://stackoverflow.com/questions/7621897/python-logging-module-globally"""

# Imports
import logging
import os

__author__ = "Michael Lane"
__email__ = "mikelane@gmail.com"
__copyright__ = "Copyright 2017, Michael Lane"
__license__ = "MIT"


def setup_custom_logger(name, level):
    logger = logging.getLogger(name=name)

    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s - %(message)s')

    os.makedirs('logs/', exist_ok=True)
    file_handler = logging.FileHandler('logs/server.log')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)  # Always log debug information

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    if level >= 4:
        stream_handler.setLevel(logging.DEBUG)
    elif level == 3:
        stream_handler.setLevel(logging.INFO)
    elif level == 2:
        stream_handler.setLevel(logging.WARNING)
    elif level == 1:
        stream_handler.setLevel(logging.ERROR)
    else:
        stream_handler.setLevel(logging.CRITICAL)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger

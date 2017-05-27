#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Short description

Long description
"""

# Imports
import asyncio

from minIRC_Server import log
from minIRC_Server.server import Server

__author__ = "Michael Lane"
__email__ = "mikelane@gmail.com"
__copyright__ = "Copyright 2017, Michael Lane"
__license__ = "MIT"

logger = log.setup_custom_logger('root', level=5)

HOST = '127.0.0.1'
PORT = 10101

channels = set()
users = {}

loop = asyncio.get_event_loop()
coro = loop.create_server(lambda: Server(loop), HOST, PORT)
server = loop.run_until_complete(coro)
logger.debug(f'Serving on {server.sockets[0].getsockname()}')

try:
    loop.run_forever()
except KeyboardInterrupt:
    logger.info('Keyboard interrupt detected. Stopping server.')
finally:
    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()

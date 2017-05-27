#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""A minIRC Server

The starting place for this code was the Python 3.6 documentation for
the asyncio library.
"""

import asyncio
import functools
import json
import logging
import re
import configparser

from minIRC_Server import log
from minIRC_Server.channel import Channel

__author__ = "Michael Lane"
__email__ = "mikelane@gmail.com"
__copyright__ = "Copyright 2017, Michael Lane"
__license__ = "MIT"

logger = log.setup_custom_logger('root.server', level=5)
logging.getLogger('asyncio').setLevel(logging.DEBUG)

configs = configparser.ConfigParser()
configs.read('settings.ini')
HOST = configs['SERVER']['HOST']
PORT = configs['SERVER']['PORT']

channels = {}

users = {}


class Server(asyncio.Protocol):
    client_counter = 0

    def __init__(self, loop):
        global users
        self.loop = loop
        self.pong_received = False
        self.ping_delay = 10
        self.client_counter += 1
        self.username = f'user_{self.client_counter}'  # A default username
        users[self.username] = self
        self.my_channels = {}
        self.my_private_messages = {}
        self.dispatcher = {
            'LOGIN': self.login,
            'QUIT': self.quit,
            'CREATECHAN': self.create_channel,
            'LIST': self.list_channels,
            'JOIN': self.join_channels,
            'USERS': self.list_channel_users,
            'SENDMSG': self.message,
            'KICK': self.kick_user
        }

    def __hash__(self) -> int:
        return hash(tuple([self.host, self.port]))

    def __eq__(self, o: object) -> bool:
        return (o.host, o.port) == (self.host, self.port)

    def __repr__(self) -> str:
        return f'{self.host}:{self.port} - {self.username}'

    def __str__(self) -> str:
        return self.__repr__()

    def make_response(self, command, kwargs):
        if not kwargs:
            kwargs = None
        return json.dumps({command: kwargs}).encode()

    def send_response(self, command, **kwargs):
        response = self.make_response(command, kwargs)
        logger.debug(f'{str(self)} - Sending the following response: {response}')
        self.loop.call_soon(self.transport.write, response)

    def send_message(self, response):
        resp = json.dumps(response).encode()
        logger.debug(f'{str(self)} - Sending the following response: {resp}')
        self.loop.call_soon(self.transport.write, resp)

    def connection_made(self, transport):
        self.host, self.port = transport.get_extra_info('peername')
        logger.debug(f'{str(self)} - Connection established')
        users[self.username] = self
        self.transport = transport
        self.ping_handler = self.loop.call_later(self.ping_delay, self.ping)

    def data_received(self, data):
        data = data.strip().decode()
        logger.debug(f'{str(self)} - Data received: {data}')
        # This is where we parse the incoming messages and do things with them
        if data == '{"PING": "PONG"}':
            self.pong_received = True
        else:
            try:
                parsed_message = json.loads(data)
            except json.decoder.JSONDecodeError:
                print(f'This is where I log something about ill-formed response')
                return
            command = next(iter(parsed_message))
            kwargs = parsed_message[command]
            callback = functools.partial(self.dispatcher[command], **(kwargs or {}))
            self.loop.call_soon(callback=callback)

    def ping(self):
        self.pong_received = False
        self.transport.write(b'{"PING": null}')
        logger.debug(f'{str(self)} - Sent PING')
        self.loop.call_later(1, self.check_pong)

    def check_pong(self):
        if self.pong_received:
            logger.debug(f'{str(self)} - PONG received. Scheduling next ping')
            self.ping_handler = self.loop.call_later(self.ping_delay, self.ping)
        else:
            logger.debug(f'{str(self)} - PONG not received. Ensuring connection is closed.')
            self.ping_handler.cancel()
            self.transport.close()

    def login(self, NICK):
        global users
        if NICK in users:
            self.send_response('ERROR', STATUS=409, MESSAGE=f'Username {NICK} already exists')
            return
        del (users[self.username])
        self.username = NICK
        users[self.username] = self
        logger.debug(f'{str(self)} - Username set to {self.username}')
        self.send_response('SUCCESS', STATUS=200, MESSAGE=f'Username changed to {NICK}')

    def quit(self):
        global users
        logger.debug(f'{str(self)} - Quit received. Closing the socket.')
        self.transport.write(b'GOODBYE')
        self.transport.close()

    def remove_user_from_channels(self):
        global channels
        logger.debug(f'{str(self)} - QUIT received. Cleaning up channels')
        to_remove = set()
        for channel in self.my_channels.values():
            if channel.remove(self):  # True if no more users remain in the channel
                to_remove |= {channel.name}
        for name in to_remove:  # Cull the empty channels.
            del (channels[name])
        logger.debug(f'{str(self)} - The following channels were removed: {[str(c) for c in to_remove]}')

    def create_channel(self, NAME):
        global channels
        if NAME not in channels:
            channel = Channel(NAME, self)
            logger.debug(f'{str(self)} - Creating channel name {NAME}, Moderator {self.username}')
            channels[channel.name] = channel
            self.my_channels[channel.name] = channel
            self.send_response('SUCCESS', STATUS=200, MESSAGE=f'Channel {NAME} created successfully')
            logger.debug(f'{str(self)} - The my_channels data structure is now {[k for k in self.my_channels.keys()]}')
        else:
            self.send_response('ERROR', STATUS=409, MESSAGE=f'Channel {NAME} already exists')

    def list_channels(self, FILTER):
        if FILTER:
            regex = re.compile(FILTER)
        else:
            regex = re.compile(r'.*')
        result = []
        for channel in channels:
            if re.match(regex, str(channel)):
                result.append(str(channel))
        self.send_response('SUCCESS', STATUS=200, MESSAGE=str(result))

    def join_channels(self, CHANNELS):
        global channels
        response = {'ERROR': [], 'SUCCESS': []}
        if type(CHANNELS) == str:
            logger.debug(
                f'{str(self)} - Error. Returning to user: 409 Malformed request. Channel names must be passed as a list.')
            self.send_response('ERROR', STATUS=401,
                               MESSAGE=f'Malformed request. Channel names must be passed as a list')
            return
        for channel_name in CHANNELS:
            if channel_name not in channels:
                logger.debug(f'{str(self)} - Error. User trying to join channel that does not exist. Returning 404.')
                response['ERROR'].append({'STATUS': 404, 'MESSAGE': f'Channel {channel_name} does not exist.'})
                # self.send_response('ERROR', STATUS=404, MESSAGE=f'Channel {channel_name} does not exist.')
                continue
            try:
                channels[channel_name].join(self)
                self.my_channels[channel_name] = channels[channel_name]
                response['SUCCESS'].append({'STATUS': 200, 'MESSAGE': f'Channel {channel_name} joined successfully.'})
            except KeyError:
                logger.debug(f'{str(self)} - Error. User already in channel. Returning 402.')
                response['ERROR'].append(
                    {'STATUS': 402, 'MESSAGE': f'User {self.username} already in channel {channel_name}'})
                # self.send_response('ERROR', STATUS=402, MESSAGE=f'User {self.username} already in channel {channel_name}')
                continue
        self.send_message(response)

    def list_channel_users(self, NAME=None, FILTER=None):
        if not NAME:
            self.send_response('ERROR', STATUS=401, MESSAGE='Malformed request. Must send name of channel.')
            return
        if FILTER:
            regex = re.compile(FILTER)
        else:
            regex = re.compile('.*')

        try:
            users = list(channels[NAME].users)
            logger.debug(f'{str(self)} - Sending STATUS: 200 MESSAGE: {users}')
            self.send_response('SUCCESS', STATUS=200, MESSAGE=users)
        except KeyError:
            logger.debug(f'{str(self)} - Error. There is no channel {NAME}')
            self.send_message({'ERROR': {'STATUS': 404, 'MESSAGE': f'There is no channel {NAME}'}})

    def message(self, MESSAGE, USERS=None, CHANNELS=None):
        if not MESSAGE:
            logger.debug(f'{str(self)} - Error. STATUS: 401, MESSAGE: Malformed request. Message is required.')
            self.send_response('ERROR', STATUS=401, MESSAGE='Malformed request. Message is required.')
            return
        response = {'ERROR': [], 'SUCCESS': []}
        if USERS:
            if type(USERS) != list:
                USERS = [USERS]
            for user_name in USERS:
                if user_name not in users:
                    logger.debug(f'{str(self)} - Sending Error. STATUS: 404, MESSAGE: User {user_name}')
                    response['ERROR'].append({'STATUS': 404, 'MESSAGE': f'User {user_name} not found.'})
                    continue
                else:
                    logger.debug(f'{str(self)} - Sending message {MESSAGE} to {users[user_name]}')
                    users[user_name].send_message(
                        {'DIRECTMSG': {'FROM': self.username, 'TO': users[user_name].username, 'MESSAGE': MESSAGE}})
        elif CHANNELS:
            if type(CHANNELS) != list:
                CHANNELS = [CHANNELS]
            for channel_name in CHANNELS:
                try:
                    channels[channel_name].broadcast(MESSAGE, self.username)
                    logger.debug(f'{str(self)} - Sent message to {channel_name}')
                except KeyError:
                    logger.debug(f'{str(self)} - Error. STATUS: 404, MESSAGE: Channel {channel_name} not found')
                    response['ERROR'].append({'STATUS': 404, 'MESSAGE': f'Channel {channel_name} not found.'})
        else:
            logger.debug(
                f'{str(self)} - Error: STATUS: 401, MESSAGE: Malformed request. User(s) or channel(s) required.')
            self.send_response('ERROR', STATUS=401, MESSAGE=f'Malformed request. User(s) or channel(s) required.')

        # Send back the response codes
        self.send_message(response)

    def kick_user(self, NICKS, MESSAGE=None):
        global users
        # @TODO more robust user management
        if self.username != 'Admin':
            logger.debug(f'{str(self)} - Error: STATUS: 401, MESSAGE: Unauthorized')
            self.send_response('ERROR', STATUS=401, MESSAGE='Unauthorized')
        if type(NICKS) != list:
            NICKS = [NICKS]
        for nick in NICKS:
            try:
                logger.debug(f'Sending KICK message to {nick}')
                users[nick].send_message(
                    {'KICK': {'MESSAGE': f'You were kicked by {self.username}. Message: {MESSAGE}'}})
                logger.debug(f'Calling users[nick].quit()')
                users[nick].quit()
                self.send_response('SUCCESS', STATUS=200, MESSAGE=f'User {nick} kicked.')
            except KeyError:
                self.send_response('ERROR', STATUS=404, MESSAGE=f'User {nick} not found.')

    def connection_lost(self, exc):
        logger.debug(f'{str(self)} - Connection lost. Cleaning up user.')
        self.ping_handler.cancel()
        if self.username in users:
            logger.debug(f'{str(self)} - Attempting to remove {self.username} from users')
            logger.debug(f'{str(self)} - Before {[u for u in users]}')
            del (users[self.username])
            logger.debug(f'{str(self)} - After: {[u for u in users]}')
        self.remove_user_from_channels()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    coro = loop.create_server(lambda: Server(loop), HOST, PORT)
    server = loop.run_until_complete(coro)

    logger.debug(f'{str(self)} - Serving on {server.sockets[0].getsockname()}')
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info('Keyboard interrupt detected. Stopping server.')
    finally:
        server.close()
        loop.run_until_complete(server.wait_closed())
        loop.close()

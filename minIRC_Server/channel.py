#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""A class to manage minIRC rooms"""

# Imports
from datetime import datetime

from minIRC_Server import log

__author__ = "Michael Lane"
__email__ = "mikelane@gmail.com"
__copyright__ = "Copyright 2017, Michael Lane"
__license__ = "MIT"

logger = log.setup_custom_logger('root.channel', level=5)


class Channel:
    def __init__(self, name, moderator):
        self.name = name
        self.moderator = moderator
        self.users = {moderator}

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, o: object) -> bool:
        return o.name == self.name

    def __repr__(self) -> str:
        return f'Channel(name={self.name}, moderator={self.moderator})'

    def __str__(self) -> str:
        return self.name

    def join(self, user):
        if user in self.users:
            logger.debug(f'User {user.username} has already joined this channel {self.name}.')
            raise KeyError(f'User {user.username} has already joined channel {self.name}.')
        self.users |= set([user])
        user.send_message({'CHANHIST': {'CHANNEL': self.name, }})

    def remove(self, user):
        if len(self.users) == 1:
            return True  # Just kill the room if nobody is left in it.
        if user.username == self.moderator:
            # Setting an arbitrary user to be moderator probably isn't a good idea.
            self.moderator = self.users.pop()
        self.users ^= set([user])

    def broadcast(self, message, from_user):
        time = str(datetime.now())
        for user in self.users:
            user.send_message({'CHANMSG': {'CHANNEL': self.name, 'TIME': time, 'FROM': from_user, 'MESSAGE': message}})


if __name__ == '__main__':
    pass

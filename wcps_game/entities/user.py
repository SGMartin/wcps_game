import asyncio
import time
from wcps_game.entities import BaseNetworkEntity


class User(BaseNetworkEntity):
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):

        # network properties
        self.reader = reader
        self.writer = writer

        # authorization properties
        self.authorized = False
        self.session_id = None
        self.rights = -1
        self.username = None
        
        # game properties
        self.displayname = ""
        self.last_ping = time.time() * 1000  # milliseconds
        self.ping = 0
        self.is_updated_ping = True

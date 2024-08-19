import asyncio
import logging

from datetime import datetime
import time

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.rooms import Room

from wcps_core.constants import Ports, ServerTypes, InternalKeys
from wcps_core.packets import OutPacket

from wcps_game.config import settings
from wcps_game.database import (
    get_user_details_and_stats,
    update_user_money,
    update_user_details,
    update_user_stats
)
from wcps_game.game.constants import Premium, ChannelType, get_level_for_exp
from wcps_game.game.channels import Channel
from wcps_game.game.user_stats import UserStats
from wcps_game.game.inventory import Inventory
from wcps_game.entities.network_entities import NetworkEntity
from wcps_game.handlers import get_handler_for_packet
from wcps_game.networking import ClientXorKeys
from wcps_game.packets.packet_list import PacketList
from wcps_game.packets.packet_factory import PacketFactory


class User(NetworkEntity):
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, game_server):
        super().__init__(
            reader=reader,
            writer=writer,
            xor_key_send=ClientXorKeys.SEND,
            xor_key_receive=ClientXorKeys.RECEIVE
            )
        # network properties
        self.reader = reader
        self.writer = writer
        self.this_server = game_server

        # UDP properties
        self.remote_end_point = None
        self.remote_port = None
        self.local_end_point = None
        self.local_port = None

        # authorization properties
        self.authorized = False
        self.session_id = None
        self.internal_id = -1  # probably legacy but maybe the client uses it for some stuff?
        self.rights = -1
        self.username = None

        # game properties
        self.displayname = ""
        self.xp = 0
        self.money = 0
        self.channel = 0
        self.room = None
        self.userlist_page = 0
        self.room_page = 0

        # Premium data
        self.premium = Premium.F2P
        self.premium_seconds_left = -1
        self.premium_expire_date = 0

        self.last_ping = datetime.now()
        self.ping = 0
        self.is_updated_ping = True

        # stats
        self.stats = None

        # inventory and equipment
        self.inventory = None

    def get_handler_for_packet(self, packet_id):
        return get_handler_for_packet(packet_id)

    async def authorize(self, username: str, session_id: int, rights: int) -> bool:
        self.username = username
        self.session_id = session_id
        self.rights = rights
        self.authorized = True

        self.stats = UserStats(username=self.username)

        details_load_successful = await self.load_user_details_from_database()
        inventory_load_successful = await self.load_inventory_data()

        return details_load_successful and inventory_load_successful

    async def load_user_details_from_database(self) -> bool:
        database_details = await get_user_details_and_stats(username=self.username)
        success = False
        if database_details:
            self.money = database_details["money"]
            self.xp = database_details["xp"]
            self.premium = database_details["premium"]
            self.premium_expire_date = database_details["premium_expiredate"]
            await self.stats.update_kills(kills=int(database_details["kills"]))
            await self.stats.update_deaths(deaths=int(database_details["deaths"]))

            success = True

        return success

    async def load_inventory_data(self) -> bool:
        self.inventory = Inventory(user=self)
        can_load = await self.inventory.get_inventory_and_equipment_from_db()
        return can_load

    async def disconnect(self):
        logging.info("Called disconnect to client")

        # Call the base class's disconnect for network issues
        await super().disconnect()

        self.reader = None
        self.writer = None

        if self.authorized:
            self.authorized = False
            try:
                # TODO: improve leave server routine including mysql queries
                await self.this_server.channels[self.channel].remove_user(self)
                await self.this_server.remove_player(self.username)
            except Exception as e:
                logging.exception(f"Error removing player {self.username}: {e}")

    # TODO: Do we need a lock here?
    async def send_ping(self):
        if not self.is_updated_ping:
            # await self.disconnect()
            # TODO: Have a retry mechanism here before disconnecting
            logging.error(f"Could not send ping to {self.username}")
        else:
            self.is_updated_ping = False
            await self.update_premium_status()
            user_ping_packet = PacketFactory.create_packet(
                packet_id=PacketList.PING,
                u=self
            )
            await self.send(user_ping_packet.build())

    async def answer_ping(self):
        self.is_updated_ping = True
        ping_diff = datetime.now() - self.last_ping
        self.ping = int(ping_diff.total_seconds() * 1000)  # Convert to milliseconds

    async def update_premium_status(self):
        if self.premium_expire_date > 0 or self.premium != Premium.F2P:
            current_time_epoch = int(time.time())
            premium_time_left = int(self.premium_expire_date - current_time_epoch)

            if premium_time_left <= 0:
                self.premium_expire_date = 0
                self.premium_seconds_left = -1
                self.premium = Premium.F2P
            else:
                self.premium_seconds_left = premium_time_left

    async def update_money(self, new_money: int):
        if await update_user_money(username=self.username, new_money=new_money):
            self.money = new_money
        else:
            logging.error(f"Failed to update money for {self.username} to {new_money}")

    async def end_game(self, xp_earned, money_earned):
        current_xp = self.xp
        new_xp = current_xp + xp_earned
        self.xp = new_xp

        # have we leveled up?
        current_level = get_level_for_exp(current_xp)
        new_level = get_level_for_exp(new_xp)

        if new_level > current_level:
            levels_gained = new_level - current_level

            reward_money = levels_gained * 2500  # TODO: customize this
            self.money += reward_money

            level_up = PacketFactory.create_packet(
                packet_id=PacketList.DO_PROMOTION,
                user=self,
                money_earned=reward_money
            )
            await self.send(level_up.build())

        self.money = self.money + money_earned

        # Save everything to the database
        await update_user_details(self)

    async def update_stats(self):
        # Call database method
        await update_user_stats(user=self)

    def set_room(self, room: "Room", room_slot: int):
        self.room = room
        self.room_slot = room_slot
        # reset room and user list page
        self.room_page = 0
        self.userlist_page = 0


class GameServer(NetworkEntity):
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        super().__init__(
            reader=reader,
            writer=writer,
            xor_key_send=InternalKeys.XOR_GAME_SEND,
            xor_key_receive=InternalKeys.XOR_AUTH_SEND
            )

        # Network data
        # TODO: configs here
        self.name = settings().server_name
        self.ip = settings().server_ip
        self.port = Ports.GAME_CLIENT

        # Authorization properties
        self.is_first_authorized = True
        self.authorized = False
        self.session_id = None
        self.id = settings().authentication_id

        # Game properties
        self.max_players = 3600
        self.current_rooms = 0
        self.server_type = ServerTypes.ENTIRE
        self.premium_only = False

        self.online_users = {}

        self.channels = {
            ChannelType.CQC: Channel(channel_type=ChannelType.CQC),
            ChannelType.URBANOPS: Channel(channel_type=ChannelType.URBANOPS),
            ChannelType.BATTLEGROUP: Channel(channel_type=ChannelType.BATTLEGROUP)
        }
        # Lock to ensure thread safety and asyncio safety
        self.lock = asyncio.Lock()

    def get_handler_for_packet(self, packet_id):
        return get_handler_for_packet(packet_id)

    async def add_player(self, u: User):
        async with self.lock:
            if not u.username:
                raise Exception("Attempt to add an unnamed user")
            if u.username in self.online_users:
                raise Exception(f"User {u.username} already exists")
            self.online_users[u.username] = u

    # TODO: send internal packet to auth
    async def remove_player(self, username):
        async with self.lock:
            if username in self.online_users:
                del self.online_users[username]
                logging.info(f"Removed player {username}")
            else:
                raise Exception(f"User {username} does not exist")

    async def is_online(self, username) -> bool:
        async with self.lock:
            return username in self.online_users

    def get_player_count(self) -> int:
        return len(self.online_users)

    async def get_player(self, username) -> User:
        async with self.lock:
            user = self.online_users.get(username)
            return user

    async def get_player_by_displayname(self, displayname) -> User:
        async with self.lock:
            for user in self.online_users.values():
                if user.displayname == displayname:
                    return user
            return None

    async def broadcast_packet_to_lobby(self, packet: OutPacket):
        for user in self.online_users.values():
            if user.authorized and user.room is None:
                await user.send(packet)

    def get_player_by_session(self, session_id: int):
        for user in self.online_users.values():
            if user.authorized and user.session_id == session_id:
                return user
        return None

    def authorize(self, session_id: int):
        self.session_id = session_id
        self.authorized = True
        self.is_first_authorized = False

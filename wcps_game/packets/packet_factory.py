from wcps_game.packets.packet_list import PacketList

from wcps_game.packets.internal_gameserver_details import GameServerAuthentication
from wcps_game.packets.internal_gameserver_status import GameServerStatus
from wcps_game.packets.internal_player_auth import InternalPlayerAuthorization

from wcps_game.packets.request_server_time import ServerTime
from wcps_game.packets.player_authorization import PlayerAuthorization
from wcps_game.packets.leave_server import LeaveServer
from wcps_game.packets.ping import Ping
from wcps_game.packets.userlist import UserList
from wcps_game.packets.equipment import Equipment
from wcps_game.packets.update_inventory import UpdateInventory
from wcps_game.packets.itemshop import ItemShop
from wcps_game.packets.coupon import Coupon
from wcps_game.packets.use_px_item import UsePXItem
from wcps_game.packets.select_channel import SelectChannel
from wcps_game.packets.chat import Chat
from wcps_game.packets.room import (
    RoomCreate,
    RoomLeave,
    RoomList,
    RoomInfoUpdate,
    RoomJoin,
    RoomPlayers,
)
from wcps_game.packets.game_process import GameProcess
from wcps_game.packets.game_clock import GameUpdateClock
from wcps_game.packets.scoreboard import ScoreBoard
from wcps_game.packets.end_game import EndGame
from wcps_game.packets.promotion import Promotion


class PacketFactory:
    packet_classes = {
        # Internal
        PacketList.INTERNAL_GAME_AUTHENTICATION: GameServerAuthentication,
        PacketList.INTERNAL_GAME_STATUS: GameServerStatus,
        PacketList.INTERNAL_PLAYER_AUTHENTICATION: InternalPlayerAuthorization,
        # Lobby
        PacketList.REQUEST_SERVER_TIME: ServerTime,
        PacketList.PLAYER_AUTHORIZATION: PlayerAuthorization,
        PacketList.SELECT_CHANNEL: SelectChannel,
        PacketList.PING: Ping,
        PacketList.LEAVE_SERVER: LeaveServer,
        PacketList.USERLIST: UserList,
        PacketList.CHAT: Chat,
        # Shop
        PacketList.EQUIPMENT: Equipment,
        PacketList.UPDATE_INVENTORY: UpdateInventory,
        PacketList.ITEMSHOP: ItemShop,
        PacketList.USEITEM: UsePXItem,
        PacketList.COUPON: Coupon,
        # Room
        PacketList.ROOM_CREATE: RoomCreate,
        PacketList.DO_ROOM_LIST: RoomList,
        PacketList.DO_EXIT_ROOM: RoomLeave,
        PacketList.DO_ROOM_INFO_CHANGE: RoomInfoUpdate,
        PacketList.DO_JOIN_ROOM: RoomJoin,
        PacketList.DO_GAME_USER_LIST: RoomPlayers,
        # Game
        PacketList.DO_GAME_PROCESS: GameProcess,
        PacketList.DO_GAME_UPDATE_CLOCK: GameUpdateClock,
        PacketList.DO_GAME_SCORE: ScoreBoard,
        PacketList.DO_GAME_RESULT: EndGame,
        PacketList.DO_PROMOTION_OLD: Promotion
    }

    @staticmethod
    def create_packet(packet_id: int, *args, **kwargs):
        packet_class = PacketFactory.packet_classes.get(packet_id)
        if packet_class:
            return packet_class(*args, **kwargs)
        else:
            raise ValueError(f"Unknown packet ID: {packet_id}")

    @staticmethod
    def get_packet_class(packet_id: int):
        return PacketFactory.packet_classes.get(packet_id)

    @staticmethod
    def get_packet_id(packet_class):
        for packet_id, cls in PacketFactory.packet_classes.items():
            if cls == packet_class:
                return packet_id
        return None

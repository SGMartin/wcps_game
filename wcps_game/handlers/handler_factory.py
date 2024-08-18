import logging

from wcps_game.packets.packet_list import PacketList

from wcps_game.handlers.packet_handler import PacketHandler
from wcps_game.handlers.internal_auth_connection import AuthConnectionHandler
from wcps_game.handlers.internal_server_authentication import AuthorizeServerHandler
from wcps_game.handlers.internal_client_authentication import AuthorizeClientHandler
from wcps_game.handlers.request_server_time import RequestServerTimeHandler
from wcps_game.handlers.client_authentication import ClientAuthenticationHandler
from wcps_game.handlers.leave_server import LeaveServerHandler
from wcps_game.handlers.ping import PingHandler
from wcps_game.handlers.select_channel import SelectChannelHandler
from wcps_game.handlers.chat import ChatHandler
from wcps_game.handlers.userlist import UserListHandler
from wcps_game.handlers.equipment import EquipmentHandler
from wcps_game.handlers.itemshop import ItemShopHandler
from wcps_game.handlers.coupon import CouponHandler
from wcps_game.handlers.room_handlers import (
    RoomCreateHandler,
    RoomJoinHandler,
    RoomLeaveHandler,
    RoomListHandler,
)
from wcps_game.handlers.game_proccess import GameProcessHandler
from wcps_game.handlers.scoreboard import ScoreBoardHandler

# Dictionary to map packet IDs to handler classes
HANDLER_MAP = {
    # Internal server-server packets
    PacketList.INTERNAL_GAME_AUTHENTICATION: AuthorizeServerHandler,
    PacketList.INTERNAL_CLIENT_CONNECTION: AuthConnectionHandler,
    PacketList.INTERNAL_PLAYER_AUTHENTICATION: AuthorizeClientHandler,
    # Server - client lobby
    PacketList.REQUEST_SERVER_TIME: RequestServerTimeHandler,
    PacketList.PLAYER_AUTHORIZATION: ClientAuthenticationHandler,
    PacketList.LEAVE_SERVER: LeaveServerHandler,
    PacketList.SELECT_CHANNEL: SelectChannelHandler,
    PacketList.PING: PingHandler,
    PacketList.USERLIST: UserListHandler,
    PacketList.CHAT: ChatHandler,
    # Shop
    PacketList.EQUIPMENT: EquipmentHandler,
    PacketList.ITEMSHOP: ItemShopHandler,
    PacketList.COUPON: CouponHandler,
    # Room
    PacketList.ROOM_CREATE: RoomCreateHandler,
    PacketList.DO_ROOM_LIST: RoomListHandler,
    PacketList.DO_EXIT_ROOM: RoomLeaveHandler,
    PacketList.DO_JOIN_ROOM: RoomJoinHandler,
    # Game
    PacketList.DO_GAME_PROCESS: GameProcessHandler,
    PacketList.DO_GAME_SCORE: ScoreBoardHandler
}


def get_handler_for_packet(packet_id: int) -> PacketHandler:
    handler_class = HANDLER_MAP.get(packet_id)
    if handler_class:
        return handler_class()
    else:
        logging.info(f"Unknown packet ID {packet_id}")
        return None

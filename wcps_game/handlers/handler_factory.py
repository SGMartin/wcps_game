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
    RoomQuickJoinHandler,
    RoomLeaveHandler,
    RoomListHandler,
    RoomInviteHandler,
    RoomExpelHandler,
    RoomSpectateHandler
)
from wcps_game.handlers.game_proccess import GameProcessHandler
from wcps_game.handlers.scoreboard import ScoreBoardHandler
from wcps_game.handlers.leave_vehicle_world import LeaveVehicleHandler
from wcps_game.handlers.explosives import ExplosivesHandler

# Dictionary to map packet IDs to handler classes
HANDLER_MAP = {
    # Internal server-server packets
    PacketList.INTERNAL_GAME_AUTHENTICATION: AuthorizeServerHandler,
    PacketList.INTERNAL_CLIENT_CONNECTION: AuthConnectionHandler,
    PacketList.INTERNAL_PLAYER_AUTHENTICATION: AuthorizeClientHandler,
    # Server - client lobby
    PacketList.DO_SERIAL_GSERV: RequestServerTimeHandler,
    PacketList.DO_JOIN_SERV: ClientAuthenticationHandler,
    PacketList.DO_CLOSE_WARROCK: LeaveServerHandler,
    PacketList.DO_SET_CHANNEL: SelectChannelHandler,
    PacketList.DO_KEEPALIVE: PingHandler,
    PacketList.DO_USER_LIST: UserListHandler,
    PacketList.DO_CHAT: ChatHandler,
    # Shop
    PacketList.DO_BITEM_CHANGE: EquipmentHandler,
    PacketList.DO_ITEM_PROCESS: ItemShopHandler,
    PacketList.DO_COUPON: CouponHandler,
    # Room
    PacketList.ROOM_CREATE: RoomCreateHandler,
    PacketList.DO_ROOM_LIST: RoomListHandler,
    PacketList.DO_EXIT_ROOM: RoomLeaveHandler,
    PacketList.DO_JOIN_ROOM: RoomJoinHandler,
    PacketList.DO_QUICK_JOIN: RoomQuickJoinHandler,
    PacketList.DO_GUEST_JOIN: RoomSpectateHandler,
    PacketList.DO_INVITATION: RoomInviteHandler,
    PacketList.DO_EXPEL_PLAYER: RoomExpelHandler,
    # Game
    PacketList.DO_GAME_PROCESS: GameProcessHandler,
    PacketList.DO_BOMB_PROCESS: ExplosivesHandler,
    PacketList.DO_GAME_SCORE: ScoreBoardHandler,
    PacketList.DO_VEHICLE_LEAVE_WORLD: LeaveVehicleHandler
}


def get_handler_for_packet(packet_id: int) -> PacketHandler:
    handler_class = HANDLER_MAP.get(packet_id)
    if handler_class:
        return handler_class()
    else:
        logging.info(f"Unknown packet ID {packet_id}")
        return None

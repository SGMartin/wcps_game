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


class PacketFactory:
    packet_classes = {
        # Internal
        PacketList.INTERNAL_GAME_AUTHENTICATION: GameServerAuthentication,
        PacketList.INTERNAL_GAME_STATUS: GameServerStatus,
        PacketList.INTERNAL_PLAYER_AUTHENTICATION: InternalPlayerAuthorization,
        # Lobby
        PacketList.REQUEST_SERVER_TIME: ServerTime,
        PacketList.PLAYER_AUTHORIZATION: PlayerAuthorization,
        PacketList.PING: Ping,
        PacketList.LEAVE_SERVER: LeaveServer,
        PacketList.USERLIST: UserList,
        # Shop
        PacketList.EQUIPMENT: Equipment

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

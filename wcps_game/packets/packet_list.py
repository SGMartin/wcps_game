from wcps_core.packets import PacketList as cp


class ClientXorKeys:
    SEND = 0x96
    RECEIVE = 0xC3


class PacketList:
    # Internal
    INTERNAL_GAME_AUTHENTICATION = cp.GameServerAuthentication
    INTERNAL_GAME_STATUS = cp.GameServerStatus
    INTERNAL_CLIENT_CONNECTION = cp.ClientConnection
    INTERNAL_PLAYER_AUTHENTICATION = cp.ClientAuthentication
    # Lobby
    LEAVE_SERVER = 0x6000
    REQUEST_SERVER_TIME = 0x6100
    PLAYER_AUTHORIZATION = 0x6200
    PING = 0x6400
    USERLIST = 0x7100
    # Shop
    EQUIPMENT = 0x7512
    UPDATE_INVENTORY = 0x7900  # Also controls when items expire
    ITEMSHOP = 0x7600
    USEITEM = 0x7800

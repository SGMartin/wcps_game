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
    SELECT_CHANNEL = 0x7001
    USERLIST = 0x7100
    CHAT = 0x7400
    # Shop
    EQUIPMENT = 0x7512
    UPDATE_INVENTORY = 0x7900  # Also controls when items expire
    ITEMSHOP = 0x7600
    USEITEM = 0x7800
    COUPON = 0x8100

    # Room
    DO_ROOM_LIST = 0x7200
    ROOM_CREATE = 0x7300
    DO_JOIN_ROOM = 0x7310
    DO_EXIT_ROOM = 0x7340
    DO_ROOM_INFO_CHANGE = 0x7210
    DO_GAME_USER_LIST = 0x7500

    # Game packet
    DO_GAME_PROCESS = 0x7530

    # Subpackets of DO_GAME_PROCESS
    DO_MAP_CLICK = 0x33

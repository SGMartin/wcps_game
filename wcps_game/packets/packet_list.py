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
    DO_CLOSE_WARROCK = 0x6000
    DO_SERIAL_GSERV = 0x6100
    DO_JOIN_SERV = 0x6200
    DO_KEEPALIVE = 0x6400
    DO_SET_CHANNEL = 0x7001
    DO_USER_LIST = 0x7100
    DO_CHAT = 0x7400
    # Shop
    DO_BITEM_CHANGE = 0x7512
    DO_SBI_CHANGE = 0x7900  # Also controls when items expire
    DO_ITEM_PROCESS = 0x7600
    DO_NCASH_PROCESS = 0x7800
    DO_COUPON = 0x8100  # Id by DarkRaptor

    # Room
    DO_ROOM_LIST = 0x7200
    DO_ROOM_INFO_CHANGE = 0x7210
    ROOM_CREATE = 0x7300
    DO_JOIN_ROOM = 0x7310
    DO_QUICK_JOIN = 0x7320
    DO_GUEST_JOIN = 0x7330
    DO_EXIT_ROOM = 0x7340
    DO_EXPEL_PLAYER = 0x7341
    DO_INVITATION = 0x7350
    DO_GAME_USER_LIST = 0x7500
    DO_GAME_GUEST_LIST = 0x7501

    # Game packets
    DO_GDATA_INFO = 0x7510
    DO_VEHICLE_LEAVE_WORLD = 0x7511  # Named by DarkRaptor. Present in older sources. Maybe it moved
    DO_BOMB_PROCESS = 0x7520
    DO_GAME_PROCESS = 0x7530
    DO_GAME_UPDATE_CLOCK = 0x7540
    DO_GAME_UPDATE_DATA = 0x7541
    DO_GAME_SCORE = 0x7550
    DO_GAME_RESULT = 0x7560
    DO_PROMOTION_OLD = 0x8200

    # Subpackets of DO_GAME_PROCESS
    # Lobby related #
    DO_ROOM_START = 0x1  # ID by DarkRaptor
    DO_ROOM_START_CONFIRM = 0x4  # ID by DarkRaptor
    DO_READY_CLICK = 0x32
    DO_MAP_CLICK = 0x33
    DO_TYPE_CLICK = 0x34
    DO_ROUND_CLICK = 0x35
    DO_KILL_CLICK = 0x37
    DO_TEAM_CLICK = 0x38
    DO_PING_CLICK = 0x3B
    DO_HOLD_CLICK = 0x3A
    DO_VOTE_KICK = 0x3D
    DO_AUTOSTART_CLICK = 0x3E
    # Ingame subpackets
    DO_ROUND_START = 0x5  # ID by darkraptor
    DO_ROUND_END = 0x6    # ID by darkraptor
    DO_ROUND_START_CONFIRM = 0x7  # ID by darkraptor
    DO_BACK_TO_LOBBY = 0x9  # ID by DarkRaptor
    DO_REQUEST_MISSION = 0x192  # ID by darkraptor
    DO_GO = 0x193
    DO_BRANCH_CLICK = 0x64
    DO_HEALING_PLAYER = 0x65
    DO_HEALING_UNIT = 0x66
    DO_DAMAGED_PLAYER = 0x67
    DO_DAMAGED_UNIT = 0x68
    DO_RELOAD_PLAYER = 0x69
    DO_PLAYER_REGEN = 0x96
    DO_UNIT_REGEN = 0x97
    DO_PLAYER_DIE = 0x98
    DO_UNIT_DIE = 0x99
    DO_PLAYER_DENY = 0x9A
    DO_CHANGE_WEAPONS = 0x9B
    DO_ITEM_DROP = 0x190
    DO_ITEM_PICKUP = 0x191
    DO_CRASH_OBJECT = 0x1F4
    DO_CONQUEST_CAMP = 0x9C
    DO_SUICIDE = 0x9D
    DO_FIRE_ARTILLERY = 0x9F
    DO_OBJECT_RIDE = 0xC8
    DO_OBJECT_CHANGE_SEAT = 0xC9
    DO_OBJECT_ALIGHT = 0xCA

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

    # Game packets
    DO_GAME_PROCESS = 0x7530
    DO_GAME_UPDATE_CLOCK = 0x7540
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
    DO_AUTOSTART_CLICK = 0x3E
    # In game subpackets
    DO_BACK_TO_LOBBY = 0x9  # ID by DarkRaptor
    DO_REQUEST_MISSION = 0x192  # ID by darkraptor
    DO_GO = 0x193
    DO_BRANCH_CLICK = 0x64
    DO_HEALING_PLAYER = 0x65
    DO_DAMAGED_PLAYER = 0x67
    DO_DAMAGED_UNIT = 0x68
    DO_RELOAD_PLAYER = 0x69
    DO_PLAYER_REGEN = 0x96
    DO_PLAYER_DIE = 0x98
    DO_CHANGE_WEAPONS = 0x9B
    DO_ITEM_DROP = 0x190
    DO_ITEM_PICKUP = 0x191
    DO_CRASH_OBJECT = 0x1F4
    DO_CONQUEST_CAMP = 0x9C
    DO_SUICIDE = 0x9D
    DO_FIRE_ARTILLERY = 0x9F

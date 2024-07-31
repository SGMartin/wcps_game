class Premium:
    F2P = 0
    BRONZE = 1
    SILVER = 2
    GOLD = 3

class Channel:
    NONE = 0
    CQC = 1
    URBANOPS = 2
    BATTLEGROUP = 3


class ChatChannel:
    NOTICE1 = 1
    NOTICE2 = 2
    LOBBY2CHANNEL = 3
    ROOM2ALL = 4
    ROOM2TEAM = 5
    WHISPER = 6
    LOBBY2ALL = 8 ## missing 7, 9???
    CLAN = 10

class Classes:
    ENGINEER = 0
    MEDIC = 1
    SNIPER = 2
    SOLDIER = 3
    HEAVY = 4

class AdminCommand:
    TEST = 0
    NOTICE = 1
    DISCONNECTUSER = 2
    LIST = 3

class HitboxBone:
    HEADNECK = 1237
    TORSOLIMBS = 1239
    FEETHANDS = 1241
    SNIPERBONE = 1243 # odd bone. AW50F uses it for upper body. PSG, BARRETT too but only in UO...

class DamageMultipliers:
    HEADNECK = 120
    TORSOLIMBS = 60
    FEETHANDS = 30

class DamageTypes:
    INFANTRY = 0
    GROUND = 1
    AIRCRAFT = 2
    SHIP = 3

class DamageDistances:
    SHORT = 0
    MEDIUM = 1
    LONG = 2

class ItemAction:
    BUY = 0x456
    USE = 0x457
    REMOVE = 0x458

class GameMode:
    EXPLOSIVE = 0
    FFA = 1
    TDM = 2
    CONQUEST = 3

class RoomStatus:
    WAITING = 0
    PLAYING = 1

class RoomUpdateType:
    CREATE = 0
    UPDATE = 1
    DELETE = 2

class Team:
    DERBARAN = 0
    NIU = 1
    NONE = 2

class VehicleClass:
    NONE = 0
    GROUND = 1
    AIRCRAFT = 2
    SHIP = 3

class VehicleWeapon:
    MAIN = 0
    SUB = 1
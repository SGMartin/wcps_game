# GAME CONSTANTS
ROUND_LIMITS = [1, 3, 5, 7, 9]
TDM_LIMITS = [30, 50, 100, 150, 200, 300]
MAX_CHANNELS = 3
MAX_CLASSES = 5
MAX_WEAPONS_SLOTS = 8
MAX_ITEMS = 32

EXPTABLE = [
    # 1 - 10
    0, 2250, 6750, 11250, 16650, 24750, 32850, 41625, 50400, 59175,
    # 11 -20
    67950, 76725, 94725, 112725, 130725, 148725, 166725, 189225, 211725, 234225,
    # 21 -30
    256725, 279225, 306225, 333225, 360225, 387225, 414225, 441225, 497475, 553725,
    # 31-40
    609975, 666225, 722475, 778725, 857475, 936225, 1014975, 1093725,  1172475, 1251225,
    # 41-50
    1363725, 1476225, 1588725, 1701225, 1813725, 1926225, 2038725, 2207475,  2376225, 2544975,
    # 51-60
    2713725, 2882475, 3051225, 3219975, 3444975, 3669975, 3894975, 4119975,  4344975, 4569975,
    # 61-70
    4794975, 5132475, 5469975, 5807475, 6144975, 6482475, 6819975, 7157475,  7494975, 7944975,
    # 71-80
    8394975, 8844975, 9294975, 9744975, 10194975, 10644975, 11094975, 11657475, 12219975, 12782475,
    # 81-89
    13344975, 13907475, 14469975, 15032475, 15932475, 17282475, 18632475, 19982475, 21332475,
    # 90
    22682475,
    # 91-99
    24032475, 25382475, 26732475, 28307475, 29882475, 31457475, 33032475, 34607475, 36182475,
    # 100
    37757475
]


def get_exp_for_level(level: int) -> int:
    if level < 0 or level > 101:
        raise Exception("Invalid level value {level}")
    else:
        xp = 0 if level == 0 else EXPTABLE[level - 1]
        return xp


def get_level_for_exp(exp: int) -> int:
    if exp > EXPTABLE[-1]:
        return 100
    else:
        for lvl, required_exp in enumerate(EXPTABLE):
            if exp < required_exp:
                return lvl


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
    # missing 7, 9???
    LOBBY2ALL = 8
    CLAN = 10


class Classes:
    ENGINEER = 0
    MEDIC = 1
    SNIPER = 2
    ASSAULT = 3
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
    # odd bone. AW50F uses it for upper body. PSG, BARRETT too but only in UO...
    SNIPERBONE = 1243


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


# TODO check this against ops.warrock.net somehow
class ClanRank:
    ROOKIE = 0
    SUB = 1
    LIUTENANT = 2
    CHAIRMAN = 3
    MASTER = 4


class ItemType:
    WEAPON = 1
    OTHER = 2


class ResourceItem:  # unused in CP1
    OIL = "A"
    WOOD = "B"
    STONE = "C"
    MINERAL = "D"
    FIBER = "E"


class CharacterItem:  # unused in CP1
    UNIFORM = "A"
    SHIRT = "B"
    PANTS = "C"
    GOGGLE = "D"
    EARRING = "E"
    NECKLACE = "F"
    MASK = "G"
    BRACELET = "H"
    RING = "I"
    SHOES = "J"
    GLOVES = "K"


class PXItem:  # Introduced in late CP1
    SLOT = "A"
    DISPOSABLE = "B"
    TIME = "C"
    EXPSET = "D"
    DINARSET = "E"


class WeaponTypes:
    DAGGER = "A"
    PISTOL = "B"
    RIFLE = "C"
    RIFLE2 = "D"
    RIFLE3 = "E"
    SMG = "F"
    SNIPER = "G"
    MACHINE_GUN = "H"
    SHOTGUN = "I"
    ANTITANK_WEAPON = "J"
    GROUND_TO_AIR_WEAPON = "K"
    ANTITANK_MINE = "L"
    GRENADE = "M"
    GRENADE_COMBATANT = "N"
    EXTRA_AMMO = "O"
    BOMB = "P"
    MEDIC_KIT = "Q"
    SPANNER = "R"
    ALLCLASS_PAID = "S"
    MACHINE_GUN2 = "T"
    ENGINEER_PAID = "U"
    MEDIC_PAID = "V"
    ALLCLASS = "W"
    SCOUT_PAID = "X"
    COMBATANT_PAID = "Y"
    HEAVY_WEAPONS_PAID = "Z"


class EquipmentTypes:
    FIXED_GROUND_TO_GROUND_MISSILE = "A"
    FIXED_GROUND_TO_AIR_MISSILE = "B"
    MOTORCYCLE = "C"
    CAR = "D"
    TANK = "E"
    LIGHT_TANK = "F"
    ARMORED_VEHICLE = "G"
    SELF_PROPELLED_ARTILLERY = "H"
    SELF_PROPELLED_ANTI_AIR_GUN = "I"
    HELICOPTER = "J"
    AIRPLANE = "K"
    NAVAL_TRANSPORT = "L"
    NAVAL_ATTACK = "M"


class EquipmentWeaponTypes:
    SEAT = "A"
    MACHINE_GUN = "B"
    HEAVY_MACHINE_GUN = "C"
    ANTIAIRCRAFT_GUN = "D"
    MINI_GUN = "E"
    TANK_GUN = "F"
    SELF_PROPELLED_ARTILLERY = "G"
    GRENADE_LAUNCHER = "H"
    ANTI_AIRCRAFT_MISSILE = "I"
    GROUND_MISSILE = "J"
    ANTI_SHIP_MISSILE = "K"
    BOMB = "L"


class DefaultWeapon:  # TODO Config this?
    DEFAULTS = [
        "DA02",  # Knuckles
        "DB01",  # COLT45
        "DF01",  # MP5
        "DR01",  # WRENCH 01
        "DQ01",  # Medic kit 1
        "DG05",  # M24
        "DN01",  # Default grenade
        "DC02",  # K2
        "DJ01",  # PZF3
        "DL01"   # Anti tank mines

    ]

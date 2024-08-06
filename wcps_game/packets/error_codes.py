class ServerTimeError:
    FORMAT_C_PRANK = 90010            # Format C Drive?
    CLIENT_VERSION_MISSMATCH = 90020  # Client version is different. Please download the patch
    REINSTALL_WINDOWS_PRANK = 90030   # Reinstalling Windows?


class PlayerAuthorizationError:
    NORMAL_PROCEDURE = 73030             # Please log in using the normal procedure!
    INVALID_PACKET = 90100               # Invalid Packet.
    UNREGISTERED_USER = 90101            # Unregistered User.
    SIX_CHARACTERS_MINIMUM = 90102       # You must type at least 6 characters .
    NICKNAME_TOO_SHORT = 90103           # Nickname should be at least 6 charaters.
    ID_IN_USE_OTHER_SERVER = 90104       # Same ID is being used on the server.
    NOT_ACCESIBLE = 90105                # Server is not accessible.
    TRAINING_SERVER = 90106              # Trainee server is accesible until the rank of a private
    CANNOT_CLAN_WAR = 90112              # You cannot participate in Clan War
    LACK_OF_RESPONSE = 91010             # Connection terminated because of lack of response
    SERVER_FULL = 91020                  # You cannot connect. Server is full.
    INFO_REQUEST_TRAFIC = 91030          # Info request are in traffic.
    ACCOUNT_UPDATE_FAILED = 91040        # Account update has failed.
    BAD_SYNCHRONIZATION = 91050          # User Info synchronization has failed.
    IDIN_USE = 92040                     # That ID is currently being used.
    PREMIUM_ONLY = 98010                 # Available to Premium users only.


class EquipmentError:
    CANNOTBEPLACED = 97010    # Item cannot be placed in this slot
    INVALID_SLOT = 97011      # Can't be equipped at the slot.
    INVALID_BRANCH = 97080    # Item is unsuitable for this branch of the service
    ALREADY_EQUIPPED = 97090  # Item is already equipped


class ItemShopError:
    PREMIUM_ONLY = 98010         # Available to Premium users only.
    GOLD_PREMIUM_ONLY = 98020    # Available to Gold users only.
    SLOT5_FREE_GOLD = 98030      # 5th Slot is free for Gold user.
    INVALID_ITEM = 97010         # Item is no longer valid
    SLOT5_NEEDED = 97012         # You must purchase 5th slot first.
    SLOT5_LOW_TIME = 97015       # Insufficient slot time.
    CANNOT_BE_BOUGHT = 97020     # Item cannot be bought
    NOT_ENOUGH_MONEY = 97040     # Insufficient balance
    LEVEL_UNSUITABLE = 97050     # Your level is unsuitable
    NO_LEVEL_REQUIREMENT = 97060  # You do not meet the level requirements to purchase this weapon.
    INVENTORY_FULL = 97070      # Your inventory is full
    EXCEEDED_LEASE = 97080      # Cannot purchase. You have exceeded maximum lease period.
    CANNOT_BUY_TWICE = 97090    # You cannot purchase the item twice.

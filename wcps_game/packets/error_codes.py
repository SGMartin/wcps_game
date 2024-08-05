class ServerTimeError():
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
    CANNOTBEPLACED = 0x17AF2    # Item cannot be placed in this slot
    INVALID_SLOT = 0x17AF3      # Can't be equipped at the slot.
    INVALID_BRANCH = 0x17B38    # Item is unsuitable for this branch of the service
    ALREADY_EQUIPPED = 0x17B42  # Item is already equipped

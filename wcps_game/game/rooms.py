from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.game_server import User

from wcps_game.game import constants as gconstants


class Room:
    def __init__(
        self,
        master: "User",
        displayname: str,
        password_protected: bool,
        password: str = "",
        max_players: int = 0,
        room_type: int = 0,
        level_limit: int = 0,
        premium_only: bool = False,
        vote_kick: bool = True,
        is_clanwar: bool = False
    ):

        self.id = -1
        self.master = master
        self.master_slot = 0
        self.displayname = displayname
        self.state = gconstants.RoomStatus.WAITING
        self.channel = master.channel
        self.type = room_type  # Unused in CP1
        self.level_limit = level_limit
        self.premium_only = premium_only
        self.vote_kick = vote_kick
        self.is_clanwar = is_clanwar

        self.password_protected = password_protected

        if password_protected:
            self.password = password
        else:
            self.password = None

        if self.master.inventory.has_item("CC02"):
            self.supermaster = True
        else:
            self.supermaster = False

        self.max_players = gconstants.RoomMaximumPlayers.MAXIMUM_PLAYERS[self.channel][max_players]

        default_modes = {
            gconstants.ChannelType.CQC: gconstants.GameMode.EXPLOSIVE,
            gconstants.ChannelType.URBANOPS: gconstants.GameMode.TDM,
            gconstants.ChannelType.BATTLEGROUP: gconstants.GameMode.TDM
        }

        self.game_mode = default_modes[self.channel]
        self.ping_limit = gconstants.RoomPingLimit.GREEN

        # These are just default values
        self.rounds_setting = 3
        self.tickets_setting = 3
        self.rounds = gconstants.ROUND_LIMITS[self.rounds_setting]
        self.tdm_tickets = gconstants.TDM_LIMITS[self.tickets_setting]

        self.autostart = False

    def authorize(self, room_id: int):
        self.id = room_id

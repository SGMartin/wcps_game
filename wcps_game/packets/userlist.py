from wcps_core.packets import OutPacket

from wcps_game.packets.packet_list import ClientXorKeys, PacketList


class UserList(OutPacket):
    static_user_list = [
        [6, 7, "Jastro", -1, -1, -1, -1, 18202728, 1],
        [4, 8, "DarkRaptor", 2, "PUEBLO", 5, 0, 2821928, 3],
        [5, 9, "PJ1712", -1, -1, -1, -1, 1, 2],
        [12, 18, "Sinso", 1, "MAFIA", 2, 0, 1363725, 2],
        [13, 26, "CrS-", 1, "MAFIA", 4, 0, 2363725, 2],
        [13, 26, "MoonKai", 1, "NAVAJA", 4, 0, 10194975, 2]

    ]

    def __init__(self, lobby_user_list: list, target_page: int):
        super().__init__(packet_id=PacketList.USERLIST, xor_key=ClientXorKeys.SEND)

        # User list count. Technically I managed to get to 302 with slider = 1
        # but sometime it crashes going back. 250 ALWAYS work
        self.append(len(lobby_user_list))
        self.append(target_page)  # user list page

        # Discovered by SGMartin. The user list is a slider. The higher the value,
        # the lower the userlist rotates. Max. to 10 and the user list stays in place
        slider = 1

        for idx, this_user in enumerate(lobby_user_list):
            self.append(idx + target_page * slider)
            self.append(this_user.session_id)  # used to be internal id
            self.append(this_user.session_id)  # session id
            self.append(this_user.displayname)  # displayname
            self.append(-1)  # clan id
            self.append(-1)  # clan name
            self.append(-1)  # clan rank or icon id?
            self.append(-1)  # Clan master = 5. Rank?
            self.append(0)  # unknown
            self.append(16)  # unknown
            self.append(this_user.xp)  # xp
            self.append(this_user.premium)  # premium
            self.append(this_user.channel)  # channel ?

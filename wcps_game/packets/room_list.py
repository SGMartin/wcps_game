from wcps_core.packets import OutPacket

from wcps_game.packets.packet_list import PacketList, ClientXorKeys


class RoomList(OutPacket):
    def __init__(self, room_page: int, room_list: list):
        super().__init__(
            packet_id=PacketList.ROOMLIST,
            xor_key=ClientXorKeys.SEND
        )

        self.append(len(room_list))  # The total room list for this page
        self.append(room_page)
        self.append(0)  # ?
        for idx, room in enumerate(room_list):
            self.append(idx)  # TODO: use the actual id
            self.append(1)
            self.append(room.state)
            self.append(room.master)
            self.append(room.displayname)
            self.append(room.has_password)
            self.append(room.maximum_players)
            self.append(room.player_count)
            self.append(room.map)
            self.append(1)
            self.append(0)
            self.append(0)
            self.append(room.mode)
            self.append(1)  # Always 4 even in CP3
            self.append(room.joinable)
            self.append(1)  # Always 0 even in CP3
            self.append(room.supermaster)
            self.append(0)
            self.append(room.level_limit)
            self.append(room.premium)
            self.append(room.enable_kick)
            self.append(room.autostart)
            self.append(0)
            self.append(room.pinglimit)
            self.append(-1)

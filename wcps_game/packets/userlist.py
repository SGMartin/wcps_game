from wcps_core.packets import OutPacket

from wcps_game.packets.packet_list import ClientXorKeys, PacketList

# The client keeps one page of the lobby user list: 10 entries. Its reader writes each entry to row
# 'index - page * 10' with no bounds check, so a packet must only carry the users of that page.
USER_LIST_PAGE_SIZE = 10


def last_user_list_page(user_count: int) -> int:
    return max(0, (user_count - 1) // USER_LIST_PAGE_SIZE)


class UserList(OutPacket):
    def __init__(self, lobby_user_list: list, target_page: int):
        """One page of the lobby user list: the users of target_page among lobby_user_list (the whole
        channel). An empty page sends count 0: the client then keeps the list and page it shows."""
        super().__init__(packet_id=PacketList.DO_USER_LIST, xor_key=ClientXorKeys.SEND)

        first = target_page * USER_LIST_PAGE_SIZE
        page_users = lobby_user_list[first:first + USER_LIST_PAGE_SIZE]

        self.append(len(page_users))  # entries in this packet (the client returns at once if <= 0)
        self.append(target_page)  # the client stores it as its current page

        for row, this_user in enumerate(page_users):
            self.append(first + row)  # the client puts it in row 'index - page * 10' = row
            self.append(this_user.session_id)  # used to be internal id
            self.append(this_user.session_id)  # session id
            self.append(this_user.displayname)  # displayname
            self.append(-1)  # clan id
            self.append(-1)  # clan name (read as a string here)
            self.append(-1)  # clan rank or icon id?
            self.append(-1)  # Clan master = 5. Rank?
            self.append(0)  # short, same field as in 0x7500; no client reader found
            self.append(16)  # short, same field as in 0x7500; no client reader found
            self.append(this_user.xp)  # xp
            self.append(this_user.premium)  # premium
            self.append(this_user.channel)  # same field as the 0x7500 icon flag; not read in the lobby

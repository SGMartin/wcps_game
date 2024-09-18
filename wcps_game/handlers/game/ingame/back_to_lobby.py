from wcps_game.game.constants import RoomStatus, RoomUpdateType
from wcps_game.handlers.packet_handler import GameProcessHandler

from wcps_game.packets.packet_factory import PacketFactory
from wcps_game.packets.packet_list import PacketList


class BackToLobbyHandler(GameProcessHandler):
    async def handle(self):
        if self.room.state == RoomStatus.WAITING:

            if self.player.state != RoomStatus.WAITING:
                self.player.state = RoomStatus.WAITING

                self.answer = True
                self.self_target = True

                room_players = self.room.get_all_players()

                all_done = True

                for player in room_players:
                    if player.state != RoomStatus.WAITING:
                        all_done = False

                # Once all players are done, send an update to the lobby
                if all_done:
                    channel_users = await self.room.channel.get_users()

                    for chuser in channel_users:
                        if chuser.room_page == self.room.room_page and chuser.room is None:
                            room_update = PacketFactory.create_packet(
                                packet_id=PacketList.DO_ROOM_INFO_CHANGE,
                                room_to_update=self.room,
                                update_type=RoomUpdateType.UPDATE
                            )
                            await chuser.send(room_update.build())

                if self.player.user.room is None:
                    self.player.user.set_room(None, 0)

                    user_list = PacketFactory.create_packet(
                        packet_id=PacketList.DO_USER_LIST,
                        lobby_user_list=channel_users,
                        target_page=self.player.user.userlist_page
                    )
                    await self.player.user.send(user_list.build())

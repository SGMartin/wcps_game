import abc
import asyncio
import logging

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.game_server import User

from wcps_core.packets import InPacket
from wcps_core.constants import ErrorCodes as corerr

from wcps_game.entities.network_entities import NetworkEntity
from wcps_game.game.constants import RoomUpdateType
from wcps_game.packets.packet_factory import PacketFactory
from wcps_game.packets.packet_list import PacketList


class PacketHandler(abc.ABC):
    def __init__(self):
        self.in_packet = None

    async def handle(self, packet_to_handle: InPacket) -> None:
        self.in_packet = packet_to_handle
        receptor = packet_to_handle.receptor

        if isinstance(receptor, NetworkEntity):
            await self.process(receptor)
        else:
            logging.error("No receptor for this packet!")

    @abc.abstractmethod
    async def process(self, user_or_server):
        pass

    def get_block(self, block_id: int) -> str:
        return self.in_packet.blocks[block_id]


class GameProcessHandler(abc.ABC):
    def __init__(self):

        self.packet = None
        self.error_code = 1
        self.lock = asyncio.Lock()

        # The subpacket ID as defined in the packet_list.py i.e. DO_READY_CLICK
        self.sub_packet = None
        # The player that the packet is aimed at
        self.player = None
        # Unused?
        self.room_slot = 0
        # Should we resend the packet?
        self.answer = False
        # Should we update the lobby
        self.update_lobby = False
        # If the user that triggered the packet also the target?
        self.self_target = False
        # Are we sending map data
        self.map_data = False
        # The full packet
        self.blocks = []

    @abc.abstractmethod
    async def handle(self):
        pass

    def get_block(self, block_id: int) -> str:
        return self.blocks[block_id]

    async def process(self, user: "User", in_packet: InPacket):
        # Basically we copy the full packet minus the first two blocks of ticks
        self.blocks = in_packet.blocks
        # bytearray(b'30398946 30000 0 1 2 53 1 0 4 0 0 0 0 0 0 0 \n')
        # TODO: Check if it's defined in the packet_list?
        if self.blocks[3].isdigit():
            self.sub_packet = int(self.blocks[3])
            self.packet = in_packet

            async with self.lock:
                # Get rid of the first bytes of the block since we are not touching them
                self.blocks = self.blocks[4:]
                self.room = user.room

                # Get the player instance of the user for the room
                self.player = user.room.players[user.room_slot]

                if self.player is None:
                    logging.error(
                        f"Could not find player slot for {user.room_slot} at {self.room.id}"
                    )
                    return
                else:
                    self.room_slot = self.player.id

                    await self.handle()

                    if self.answer:
                        if self.error_code == corerr.SUCCESS:
                            new_packet = []
                            new_packet.append(self.error_code)
                            new_packet.append(self.room_slot)
                            new_packet.append(self.room.id)
                            new_packet.append(
                                in_packet.blocks[2]
                            )  # 2 or 0 is the value
                            new_packet.append(self.sub_packet)

                            # Copy the rest of the packet as modified by the handlers
                            new_packet.extend(self.blocks)
                        else:
                            new_packet = [self.error_code]

                        # Build the actual packet
                        game_data_packet = PacketFactory.create_packet(
                            packet_id=PacketList.DO_GAME_PROCESS, blocks=new_packet
                        )
                        print(f"Final packet {game_data_packet.blocks}")
                        if self.error_code > corerr.SUCCESS or self.self_target:
                            await user.send(game_data_packet.build())
                        else:
                            await self.room.send(game_data_packet.build())

                        if self.map_data:
                            logging.info("Implement map data packet here")

                        if self.update_lobby:
                            channel_users = await user.this_server.channels[
                                user.channel
                            ].get_users()

                            room_update = PacketFactory.create_packet(
                                packet_id=PacketList.DO_ROOM_INFO_CHANGE,
                                room_to_update=self.room,
                                update_type=RoomUpdateType.UPDATE,
                            )
                            for chuser in channel_users:
                                if (
                                    chuser.room is None
                                    and chuser.room_page == self.room.room_page
                                ):
                                    await chuser.send(room_update.build())
        else:
            logging.error(f"Unknown subpacket format {self.blocks[3]}, {self.blocks}")

import logging

from wcps_game.handlers.packet_handler import GameProcessHandler
from wcps_game.packets.packet_list import PacketList

from wcps_game.handlers.game.change_map import ChangeMapHandler
from wcps_game.handlers.game.change_mode import ChangeGameModeHandler
from wcps_game.handlers.game.change_rounds_tickets import ChangeRoundsHandler
from wcps_game.handlers.game.change_kills_tickets import ChangeKillsTicketsHandler
from wcps_game.handlers.game.change_ping_limit import ChangePingLimitHandler
from wcps_game.handlers.game.toggle_autostart import ToggleAutoStartHandler
from wcps_game.handlers.game.toggle_user_limit import ToggleUserLimitHandler
from wcps_game.handlers.game.toggle_ready import ToggleReadyHandler
from wcps_game.handlers.game.change_side import ChangeSideHandler
from wcps_game.handlers.game.start import StartRoomHandler
from wcps_game.handlers.game.ingame.game_setup import GameSetupHandler
from wcps_game.handlers.game.ingame.branch_select import BranchSelectHandler
from wcps_game.handlers.game.ingame.spawn import SpawnHandler
from wcps_game.handlers.game.ingame.player_damage import PlayerDamageHandler
from wcps_game.handlers.game.ingame.object_damage import ObjectDamageHandler
from wcps_game.handlers.game.ingame.switch_weapon import SwitchWeaponHandler
from wcps_game.handlers.game.ingame.back_to_lobby import BackToLobbyHandler
from wcps_game.handlers.game.ingame.heal import HealPlayerHandler
from wcps_game.handlers.game.ingame.ammo_recharge import AmmoRechargeHandler
from wcps_game.handlers.game.ingame.place_items_on_ground import PlaceGroundItemHandler
from wcps_game.handlers.game.ingame.use_items_on_ground import UseGroundItemHandler
from wcps_game.handlers.game.ingame.collision_damage import CollisionDamageHandler
from wcps_game.handlers.game.ingame.capture_flag import CaptureFlagHandler
from wcps_game.handlers.game.ingame.artillery import CallArtilleryHandler
from wcps_game.handlers.game.ingame.vehicle_join import JoinVehicleHandler
from wcps_game.handlers.game.ingame.vehicle_leave import LeaveVehicleHandler
from wcps_game.handlers.game.ingame.vehicle_switch_seat import SwitchVehicleSeatHandler
from wcps_game.handlers.game.ingame.suicide import SuicideHandler
from wcps_game.handlers.game.ingame.player_death import PlayerDeathHandler

# from wcps_game.handlers.game.ingame.test import TestHandler

# Dictionary to map packet IDs to handler classes
HANDLER_MAP = {
    # Lobby subpackets
    PacketList.DO_MAP_CLICK: ChangeMapHandler,
    PacketList.DO_TYPE_CLICK: ChangeGameModeHandler,
    PacketList.DO_ROUND_CLICK: ChangeRoundsHandler,
    PacketList.DO_KILL_CLICK: ChangeKillsTicketsHandler,
    PacketList.DO_PING_CLICK: ChangePingLimitHandler,
    PacketList.DO_AUTOSTART_CLICK: ToggleAutoStartHandler,
    PacketList.DO_HOLD_CLICK: ToggleUserLimitHandler,
    PacketList.DO_READY_CLICK: ToggleReadyHandler,
    PacketList.DO_TEAM_CLICK: ChangeSideHandler,
    PacketList.DO_ROOM_START: StartRoomHandler,

    # Ingame subpackets
    PacketList.DO_REQUEST_MISSION: GameSetupHandler,
    PacketList.DO_BRANCH_CLICK: BranchSelectHandler,
    PacketList.DO_PLAYER_REGEN: SpawnHandler,
    PacketList.DO_DAMAGED_PLAYER: PlayerDamageHandler,
    PacketList.DO_DAMAGED_UNIT: ObjectDamageHandler,
    PacketList.DO_HEALING_PLAYER: HealPlayerHandler,
    PacketList.DO_CHANGE_WEAPONS: SwitchWeaponHandler,
    PacketList.DO_BACK_TO_LOBBY: BackToLobbyHandler,
    PacketList.DO_RELOAD_PLAYER: AmmoRechargeHandler,
    PacketList.DO_ITEM_DROP: PlaceGroundItemHandler,
    PacketList.DO_ITEM_PICKUP: UseGroundItemHandler,
    PacketList.DO_CRASH_OBJECT: CollisionDamageHandler,
    PacketList.DO_CONQUEST_CAMP: CaptureFlagHandler,
    PacketList.DO_FIRE_ARTILLERY: CallArtilleryHandler,
    PacketList.DO_OBJECT_RIDE: JoinVehicleHandler,
    PacketList.DO_OBJECT_ALIGHT: LeaveVehicleHandler,
    PacketList.DO_OBJECT_CHANGE_SEAT: SwitchVehicleSeatHandler,
    PacketList.DO_SUICIDE: SuicideHandler,
    PacketList.DO_PLAYER_DIE: PlayerDeathHandler

}


def get_subhandler_for_packet(subpacket_id: int) -> GameProcessHandler:
    handler_class = HANDLER_MAP.get(subpacket_id)
    if handler_class:
        return handler_class()
    else:
        logging.info(f"Unknown subpacket: {subpacket_id}")
        # print("RETURNING TEST AUTOANSWER PACKET")
        # return TestHandler()

import time

from wcps_game.config import settings
from wcps_game.handlers.packet_handler import GameProcessHandler
from wcps_game.game.constants import Classes, ChannelType, RoomStatus


class ArtilleryPhase:
    REQUEST = 0  # ext = 1, f0..f2 target
    END = 1  # end / cancel
    SHELL = 2  # f0..f2 impact, f3..f5 origin, sent three times ~11 s after the request


class ArtilleryReject:
    IN_USE = 1  # "Artillery in use."
    RELOADING = 2  # "Reloading 105MM Cannon."


class CallArtilleryHandler(GameProcessHandler):
    """DO_FIRE_ARTILLERY 0x9f. The server keeps one strike per team: a request
    is accepted (p1 = 1) or rejected to the requester only (p1 = 0, p2 = in use / reloading). The end and
    the shells are only checked against that active strike: a sniper who dies or changes class during the
    ~11 s wait no longer loses the shells (and the incoming-fire marker no longer stays on)."""

    async def handle(self):
        if not self.player.user.authorized:
            return

        if self.room.state != RoomStatus.PLAYING:
            return

        if self.room.channel.type != ChannelType.BATTLEGROUP:
            return

        phase = int(self.get_block(2))  # p0
        now = time.time()
        strike = self.room.artillery.setdefault(
            self.player.team, {"owner": None, "active_until": 0.0, "cooldown_until": 0.0}
        )

        # A strike the client never ended
        if strike["owner"] is not None and now >= strike["active_until"]:
            strike["owner"] = None
            strike["cooldown_until"] = strike["active_until"] + settings().artillery_cooldown

        if phase == ArtilleryPhase.REQUEST:
            # A request a legit client cannot send (dead, not a sniper, no binoculars): no answer
            if (
                not self.player.alive
                or self.player.branch != Classes.SNIPER
                or not self.player.user.inventory.has_item("DX01")  # binoculars
            ):
                return
            if strike["owner"] is not None:
                return self.reject(ArtilleryReject.IN_USE)
            if now < strike["cooldown_until"]:
                return self.reject(ArtilleryReject.RELOADING)

            strike["owner"] = self.player
            strike["active_until"] = now + settings().artillery_active_time
            self.set_block(3, 1)  # p1: accepted ("Set target.")
            self.set_block(4, 0)
            self.answer = True
            return

        # End and shells: only from the player who holds this team's strike
        if strike["owner"] is not self.player:
            return

        if phase == ArtilleryPhase.END:
            strike["owner"] = None
            strike["cooldown_until"] = now + settings().artillery_cooldown
            self.answer = True
        elif phase == ArtilleryPhase.SHELL:
            self.answer = True

    def reject(self, reason: int):
        """Answer the requester only, so its artillery state leaves "requesting"."""
        self.set_block(3, 0)  # p1: rejected
        self.set_block(4, reason)  # p2
        self.self_target = True
        self.answer = True

import asyncio

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.player import Player


class GroundItem():
    def __init__(self, owner: "Player", code: str):
        self.id = None
        self.owner = owner
        self.code = code
        self.used = False
        self._lock = asyncio.Lock()

    async def place(self, room_id: int):
        self.id = room_id

    async def activate(self):
        async with self._lock:
            if not self.used:
                self.used = True
                return True  # Indicating successful activation
            return False  # Already activated

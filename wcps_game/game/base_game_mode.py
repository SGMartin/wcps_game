from abc import ABC, abstractmethod


class BaseGameMode(ABC):
    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name
        self.room = None
        self.initialized = False
        self.freeze_tick = False

    def initialize(self, room):
        self.room = room

    @abstractmethod
    def is_goal_reached(self) -> bool:
        pass

    @abstractmethod
    def winner(self):
        pass

    @abstractmethod
    def process(self):
        pass

    @abstractmethod
    def current_round_derbaran(self) -> int:
        pass

    @abstractmethod
    def current_round_niu(self) -> int:
        pass

    @abstractmethod
    def scoreboard_derbaran(self) -> int:
        pass

    @abstractmethod
    def scoreboard_niu(self) -> int:
        pass

    @abstractmethod
    def on_death(self, killer, target):
        pass

    def get_spawn_id(self) -> int:
        return 0

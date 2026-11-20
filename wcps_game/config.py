from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    # Database
    database_ip: str = "127.0.0.1"
    database_name: str = "game_test"
    database_user: str = "root"
    database_password: str = "root"
    database_port: int = 3306

    # Networking
    server_name: str = "WCPS"
    server_ip: str = "127.0.0.1"
    authentication_server_ip: str = "127.0.0.1"
    authentication_id: int = 0

    # Maximum players allowed in the server. 3600 is the hardcoded client max. value.
    maximum_players: int = 3600
    # Experimental, do not touch unless you really know what you are dealing with
    # ENTIRE = 0 ADULT = 1 CLAN = 2 EMPTY = 3 TEST = 4 DEVELOPMENT = 5 NONE = 6 TRAINEE = 21
    server_type: int = 0
    # Duration, in seconds, of explosive round and bombs
    explosive_round_time: int = 180
    explosive_bomb_time: int = 45
    # Default game time limit for TDM, FFA etc.
    game_time_limit: int = 3600
    # Time to wait until unused vehicles are killed and reset
    unused_vehicle_time: int = 600
    # Artillery (BG): one strike per team at a time (not one per map). Reload time after a strike ends
    # ("Reloading 105MM Cannon."): 30 s, as the game had it. artillery_active_time only frees a strike
    # whose end the client never sends
    artillery_active_time: int = 30
    # Seconds a back-to-room request (subpacket 9) waits for that player's DO_REQUEST_MISSION (#63)
    back_to_lobby_wait: int = 20
    artillery_cooldown: int = 30

    # Global multipliers for money and xp
    global_xp_rate: int = 1
    global_money_rate: int = 1

    class Config:
        env_file = ".env"


settings = Settings

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

    class Config:
        env_file = ".env"


settings = Settings

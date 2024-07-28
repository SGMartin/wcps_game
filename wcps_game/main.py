import asyncio
import datetime
import time 

from clients import AuthenticationClient
from game.game_server import GameServer

async def main():
    print("Starting WCPS Game Server...")

    # Get the current date
    now = datetime.datetime.now()
    start_time = now.strftime("%d/%m/%Y")
    
    ##TODO: config loading here for GameServer
    game_server = GameServer()
    
    print("Connecting to authentication server")
    auth_client = AuthenticationClient(game_server)
    asyncio.create_task(auth_client.run())


    keep_running = True


    while keep_running:
        print("running")
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())

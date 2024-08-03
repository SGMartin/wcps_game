import asyncio
import datetime
import logging
import sys

from wcps_game.database import run_pool
from wcps_game.game.game_server import GameServer
from wcps_game.networking import start_udp_listeners, start_tcp_listeners, AuthenticationClient

# ASCII LOGO
WCPS_IMAGE = r"""

____    __    ____  ______ .______     _______.   
\   \  /  \  /   / /      ||   _  \   /       |   
 \   \/    \/   / |  ,----'|  |_)  | |   (----`   
  \            /  |  |     |   ___/   \   \       
   \    /\    /   |  `----.|  |   .----)   |      
    \__/  \__/     \______|| _|   |_______/       
                            by SGMartin      
"""
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


async def status_reporter(game_server):
    while True:
        if game_server:
            logging.info(f"Connected players: {game_server.get_player_count()}")
            logging.info(f"Active rooms: {game_server.current_rooms}")
        else:
            logging.warning("Game server is not initialized.")

        await asyncio.sleep(60)  # Report every 60 seconds


async def task_monitor():
    while True:
        for task in asyncio.all_tasks():
            if task.done():
                logging.info(f"Task {task.get_name()} has finished.")
            elif task.cancelled():
                logging.warning(f"Task {task.get_name()} was cancelled.")       
        await asyncio.sleep(30)  # Monitor tasks every 30 seconds


async def main():

    print(WCPS_IMAGE)
    logging.info("Starting WCPS Game Server...")

    # Start the database
    await run_pool()
    # Start UDP listeners and handle binding failures
    logging.info("Starting UDP listeners...")
    asyncio.create_task(start_udp_listeners())

    # Attempt to connect to authentication server
    authentication_client = AuthenticationClient("127.0.0.1", 5012)

    try:
        connection_reader, connection_writer = await authentication_client.connect()
        game_server = GameServer(connection_reader, connection_writer)
    except Exception as e:
        logging.error(f"Failed to start the game server: {e}")
        sys.exit(1)

    # Start TCP servers
    asyncio.create_task(start_tcp_listeners(this_server=game_server))

    # Get the current date
    now = datetime.datetime.now()
    start_time = now.strftime("%d/%m/%Y")
    logging.info(f"Game server successfully started on {start_time}")

    try:
        while True:
            logging.info("Server is running. Awaiting connections...")
            await asyncio.sleep(5)  # Adjust sleep duration as needed

    except KeyboardInterrupt:
        logging.info("Shutting down server...")
    except Exception as e:
        logging.error(f"Unexpected error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
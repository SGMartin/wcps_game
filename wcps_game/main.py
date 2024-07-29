import asyncio
import datetime
import logging

from clients import AuthenticationClient, start_listeners
from game.game_server import GameServer

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
            logging.info(f"Connected players: {game_server.current_players}")
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

    # Get the current date
    now = datetime.datetime.now()
    start_time = now.strftime("%d/%m/%Y")
    logging.info(f"Server started on {start_time}")

    # Initialize and configure GameServer
    game_server = GameServer()

    logging.info("Connecting to authentication server")
    auth_client = AuthenticationClient(game_server)

    # Start tasks for authentication client and pinging
    asyncio.create_task(auth_client.run())
    asyncio.create_task(auth_client.ping_authentication_server())

    # Start tasks for status reporting and task monitoring
    asyncio.create_task(status_reporter(game_server))
    asyncio.create_task(task_monitor())

    # Start TCP listener
    asyncio.create_task(start_listeners(game_server))
    
    try:
        while True:
            logging.info("Server is running. Awaiting connections...")
            await asyncio.sleep(10)  # Adjust sleep duration as needed
    except KeyboardInterrupt:
        logging.info("Shutting down server...")
    except Exception as e:
        logging.error(f"Unexpected error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
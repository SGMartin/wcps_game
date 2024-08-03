import asyncio
import datetime
import logging

from wcps_core.constants import Ports

from wcps_game.game.game_server import GameServer, User
from wcps_game.networking import UDPListener

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

    # # Initialize and configure GameServer
    # game_server = GameServer()

    # logging.info("Connecting to authentication server")
    # auth_client = AuthenticationClient(game_server)

    # # Start tasks for authentication client and pinging
    # asyncio.create_task(auth_client.run())
    # asyncio.create_task(auth_client.ping_authentication_server())

    # # Start tasks for status reporting and task monitoring
    # asyncio.create_task(status_reporter(game_server))
    # asyncio.create_task(task_monitor())

    # # Start TCP listener
    # asyncio.create_task(start_listeners(game_server, auth_client))

    # # ## Start UDP listeners
    # udp_listener_1 = UDPListener(wcps_core.constants.Ports.UDP1)
    # udp_listener_2 = UDPListener(wcps_core.constants.Ports.UDP2)

    # await asyncio.gather(
    #     udp_listener_1.start(),
    #     udp_listener_2.start()
    # )

    # Start UDP listeners on both ports
    udp_listener_1 = UDPListener(Ports.UDP1)
    udp_listener_2 = UDPListener(Ports.UDP2)

    await asyncio.gather(
        udp_listener_1.start(),
        udp_listener_2.start()
    )

    # Initialize an configure Game Server
    this_server = GameServer()

    # Attempt to connect to authentication server
    await this_server.start()

    # TODO: check if we are connected?

    # Initialize the TCP server
    await asyncio.start_server(User, this_server.ip, this_server.port)

    # Get the current date
    now = datetime.datetime.now()
    start_time = now.strftime("%d/%m/%Y")
    logging.info(f"Game server successfully started on {start_time}")

    try:
        while True:
            logging.info("Server is running. Awaiting connections...")
            # ## test
            # from packets.server import Ping           
            # for u in game_server.online_users.values():
            #     await u.send(Ping(1,u).build())
            await asyncio.sleep(5)  # Adjust sleep duration as needed

    except KeyboardInterrupt:
        logging.info("Shutting down server...")
    except Exception as e:
        logging.error(f"Unexpected error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())

import asyncio
from wcps_core.constants import Ports

import networking.auth_server

async def start_listeners():
    try:
        auth_server_listener = await asyncio.start_server(
            networking.auth_server.AuthenticationServer, "127.0.0.1", 5013
        )
        print("Authentication listener started.")
    except OSError:
        print(f"Failed to bind to port {Ports.INTERNAL}")
        return

    # Create tasks to run the servers in the background
    auth_server_listener_task = asyncio.create_task(auth_server_listener.serve_forever())

    # Wait for the tasks to complete
    await asyncio.gather(auth_server_listener_task)

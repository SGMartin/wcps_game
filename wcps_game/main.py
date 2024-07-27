import asyncio
import datetime
import time 

from networking import start_listeners
from networking.auth_server import AuthenticationClient

async def main():
    # Get the current date
    now = datetime.datetime.now()
    start_time = now.strftime("%d/%m/%Y")
    keep_running = True

    print(f"Game Server started at {now}")

    print("Initializing database pool...")
    print("TODO!")


    print("Attempt to connect to auth")
    client = AuthenticationClient('127.0.0.1', 5012)
    await client.run("")
    # print("Launching background listeners")
    # # Start the asyncio listeners
    # asyncio.create_task(start_listeners())


    while keep_running:
        print("Server running")
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())

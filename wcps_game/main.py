import asyncio
import datetime
import time 

from clients import AuthenticationClient

async def main():
    print("Starting WCPS Game Server...")

    # Get the current date
    now = datetime.datetime.now()
    start_time = now.strftime("%d/%m/%Y")
    
    print("Connecting to authentication server")
    auth_client = AuthenticationClient("127.0.0.1", 5012)
    asyncio.create_task(auth_client.run())


    keep_running = True


    while keep_running:
        print("Server running")
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import aiomysql

from wcps_game.config import settings

pool = None


async def create_pool():
    global pool
    pool = await aiomysql.create_pool(
        host=settings().server_ip,
        port=settings().database_port,
        user=settings().database_user,
        password=settings().database_password,
        db=settings().database_name,
        loop=asyncio.get_event_loop(),
    )
    return pool


async def run_pool():
    await create_pool()


async def get_user_details(username: str) -> dict:
    async with pool.acquire() as connection:
        await connection.select_db(settings().database_name)
        async with connection.cursor() as cur:
            query = "SELECT * FROM users WHERE username = %s"
            await cur.execute(query, (username,))
            user_details = await cur.fetchall()
            # By default a tuple is recieved
            if user_details:
                user_details = user_details[0]
                if len(user_details) == 6:
                    this_user = {
                        "id": int(user_details[0]),
                        "xp": int(user_details[2]),
                        "money": int(user_details[3]),
                        "premium": int(user_details[4]),
                        "premium_expiredate": int(user_details[5])
                    }
                    return this_user
                else:
                    # TODO: Improper db format
                    print("Improper database schema")
                    return None
            else:
                return None


async def get_user_stats(username: str) -> dict:
    async with pool.acquire() as connection:
        await connection.select_db(settings().database_name)
        async with connection.cursor() as cur:
            query = "SELECT * FROM user_stats WHERE username = %s"
            await cur.execute(query, (username,))
            user_details = await cur.fetchall()
            # By default a tuple is recieved
            if user_details:
                user_details = user_details[0]
                if len(user_details) == 6:
                    this_user = {
                        "kills": int(user_details[1]),
                        "deaths": int(user_details[2])
                    }
                    return this_user
                else:
                    # TODO: Improper db format
                    print("Improper database schema")
                    return None
            else:
                return None
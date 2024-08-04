import asyncio
import aiomysql

from wcps_game.config import settings

pool = None


async def create_pool():
    global pool
    pool = await aiomysql.create_pool(
        host=settings().database_ip,
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


async def get_user_details_and_stats(username: str) -> dict:
    async with pool.acquire() as connection:
        await connection.select_db(settings().database_name)
        async with connection.cursor() as cur:
            query = """
            SELECT 
                u.id, u.xp, u.money, u.premium, u.premium_expiredate,
                s.kills, s.deaths
            FROM 
                users u
            JOIN 
                user_stats s ON u.id = s.id
            WHERE 
                u.username = %s
            """
            await cur.execute(query, (username,))
            user_details = await cur.fetchone()
            if user_details:
                this_user = {
                    "id": int(user_details[0]),
                    "xp": int(user_details[1]),
                    "money": int(user_details[2]),
                    "premium": int(user_details[3]),
                    "premium_expiredate": int(user_details[4]),
                    "kills": int(user_details[5]),
                    "deaths": int(user_details[6])
                }
                return this_user
            else:
                return None


async def get_user_equipment(username: str) -> dict:
    async with pool.acquire()as connection:
        await connection.select_db(settings().database_name)
        async with connection.cursor() as cur:
            query = """
            SELECT 
                l.engineer, l.medic, l.sniper, l.assault, l.heavy_trooper
            FROM
                users u
            JOIN
                user_loadout l ON u.id = l.id
            WHERE
                u.username = %s
            """
            await cur.execute(query, (username, ))
            user_loadout = await cur.fetchone()
            if user_loadout:
                this_loadout = {
                    "engineer": user_loadout[0],
                    "medic": user_loadout[1],
                    "sniper": user_loadout[2],
                    "assault": user_loadout[3],
                    "heavy_trooper": user_loadout[4]
                }
                return this_loadout
            else:
                return None


async def get_user_inventory(username: str) -> dict:
    async with pool.acquire()as connection:
        await connection.select_db(settings().database_name)
        async with connection.cursor() as cur:
            query = """
            SELECT 
                i.id AS inventory_id, i.code AS inventory_code, i.retail, 
                i.startdate, i.leasing_seconds, i.price, i.price_cash
            FROM
                users u
            JOIN
                user_inventory i ON u.id = i.owner
            WHERE
                u.username = %s AND i.expired != 0 AND i.deleted != 0
            """
            await cur.execute(query, (username, ))
            results = await cur.fetchone()
            if results:
                inventory_items = []
                for row in results:
                    inventory_item = {
                        "inventory_id": int(row[5]),
                        "inventory_code": row[6],
                        "retail": bool(row[7]),
                        "startdate": int(row[8]),
                        "leasing_seconds": int(row[9]),
                        "price": int(row[10]),  # TODO: used?
                        "price_cash": int(row[11])  # TODO: used?
                    }
                    inventory_items.append(inventory_item)
                return results
            else:
                return None


async def get_user_inventory_and_equipment(username: str) -> dict:
    async with pool.acquire() as connection:
        await connection.select_db(settings().database_name)
        async with connection.cursor() as cur:
            # Query to fetch user loadout and inventory
            query = """
            SELECT 
                l.engineer, l.medic, l.sniper, l.assault, l.heavy_trooper,
                i.id AS inventory_id, i.code AS inventory_code, i.retail, 
                i.startdate, i.leasing_seconds, i.price, i.price_cash
            FROM
                users u
            JOIN
                user_loadout l ON u.id = l.id
            LEFT JOIN
                user_inventory i ON u.id = i.owner
            WHERE
                u.username = %s AND i.expired = 0 AND i.deleted = 0
            """
            await cur.execute(query, (username,))
            results = await cur.fetchall()
            if results:
                # Process the results
                loadout = {
                    "engineer": results[0][0],
                    "medic": results[0][1],
                    "sniper": results[0][2],
                    "assault": results[0][3],
                    "heavy_trooper": results[0][4]
                }

                inventory_items = []
                for row in results:
                    inventory_item = {
                        "inventory_id": int(row[5]),
                        "inventory_code": row[6],
                        "retail": bool(row[7]),
                        "startdate": int(row[8]),
                        "leasing_seconds": int(row[9]),
                        "price": int(row[10]),  # TODO: used?
                        "price_cash": int(row[11])  # TODO: used?
                    }
                    inventory_items.append(inventory_item)

                return {
                    "loadout": loadout,
                    "inventory": inventory_items
                }
            else:
                return None


async def set_inventory_items_expired(items: list) -> bool:
    async with pool.acquire() as connection:
        await connection.select_db(settings().database_name)
        async with connection.cursor() as cur:
            query = """
            UPDATE user_inventory
            SET expired = 1
            WHERE (id, code) IN (%s)
            """
            item_pairs = ', '.join(['(%s, %s)'] * len(items))
            query = query % item_pairs
            params = [item for item in items for item in (item.database_id, item.item_code)]
            await cur.execute(query, params)
            await connection.commit()
            return cur.rowcount > 0
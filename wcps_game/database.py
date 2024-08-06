import asyncio
import aiomysql
import logging

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


async def update_user_equipment(username: str, target_class: str, new_loadout: str) -> bool:
    valid_branches = {"engineer", "medic", "sniper", "assault", "heavy_trooper"}
    if target_class not in valid_branches:
        raise ValueError(f"Invalid column name: {target_class}")

    async with pool.acquire() as connection:
        await connection.select_db(settings().database_name)
        async with connection.cursor() as cur:
            query = f"""
            UPDATE user_loadout l
            JOIN users u ON u.id = l.id
            SET l.{target_class} = %s
            WHERE u.username = %s
            """
            await cur.execute(query, (new_loadout, username))
            await connection.commit()
            return cur.rowcount > 0  # Returns True if a row was updated, False otherwise


async def add_user_inventory(
    username: str,
    inventory_code: str,
    startdate: int,
    leasing_seconds: int,
    price: int,
    retail: bool = False,
    price_cash: int = 0
) -> bool:
    async with pool.acquire() as connection:
        await connection.select_db(settings().database_name)
        async with connection.cursor() as cur:
            # First, get the user id based on the username
            user_query = """
            SELECT id
            FROM users
            WHERE username = %s
            """
            await cur.execute(user_query, (username,))
            user_result = await cur.fetchone()

            if not user_result:
                return False  # User not found

            user_id = user_result[0]

            # Now, insert the new inventory item
            insert_query = """
            INSERT INTO user_inventory (
                owner, code, retail, startdate, leasing_seconds, price, price_cash, expired, deleted
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, 0, 0)
            """
            await cur.execute(
                insert_query,
                (user_id, inventory_code, retail, startdate, leasing_seconds, price, price_cash)
            )
            await connection.commit()
            return cur.rowcount > 0  # Returns True if a row was inserted, False otherwise


async def extend_leasing_time(username: str, item_code: str, leasing_time: int) -> bool:
    async with pool.acquire() as connection:
        await connection.select_db(settings().database_name)
        async with connection.cursor() as cur:
            # First, get the user id based on the username
            user_query = """
            SELECT id
            FROM users
            WHERE username = %s
            """
            await cur.execute(user_query, (username,))
            user_result = await cur.fetchone()

            if not user_result:
                return False  # User not found

            user_id = user_result[0]

            # Now, select the last row in user_inventory with the given conditions
            select_query = """
            SELECT id, leasing_seconds
            FROM user_inventory
            WHERE owner = %s AND code = %s AND expired = 0 AND deleted = 0
            ORDER BY id DESC
            LIMIT 1
            """
            await cur.execute(select_query, (user_id, item_code))
            inventory_result = await cur.fetchone()

            if not inventory_result:
                return False  # No matching inventory item found

            inventory_id, current_leasing_seconds = inventory_result

            # Update the leasing_seconds by adding the leasing_time
            new_leasing_seconds = current_leasing_seconds + leasing_time
            update_query = """
            UPDATE user_inventory
            SET leasing_seconds = %s
            WHERE id = %s
            """
            await cur.execute(update_query, (new_leasing_seconds, inventory_id))
            await connection.commit()
            return cur.rowcount > 0  # Returns True if a row was updated, False otherwise


async def update_user_money(username: str, new_money: int) -> bool:
    async with pool.acquire() as connection:
        await connection.select_db(settings().database_name)
        async with connection.cursor() as cur:
            # First, get the user id based on the username
            user_query = """
            SELECT id
            FROM users
            WHERE username = %s
            """
            await cur.execute(user_query, (username,))
            user_result = await cur.fetchone()

            if not user_result:
                logging.error(f"User not found for username: {username}")
                return False  # User not found

            user_id = user_result[0]
            logging.info(f"User ID for {username} is {user_id}")

            # Now, update the money field
            update_query = """
            UPDATE users
            SET money = %s
            WHERE id = %s
            """
            await cur.execute(update_query, (new_money, user_id))
            await connection.commit()
            if cur.rowcount > 0:
                return True  # Money updated successfully
            else:
                logging.error(f"Failed to update money for user {username}")
                return False  # No rows updated

    logging.error(f"Function reached an unexpected end for user {username}")
    return False  # Explicit return at the end of the function

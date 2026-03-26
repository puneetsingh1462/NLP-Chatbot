import mysql.connector


def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",   # change this
        database="pandeyji_eatery"
    )


def get_order_status(order_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT status FROM order_tracking WHERE order_id = %s"
    cursor.execute(query, (order_id,))

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    if result:
        return result[0]

    return None


def get_food_item_price(item_name):

    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT price FROM food_items WHERE name = %s"
    cursor.execute(query, (item_name,))

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    if result:
        return float(result[0])

    return None


def get_order_total(order_map):

    total = 0.0

    for item_name, quantity in order_map.items():
        price = get_food_item_price(item_name)

        if price is None:
            raise ValueError(f"Price not found for item: {item_name}")

        total += int(quantity) * price

    return round(total, 2)


def find_matching_food_items(item_name):

    conn = get_db_connection()
    cursor = conn.cursor()

    normalized_name = item_name.strip().lower()

    exact_query = "SELECT name FROM food_items WHERE LOWER(name) = %s"
    cursor.execute(exact_query, (normalized_name,))
    exact_matches = [row[0] for row in cursor.fetchall()]

    if exact_matches:
        cursor.close()
        conn.close()
        return exact_matches

    partial_query = "SELECT name FROM food_items WHERE LOWER(name) LIKE %s ORDER BY name"
    cursor.execute(partial_query, (f"%{normalized_name}%",))
    partial_matches = [row[0] for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    return partial_matches


def get_food_item_details(item_name):

    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT item_id, name, price FROM food_items WHERE name = %s"
    cursor.execute(query, (item_name,))

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    if result:
        return {
            "item_id": result[0],
            "name": result[1],
            "price": float(result[2])
        }

    return None


def create_order_with_items(order_map, status="in progress"):

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Keep tracking-row creation and item inserts in one transaction.
        order_result = cursor.callproc("create_order_entry", [status, 0])
        order_id = int(order_result[1])

        for item_name, quantity in order_map.items():
            cursor.callproc("insert_order_item", [item_name, int(quantity), order_id])

        conn.commit()
        return order_id
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

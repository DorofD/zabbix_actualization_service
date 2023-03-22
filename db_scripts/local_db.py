import sqlite3 as sq


def execute_db_query(query, value_array=0):
    conn = sq.connect('database.db')
    cursor = conn.cursor()
    if not value_array:
        cursor.execute(query)
        result = cursor.fetchall()
    else:
        cursor.executemany(query, value_array)
        result = True
    conn.commit()
    conn.close()
    return result


def create_db():
    query = """
        CREATE TABLE IF NOT EXISTS "tags" (
        "id"	INTEGER,
        "tag"	TEXT UNIQUE,
        "value"	TEXT,
        PRIMARY KEY("id" AUTOINCREMENT)
        );
        """
    execute_db_query(query)

    query = """
        CREATE TABLE IF NOT EXISTS "groups" (
        "id"	INTEGER,
        "group"	TEXT UNIQUE,
        PRIMARY KEY("id" AUTOINCREMENT)
        );
        """
    execute_db_query(query)

    query = """
        CREATE TABLE IF NOT EXISTS "types" (
        "id"	INTEGER,
        "type"	TEXT UNIQUE,
        "group_id"  INTEGER,
        PRIMARY KEY("id" AUTOINCREMENT),
        FOREIGN KEY("group_id") REFERENCES "groups"("id")
        );
        """
    execute_db_query(query)

    query = """
        CREATE TABLE IF NOT EXISTS "shops" (
        "pid"	INTEGER UNIQUE,
        "shop"	TEXT UNIQUE,
        "work_time"	TEXT,
        "off_time"	INTEGER,
        PRIMARY KEY("pid")
        );
    """
    execute_db_query(query)

    query = """
        CREATE TABLE IF NOT EXISTS "hosts" (
        "id"	INTEGER,
        "ip"	TEXT UNIQUE,
        "shop_pid"	INTEGER,
        "type_id"	INTEGER,
        PRIMARY KEY("id" AUTOINCREMENT),
        FOREIGN KEY("shop_pid") REFERENCES "shops"("pid"),
        FOREIGN KEY("type_id") REFERENCES "types"("id")
        );
    """
    execute_db_query(query)

    query = """
        CREATE TABLE IF NOT EXISTS "host_tag" (
        "host_id"	INTEGER,
        "tag_id"	INTEGER,
        FOREIGN KEY("host_id") REFERENCES "hosts"("id"),
        FOREIGN KEY("tag_id") REFERENCES "tags"("id")
        );
    """
    execute_db_query(query)

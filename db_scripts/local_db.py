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
    CREATE TABLE IF NOT EXISTS "templates" (
    "id"	INTEGER,
    "template"	TEXT UNIQUE,
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

    query = """
        CREATE TABLE IF NOT EXISTS "host_template" (
        "host_id"	INTEGER,
        "template_id"	INTEGER,
        FOREIGN KEY("host_id") REFERENCES "hosts"("id"),
        FOREIGN KEY("template_id") REFERENCES "templates"("id")
        );
    """
    execute_db_query(query)

    query = """
        CREATE TABLE IF NOT EXISTS "type_template" (
        "type_id"	INTEGER,
        "template_id"	INTEGER,
        FOREIGN KEY("type_id") REFERENCES "types"("id"),
        FOREIGN KEY("template_id") REFERENCES "templates"("id")
        );
    """
    execute_db_query(query)


def get_groups_from_local_db():
    query = """
        SELECT * FROM groups
            """
    result = execute_db_query(query)
    return result


def get_types_from_local_db():
    query = """
        SELECT * FROM types
            """
    result = execute_db_query(query)
    return result


def get_tags_from_local_db():
    query = """
        SELECT tag, value FROM tags
            """
    result = execute_db_query(query)
    return result


def get_shops_from_local_db(pid=0):
    if not pid:
        query = f"""
            SELECT pid, shop, work_time, off_time FROM shops
                """
    else:
        query = f"""
            SELECT pid, shop, work_time, off_time FROM shops
            WHERE pid = '{pid}'
                """
    result = execute_db_query(query)
    return result


def get_hosts_from_local_db():
    # возвращает список кортежей в формате (10, '172.16.47.193', 'Роутер')
    query = """
        SELECT hosts.shop_pid, hosts.ip, types.type FROM hosts
        INNER JOIN types ON hosts.type_id = types.id
    """
    result = execute_db_query(query)
    return result


def get_hosts_from_local_db_to_import(type_id):
    # возвращает список кортежей в формате (10, 'Екатеринбург 15 (город)', '172.16.47.193', 'Роутер')
    query = f"""
        SELECT hosts.shop_pid, shops.shop, hosts.ip, types.type FROM hosts
        INNER JOIN types ON hosts.type_id = types.id
        INNER JOIN shops ON hosts.shop_pid = shops.pid
        WHERE type_id = '{type_id}'
    """
    result = execute_db_query(query)
    return result


def get_templates_from_local_db():
    query = """
        SELECT id, template FROM templates
    """
    result = execute_db_query(query)
    return result


def get_type_template_notes():
    query = """
        SELECT * FROM type_template
    """
    result = execute_db_query(query)
    return result


def get_type_template_view():
    query = """
        SELECT types.type, templates.template FROM type_template
        INNER JOIN types ON type_template.type_id = types.id
        INNER JOIN templates ON type_template.template_id = templates.id
    """
    result = execute_db_query(query)
    return result


def add_groups_to_local_db(groups_to_add):
    query = f"""
        INSERT INTO groups ('group') VALUES(?);
            """
    execute_db_query(query, groups_to_add)


def add_types_to_local_db(types_to_add):
    query = f"""
        INSERT INTO types ('type', 'group_id') VALUES(?, ?);
            """
    execute_db_query(query, types_to_add)


def add_tags_to_local_db(tags_to_add):
    query = f"""
        INSERT INTO tags ('tag', 'value') VALUES(?, ?);
            """
    execute_db_query(query, tags_to_add)


def add_shops_to_local_db(shops_to_add):
    query = f"""
        INSERT INTO shops ('pid', 'shop', 'work_time', 'off_time') VALUES(?, ?, ?, ?);
            """
    execute_db_query(query, shops_to_add)


def add_hosts_to_local_db(hosts_to_add):
    query = f"""
        INSERT INTO hosts ('ip', 'shop_pid', 'type_id') VALUES(?, ?, ?);
            """
    execute_db_query(query, hosts_to_add)


def add_templates_to_local_db(templates_to_add):
    query = f"""
        INSERT INTO templates ('template') VALUES(?);
            """
    execute_db_query(query, templates_to_add)


def add_type_template_notes(notes_to_add):
    query = f"""
        INSERT INTO type_template ('type_id', 'template_id') VALUES(?, ?);
            """
    execute_db_query(query, notes_to_add)


def update_types_from_local_db(types_to_update):
    for host_type in types_to_update:
        query = f"""
            UPDATE types SET (group_id) = ('{host_type[1]}')
            WHERE type = '{host_type[0]}';
                """
        execute_db_query(query)


def update_tags_from_local_db(tags_to_update):
    for tag in tags_to_update:
        query = f"""
            UPDATE tags SET (value) = ('{tag[1]}')
            WHERE tag = '{tag[0]}';
                """
        execute_db_query(query)


def update_shops_from_local_db(shops_to_update):
    for shop in shops_to_update:
        query = f"""
            UPDATE shops SET (work_time, off_time) = ('{shop[2]}', '{shop[3]}')
            WHERE pid = '{shop[0]}';
                """
        execute_db_query(query)


def update_hosts_from_local_db(hosts_to_update):
    for host in hosts_to_update:
        query = f"""
            UPDATE hosts SET (shop_pid, type_id) = ('{host[1]}', '{host[2]}')
            WHERE ip = '{host[0]}';
                """
        execute_db_query(query)


def delete_hosts_from_local_db(ip_to_delete):
    for ip in ip_to_delete:
        query = f"""
            DELETE FROM hosts
            WHERE ip = '{ip}';
                """
        execute_db_query(query)


def delete_templates_from_local_db(templates_to_delete):
    for template in templates_to_delete:
        query = f"""
            DELETE FROM templates
            WHERE template = '{template}';
                """
        execute_db_query(query)


# create_db()

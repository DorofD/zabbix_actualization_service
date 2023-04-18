import pyodbc
from services.env_vars import get_var


DB_SERVER = get_var('DB_SERVER')
DATABASE = get_var('DATABASE')
DB_USER = get_var('DB_USER')
DB_PASSWORD = get_var('DB_PASSWORD')
DB_DRIVER = get_var('DB_DRIVER')


def get_cursor():
    conn = pyodbc.connect(
        f'DRIVER={DB_DRIVER};SERVER={DB_SERVER};DATABASE={DATABASE};UID={DB_USER};PWD={DB_PASSWORD};Trusted_Connection=no;TrustServerCertificate=Yes')
    return conn.cursor()


def get_hosts_from_ws_db(ip='', types=[]):
    # если не указан ip - возвращает список кортежей в формате (10, '172.16.47.193', 'Роутер')
    # если ip указан - возвращает список кортежей в формате (10, 'Екатеринбург 15 (город)', 'Роутер')
    cursor = get_cursor()
    if type(types) == list and types:
        types = list(map(lambda x: f"TYPE = '{x}'", types))
        types_string = ' or '.join(types)
        query = f""" SELECT Expr1, Expr2, TYPE, IP_ADRESS, HOST, COMMENTS, USER_CHANGE
                FROM dbo.CamInShops_r
                WHERE {types_string};
                """
        cursor.execute(query)
    elif type(types) == str:
        query = f""" SELECT Expr1, Expr2, TYPE, IP_ADRESS, HOST, COMMENTS, USER_CHANGE
                FROM dbo.CamInShops_r;
                """
        cursor.execute(query)
    elif not ip:
        query = f""" SELECT Expr1, IP_ADRESS, TYPE
                FROM dbo.CamInShops_r
                """
        cursor.execute(query)
    else:
        query = f""" SELECT Expr1, Expr2, TYPE, IP_ADRESS
                FROM dbo.CamInShops_r
                WHERE IP_ADRESS = '{ip}';
                """
        cursor.execute(query)

    result = []
    for host in cursor.fetchall():
        result.append(tuple(host))

    return result


def get_shops_from_ws_db():
    # возвращает список кортежей в формате (10, 'Екатеринбург 15 (город)')
    cursor = get_cursor()
    query = f""" SELECT DISTINCT Expr1, Expr2 FROM dbo.CamInShops_r"""
    cursor.execute(query)
    result = list(cursor.fetchall())
    return result


def get_types_from_ws_db():
    # возвращает список кортежей в формате ('WAN остров', )
    cursor = get_cursor()
    query = f""" SELECT DISTINCT type FROM dbo.CamInShops_r"""
    cursor.execute(query)
    result = list(cursor.fetchall())
    return result


def get_routers_from_ws_db():
    # возвращает список кортежей в формате (10, 'Екатеринбург 15 (город)', 'VPN2S')
    cursor = get_cursor()
    query = f""" SELECT DISTINCT Expr1, Expr2, RouterModel FROM dbo.Router_in_Shop"""
    cursor.execute(query)
    result = list(cursor.fetchall())
    return result

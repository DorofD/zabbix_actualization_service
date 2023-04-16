from dotenv import load_dotenv
import os
import pyodbc

project_path = os.path.join(os.path.dirname(__file__))
dotenv_path = str(project_path[0:(project_path.index(
    'zabbix_actualization_service') + 29)]) + '.env'

if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
DB_SERVER = os.environ['DB_SERVER']
DATABASE = os.environ['DATABASE']
DB_USER = os.environ['DB_USER']
DB_PASSWORD = os.environ['DB_PASSWORD']
DB_DRIVER = os.environ['DB_DRIVER']


def get_hosts_from_ws_db(ip='', types=[]):
    # если не указан ip - возвращает список кортежей в формате (10, '172.16.47.193', 'Роутер')
    # если ip указан - возвращает список кортежей в формате (10, 'Екатеринбург 15 (город)', 'Роутер')
    conn = pyodbc.connect(
        f'DRIVER={DB_DRIVER};SERVER={DB_SERVER};DATABASE={DATABASE};UID={DB_USER};PWD={DB_PASSWORD}')
    cursor = conn.cursor()
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
    conn = pyodbc.connect(
        f'DRIVER={DB_DRIVER};SERVER={DB_SERVER};DATABASE={DATABASE};UID={DB_USER};PWD={DB_PASSWORD}')
    cursor = conn.cursor()
    query = f""" SELECT DISTINCT Expr1, Expr2 FROM dbo.CamInShops_r"""
    cursor.execute(query)
    result = list(cursor.fetchall())
    return result


def get_types_from_ws_db():
    # возвращает список кортежей в формате ('WAN остров', )
    conn = pyodbc.connect(
        f'DRIVER={DB_DRIVER};SERVER={DB_SERVER};DATABASE={DATABASE};UID={DB_USER};PWD={DB_PASSWORD}')
    cursor = conn.cursor()
    query = f""" SELECT DISTINCT type FROM dbo.CamInShops_r"""
    cursor.execute(query)
    result = list(cursor.fetchall())
    return result


def get_routers_from_ws_db():
    # возвращает список кортежей в формате (10, 'Екатеринбург 15 (город)', 'VPN2S')
    conn = pyodbc.connect(
        f'DRIVER={DB_DRIVER};SERVER={DB_SERVER};DATABASE={DATABASE};UID={DB_USER};PWD={DB_PASSWORD}')
    cursor = conn.cursor()
    query = f""" SELECT DISTINCT Expr1, Expr2, RouterModel FROM dbo.Router_in_Shop"""
    cursor.execute(query)
    result = list(cursor.fetchall())
    return result

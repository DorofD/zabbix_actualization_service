from dotenv import load_dotenv
import os
import pyodbc

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

DB_SERVER = os.environ['DB_SERVER']
DATABASE = os.environ['DATABASE']
DB_USER = os.environ['DB_USER']
DB_PASSWORD = os.environ['DB_PASSWORD']
DB_DRIVER = os.environ['DB_DRIVER']


def get_hosts_from_ws_db():
    conn = pyodbc.connect(
        f'DRIVER={DB_DRIVER};SERVER={DB_SERVER};DATABASE={DATABASE};UID={DB_USER};PWD={DB_PASSWORD}')
    cursor = conn.cursor()
    query = f""" SELECT Expr1, IP_ADRESS, TYPE
            FROM dbo.CamInShops_r

            """
    cursor.execute(query)

    result = []
    for host in cursor.fetchall():
        result.append(tuple(host))

    return result


def get_shops_from_ws_db():
    conn = pyodbc.connect(
        f'DRIVER={DB_DRIVER};SERVER={DB_SERVER};DATABASE={DATABASE};UID={DB_USER};PWD={DB_PASSWORD}')
    cursor = conn.cursor()
    query = f""" SELECT DISTINCT Expr1, Expr2 FROM dbo.CamInShops_r"""
    cursor.execute(query)
    result = list(cursor.fetchall())
    return result


def get_types_from_ws_db():
    conn = pyodbc.connect(
        f'DRIVER={DB_DRIVER};SERVER={DB_SERVER};DATABASE={DATABASE};UID={DB_USER};PWD={DB_PASSWORD}')
    cursor = conn.cursor()
    query = f""" SELECT DISTINCT type FROM dbo.CamInShops_r"""
    cursor.execute(query)
    result = list(cursor.fetchall())
    return result

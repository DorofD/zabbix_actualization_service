import os
import logging
from dotenv import load_dotenv
import pyodbc


logging.basicConfig(level=logging.INFO,
                    filename="log.txt", filemode="a", format=f'%(asctime)s %(levelname)s: %(message)s')

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

DB_SERVER = os.environ['DB_SERVER']
DATABASE = os.environ['DATABASE']
DB_USER = os.environ['DB_USER']
DB_PASSWORD = os.environ['DB_PASSWORD']
DB_DRIVER = os.environ['DB_DRIVER']
ZABBIX_SERVER = os.environ['ZABBIX_SERVER']
ZABBIX_USER = os.environ['ZABBIX_USER']
ZABBIX_PASSWORD = os.environ['ZABBIX_PASSWORD']


def get_hosts(host_type):
    conn = pyodbc.connect(
        f'DRIVER={DB_DRIVER};SERVER={DB_SERVER};DATABASE={DATABASE};UID={DB_USER};PWD={DB_PASSWORD}')

    cursor = conn.cursor()

    query = f""" SELECT Expr1, Expr2, IP_ADRESS, TYPE
            FROM dbo.CamInShops_r
            WHERE TYPE = '{host_type}' """

    cursor.execute(query)
    result = list(cursor.fetchall())
    return result


host = 'Гл. касса'

a = get_hosts(host)

for i in a:
    print(i)

logging.info('info')
logging.error('error')

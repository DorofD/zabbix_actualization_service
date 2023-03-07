import os
import logging
from dotenv import load_dotenv
import pyodbc
import requests
import ast

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


def get_hosts_from_ws_db(host_type):
    try:
        conn = pyodbc.connect(
            f'DRIVER={DB_DRIVER};SERVER={DB_SERVER};DATABASE={DATABASE};UID={DB_USER};PWD={DB_PASSWORD}')

        cursor = conn.cursor()

        query = f""" SELECT Expr1, Expr2, IP_ADRESS, TYPE
                FROM dbo.CamInShops_r
                WHERE TYPE = '{host_type}' """

        cursor.execute(query)
        result = list(cursor.fetchall())
        return result
    except Exception as exc:
        print(exc)
        return False


def get_zabbix_auth_key():
    try:
        login = {
            "jsonrpc": "2.0",
            "method": "user.login",
            "params": {
                "user": f"{ZABBIX_USER}",
                "password": f"{ZABBIX_PASSWORD}"
            },
            "id": 1
        }

        responce = requests.post(
            # rf'{ZABBIX_SERVER}/api_jsonrpc.php', json=login, headers={'Content-Type': 'application/json-rpc'}) # для Zabbix 5.2
            rf'{ZABBIX_SERVER}/zabbix/api_jsonrpc.php', json=login, headers={'Content-Type': 'application/json-rpc'})  # для Zabbix 5.0
        decode_responce = responce.content.decode('utf-8')
        dict_responce = ast.literal_eval(decode_responce)
        key = dict_responce['result']
        return key

    except Exception as exc:
        print(exc)
        return False


def get_hosts_from_zabbix_server(key, groupid, tag):
    try:
        request = {
            "jsonrpc": "2.0",
            "method": "host.get",
            "params": {
                "tags": [{
                    "tag": tag,
                }],
                "groupids": groupid,
                "selectTags": ["tag", "value"],
                "selectGroups": "extend",
                "output": [
                    "hostid",
                    "host",
                    "name",
                ],
            },
            "auth": key,
            "id": 1
        }
        if not groupid:
            del request["params"]["groupids"]
        if not tag:
            del request["params"]["tags"]

        responce = requests.post(
            # rf'{ZABBIX_SERVER}/api_jsonrpc.php', json=request, headers={'Content-Type': 'application/json-rpc'}) # для Zabbix 5.2
            rf'{ZABBIX_SERVER}/zabbix/api_jsonrpc.php', json=request, headers={'Content-Type': 'application/json-rpc'})  # для Zabbix 5.0
        decode_responce = responce.content.decode('utf-8')
        decode_responce = decode_responce.replace('true', 'True')
        dict_responce = ast.literal_eval(decode_responce)
        result = dict_responce['result']
        return result
    except Exception as exc:
        print(exc)
        return False


host = 'Гл. касса'

# a = get_hosts_from_ws_db(host)

# for i in a:
#     print(i)
key = get_zabbix_auth_key()

hosts = get_hosts_from_zabbix_server(key, 0, 'podro4ilda')
for i in hosts:
    print(i)

logging.info('info')
logging.error('error')

import requests
import ast
import json
import os
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO,
                    filename="log.txt", filemode="w", format=f'%(asctime)s %(levelname)s: %(message)s')

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
            # rf'{ZABBIX_SERVER}/api_jsonrpc.php', json=login, headers={'Content-Type': 'application/json-rpc'})  # для Zabbix 5.2
            rf'{ZABBIX_SERVER}/zabbix/api_jsonrpc.php', json=login, headers={'Content-Type': 'application/json-rpc'})  # для Zabbix 5.0
        decode_responce = responce.content.decode('utf-8')
        dict_responce = ast.literal_eval(decode_responce)
        key = dict_responce['result']
        return key

    except Exception as exc:
        print(exc)
        return False


key = get_zabbix_auth_key()


request = {
    "jsonrpc": "2.0",
    "method": "configuration.export",
    "params": {
        "options": {
            "hosts": [
                "10525"
            ]
        },
        "format": "json"
    },
    "auth": key,
    "id": 1
}


responce = requests.post(
    # rf'{ZABBIX_SERVER}/api_jsonrpc.php', json=request, headers={'Content-Type': 'application/json-rpc'})  # для Zabbix 5.2
    rf'{ZABBIX_SERVER}/zabbix/api_jsonrpc.php', json=request, headers={'Content-Type': 'application/json-rpc'})  # для Zabbix 5.0
decode_responce = responce.content.decode('utf-8')
decode_responce = decode_responce.replace('true', 'True')
# print(decode_responce)
dict_responce = ast.literal_eval(decode_responce)
# print(dict_responce)

if 'error' in dict_responce:
    print('Error:', dict_responce['error'])
elif type(dict_responce['result']) == bool:
    print('Result:', dict_responce['result'])
else:
    for i in dict_responce['result']:
        logging.info(i)
        print(i)

hosts = [
    {'host': '172.16.49.1', 'name': '172.16.49.1', 'tags': [{'tag': 'aboba2228', 'value': ''}], 'groups': [
        {'name': 'Discovered hosts'}], 'interfaces': [{'ip': '172.16.49.1', 'interface_ref': 'if1'}], 'inventory_mode': 'DISABLED'},
    {'host': '172.16.49.2', 'name': '172.16.49.2', 'tags': [{'tag': 'aboba2228', 'value': ''}, {'tag': 'zalupa', 'value': '1488'}], 'groups': [{'name': 'Discovered hosts'}, {'name': 'WAN2'}], 'interfaces': [{'ip':
                                                                                                                                                                                                                '172.16.49.2', 'interface_ref': 'if1'}], 'inventory_mode': 'DISABLED'}
]

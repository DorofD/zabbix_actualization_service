import requests
import ast
import json
import os
from dotenv import load_dotenv

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
            # rf'{ZABBIX_SERVER}/api_jsonrpc.php', json=login, headers={'Content-Type': 'application/json-rpc'}) # для Zabbix 5.2
            rf'{ZABBIX_SERVER}/zabbix/api_jsonrpc.php', json=login, headers={'Content-Type': 'application/json-rpc'})  # для Zabbix 5.0
        decode_responce = responce.content.decode('utf-8')
        dict_responce = ast.literal_eval(decode_responce)
        key = dict_responce['result']
        return key

    except Exception as exc:
        print(exc)
        return False


key = get_zabbix_auth_key()

# request = {
#     "jsonrpc": "2.0",
#     "method": "host.get",
#     "params": {
#         "output": [
#             "hostid",
#             "host",
#             "name"
#         ],
#         "selectInterfaces": [
#             "interfaceid",
#             "ip"
#         ]
#     },
#     "id": 2,
#     "auth": key
# }

host = {"zabbix_export":
        {"version": "5.0",
         "groups": [{"name": "Discovered hosts"}],
         "hosts": [
             {"host": "172.16.49.216",
              "name": "172.16.49.216",
              "groups": [{"name": "Discovered hosts"}],
              "interfaces": [{"ip": "172.16.49.216", "interface_ref": "if1"}],
              "inventory_mode": "DISABLED"}]}}
json_host = json.dumps(host)

# host = '{"zabbix_export":{"version":"5.0","date":"2023-03-07T11:32:46Z","groups":[{"name":"Discovered hosts"}],"hosts":[{"host":"172.16.49.37","name":"172.16.49.37","groups":[{"name":"Discovered hosts"}],"interfaces":[{"ip":"172.16.49.37","interface_ref":"if1"}],"inventory_mode":"DISABLED"}]}}'

request = {
    "jsonrpc": "2.0",
    "method": "configuration.import",
    "params": {
        "format": "json",
        "rules": {"applications": {
            "createMissing": True,
        },
            "discoveryRules": {"createMissing": True, "updateExisting": True},
            "graphs": {"createMissing": True, "updateExisting": True},
            "groups": {"createMissing": True},
            "hosts": {"createMissing": True, "updateExisting": True},
            "images": {"createMissing": True, "updateExisting": True},
            "items": {"createMissing": True, "updateExisting": True},
            "maps": {"createMissing": True, "updateExisting": True},
            "screens": {"createMissing": True, "updateExisting": True},
            "templateLinkage": {"createMissing": True},
            "templates": {"createMissing": True, "updateExisting": True},
            "triggers": {"createMissing": True, "updateExisting": True},
            "valueMaps": {"createMissing": True, "updateExisting": True},
        },
        "source": json_host
    },
    "auth": key,
    "id": 1
}

# request = {
#     "jsonrpc": "2.0",
#     "method": "configuration.export",
#     "params": {
#         "options": {
#             "hosts": [
#                 "10525"
#             ]
#         },
#         "format": "json"
#     },
#     "auth": key,
#     "id": 1
# }
request = {
    "jsonrpc": "2.0",
    "method": "host.get",
    "params": {
        "output": [
            "hostid",
            "host",
            "name",
            "groups"
        ],
        "selectInterfaces": [
            "interfaceid",
            "ip"
        ]
    },
    "id": 2,
    "auth": key
}

request = {
    "jsonrpc": "2.0",
    "method": "hostgroup.get",
    "params": {
        "output": "extend",

    },
    "auth": key,
    "id": 1
}
responce = requests.post(
    # rf'{ZABBIX_SERVER}/api_jsonrpc.php', json=request, headers={'Content-Type': 'application/json-rpc'}) # для Zabbix 5.2
    rf'{ZABBIX_SERVER}/zabbix/api_jsonrpc.php', json=request, headers={'Content-Type': 'application/json-rpc'})  # для Zabbix 5.0
decode_responce = responce.content.decode('utf-8')
decode_responce = decode_responce.replace('true', 'True')
# print(decode_responce)
dict_responce = ast.literal_eval(decode_responce)
# print(dict_responce)

for i in dict_responce['result']:
    print(i)

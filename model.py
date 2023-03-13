import os
import logging
import json
from dotenv import load_dotenv
import pyodbc
import requests
import ast
import sqlite3 as sq
import pandas as pd

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


def send_request_to_zabbix(request):
    try:
        responce = requests.post(
            # rf'{ZABBIX_SERVER}/api_jsonrpc.php', json=request, headers={'Content-Type': 'application/json-rpc'})  # для Zabbix 5.2
            rf'{ZABBIX_SERVER}/zabbix/api_jsonrpc.php', json=request, headers={'Content-Type': 'application/json-rpc'})  # для Zabbix 5.0
        decode_responce = responce.content.decode('utf-8')
        decode_responce = decode_responce.replace('true', 'True')
        decode_responce = decode_responce.replace('false', 'False')
        dict_responce = ast.literal_eval(decode_responce)
        return dict_responce
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

        responce = send_request_to_zabbix(login)
        key = responce['result']
        return key

    except Exception as exc:
        print(exc)
        return False


def get_hosts_from_zabbix(key, groupid, tag):
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

        responce = send_request_to_zabbix(request)
        result = responce['result']
        return result
    except Exception as exc:
        print(exc)
        return False


def get_groups_from_zabbix(key):
    try:
        request = {
            "jsonrpc": "2.0",
            "method": "hostgroup.get",
            "params": {
                "output": "extend"
            },
            "auth": key,
            "id": 1
        }

        responce = send_request_to_zabbix(request)
        result = responce['result']
        return result
    except Exception as exc:
        print(exc)
        return False


def import_hosts_to_zabbix(key, host_list):
    try:

        hosts = {"zabbix_export":
                 # {"version": "5.2",
                 {
                     "version": "5.0",
                     "hosts": host_list}}

        json_hosts = json.dumps(hosts)

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
                "source": json_hosts
            },
            "auth": key,
            "id": 1
        }

        responce = send_request_to_zabbix(request)
        result = {'status': '', 'message': ''}
        if 'result' in responce:
            result['status'] = True
        elif 'error' in responce:
            result['status'] = False
            result['message'] = responce['error']
        else:
            result['status'] = False
            result['message'] = 'Unexpected error'
        return result

    except Exception as exc:
        result['status'] = False
        result['message'] = exc
        return result


def execute_db_query(query, value_array=0):
    try:
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

    except Exception as exc:
        print(exc)
        conn.close()
        return False


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
        PRIMARY KEY("id" AUTOINCREMENT)
        );
        """
    execute_db_query(query)

    query = """
        CREATE TABLE IF NOT EXISTS "shops" (
        "id"	INTEGER,
        "pid"	INTEGER UNIQUE,
        "shop"	TEXT UNIQUE,
        "work_time"	TEXT,
        "off_time"	TEXT,
        PRIMARY KEY("id" AUTOINCREMENT)
        );
    """
    execute_db_query(query)

    query = """
        CREATE TABLE IF NOT EXISTS "hosts" (
        "id"	INTEGER,
        "ip"	TEXT UNIQUE,
        "shop_id"	INTEGER,
        "group_id"	INTEGER,
        "type_id"	INTEGER,
        PRIMARY KEY("id" AUTOINCREMENT),
        FOREIGN KEY("shop_id") REFERENCES "shops"("id"),
        FOREIGN KEY("group_id") REFERENCES "groups"("id"),
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


def import_independed_values(file):
    try:
        sheet = pd.read_excel(file)
        db_fields = {
            'groups': 'group',
            'types': 'type',
            'tags': ['tag', 'value'],
        }
        for import_value in db_fields:
            print(import_value)
            db_import_list = []
            if import_value != 'tags':
                for i in sheet[import_value]:
                    db_import_list.append(tuple([i]))
                query = f"""
                        INSERT INTO {import_value} ('{db_fields[import_value]}') VALUES(?);
                    """
            else:
                for i in sheet.index:
                    if type(sheet['tags'][i]) == str:
                        if type(sheet['tag_value'][i]) == str:
                            db_import_list.append(
                                tuple([sheet['tags'][i], sheet['tag_value'][i]]))
                        else:
                            db_import_list.append(
                                tuple([sheet['tags'][i], '']))
                    else:
                        break
                query = f"""
                        INSERT INTO {import_value} ('{db_fields[import_value][0]}','{db_fields[import_value][1]}') VALUES(?, ?);
                    """
            if execute_db_query(query, db_import_list) == False:
                print('Ошибка импорта в БД')
                return False

    except Exception as exc:
        print(exc)
        return False


# create_db()
# query = """
#     SELECT hosts.ip, shops.pid, shops.shop FROM hosts
#     INNER JOIN shops ON hosts.shop_id = shops.id
# """
# a = execute_db_query(query)


# import_independed_values('data.xlsx')


# query = f"""
#         SELECT * FROM aboba
#         INNER JOIN sas
#         ON aboba.sas_id = sas.id
#         """
# create_tables()


# query = f"""
#         SELECT * FROM tags
#         """
# a = execute_db_query(query)
# for i in a:
#     if i[2]:
#         print(i)

# host = 'Гл. касса'
# a = get_hosts_from_ws_db(host)
# for i in a:
#     print(i)
key = get_zabbix_auth_key()
# print(key)

# hosts = get_hosts_from_zabbix(key, groupid=0, tag='')
# for i in hosts:
#     logging.info(i)

# groups = get_groups_from_zabbix(key)
# for i in groups:
#     print(i)


# hosts = [
#     {'host': '172.16.49.1', 'name': '172.16.49.1', 'tags': [{'tag': 'aboba2228', 'value': ''}], 'groups': [
#         {'name': 'Discovered hosts'}], 'interfaces': [{'ip': '172.16.49.1', 'interface_ref': 'if1'}], 'inventory_mode': 'DISABLED'},
#     {'host': '172.16.49.2', 'name': '172.16.49.2', 'tags': [{'tag': 'aboba2228', 'value': ''}, {'tag': 'zalupa', 'value': '1488'}], 'groups': [{'name': 'Discovered hosts'}, {'name': 'WAN2'}], 'interfaces': [{'ip':
#                                                                                                                                                                                                                 '172.16.49.2', 'interface_ref': 'if1'}], 'inventory_mode': 'DISABLED'}
# ]
# print(import_hosts_to_zabbix(key, host_list=hosts))

logging.info('info')
logging.error('error')

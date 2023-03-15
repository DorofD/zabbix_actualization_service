import os
import logging
import json
from dotenv import load_dotenv
import pyodbc
import requests
import ast
import sqlite3 as sq
import pandas as pd
import re

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
EXPORT_XLS_FILE = os.environ['EXPORT_XLS_FILE']


def get_hosts_from_ws_db(host_type):
    try:
        conn = pyodbc.connect(
            f'DRIVER={DB_DRIVER};SERVER={DB_SERVER};DATABASE={DATABASE};UID={DB_USER};PWD={DB_PASSWORD}')

        cursor = conn.cursor()

        query = f""" SELECT Expr1, Expr2, IP_ADRESS, TYPE
                FROM dbo.CamInShops_r
                WHERE TYPE = '{host_type}' """

        cursor.execute(query)
        result = {'status': True, 'message': '',
                  'result': list(cursor.fetchall())}
        return result
    except Exception as exc:
        result = {'status': False, 'message': exc}
        return result


def get_shops_from_ws_db():
    try:
        conn = pyodbc.connect(
            f'DRIVER={DB_DRIVER};SERVER={DB_SERVER};DATABASE={DATABASE};UID={DB_USER};PWD={DB_PASSWORD}')

        cursor = conn.cursor()
        query = f""" SELECT DISTINCT Expr1, Expr2 FROM dbo.CamInShops_r"""
        cursor.execute(query)
        result = {'status': True, 'message': '',
                  'result': list(cursor.fetchall())}
        return result
    except Exception as exc:
        result = {'status': False, 'message': exc}
        return result


def send_request_to_zabbix(request):
    try:
        responce = requests.post(
            # rf'{ZABBIX_SERVER}/api_jsonrpc.php', json=request, headers={'Content-Type': 'application/json-rpc'})  # для Zabbix 5.2
            rf'{ZABBIX_SERVER}/zabbix/api_jsonrpc.php', json=request, headers={'Content-Type': 'application/json-rpc'})  # для Zabbix 5.0
        decode_responce = responce.content.decode('utf-8')
        decode_responce = decode_responce.replace('true', 'True')
        decode_responce = decode_responce.replace('false', 'False')
        dict_responce = ast.literal_eval(decode_responce)
        result = {'status': True, 'message': '', 'result': dict_responce}
        return result
    except Exception as exc:
        result = {'status': False, 'message': exc}
        return result


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

        responce = send_request_to_zabbix(login)['result']
        result = {'status': True, 'message': '', 'result': responce['result']}
        return result

    except Exception as exc:
        result = {'status': False, 'message': exc}
        return result


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

        responce = send_request_to_zabbix(request)['result']
        result = {'status': True, 'message': '', 'result': responce['result']}
        return result
    except Exception as exc:
        result = {'status': False, 'message': exc}
        return result


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

        responce = send_request_to_zabbix(request)['result']
        result = {'status': True, 'message': '', 'result': responce['result']}
        return result
    except Exception as exc:
        result = {'status': False, 'message': exc}
        return result


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
                    "hosts": {"createMissing": True, "updateExisting": False},
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

        responce = send_request_to_zabbix(request)['result']
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
            result = {'status': True, 'message': '',
                      'result': cursor.fetchall()}
        else:
            cursor.executemany(query, value_array)
            result = {'status': True, 'message': ''}
        conn.commit()
        conn.close()
        return result

    except Exception as exc:
        print(exc)
        conn.close()
        result = {'status': False, 'message': exc}
        return result


def create_db():
    try:
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
            "off_time"	INTEGER,
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
        result = {'status': True, 'message': ''}
        return result
    except Exception as exc:
        result = {'status': False, 'message': exc}
        return result


def import_independed_values(file):
    try:
        sheet = pd.read_excel(file)
        db_fields = {
            'groups': 'group',
            'types': 'type',
            'tags': ['tag', 'value'],
        }
        for field_name in db_fields:
            query = f"""
                    SELECT * FROM {field_name}
                    """
            available_values = []
            for i in execute_db_query(query)['result']:
                available_values.append(i[1])
            print(available_values)
            db_import_list = []
            if field_name != 'tags':
                for i in sheet[field_name]:
                    if i not in available_values and type(i) == str:
                        db_import_list.append(tuple([i]))
                query = f"""
                        INSERT INTO {field_name} ('{db_fields[field_name]}') VALUES(?);
                    """
            else:
                for i in sheet.index:
                    if type(sheet['tags'][i]) == str and sheet['tags'][i] not in available_values:
                        if type(sheet['tag_value'][i]) == str:
                            db_import_list.append(
                                tuple([sheet['tags'][i], sheet['tag_value'][i]]))
                        else:
                            db_import_list.append(
                                tuple([sheet['tags'][i], '']))
                    else:
                        continue
                query = f"""
                        INSERT INTO {field_name} ('{db_fields[field_name][0]}','{db_fields[field_name][1]}') VALUES(?, ?);
                    """
            if not db_import_list:
                continue
            if execute_db_query(query, db_import_list)['status'] == False:
                print('Ошибка импорта в поле БД:', field_name)
                result = {'status': False,
                          'message': f"Ошибка импорта в поле БД: {field_name}"}
                return result
        result = {'status': True, 'message': ''}
        return result
    except Exception as exc:
        result = {'status': False, 'message': exc}
        return result


def get_all_shops_from_xls(file):
    try:
        sheet = pd.read_excel(file)
        shops = []
        for i in sheet.index:
            if type(sheet['График работы'][i]) == str:
                temp = re.findall(f'\d\d:\d\d-\d\d:\d\d',
                                  sheet['График работы'][i])

                if temp:
                    temp_work_time = temp[0]
                    start_stop = re.findall(f'\d\d:\d\d', temp_work_time)
                    start_time = pd.to_datetime(start_stop[0], format='%H:%M')
                    end_time = pd.to_datetime(start_stop[1], format='%H:%M')
                else:
                    temp = re.findall(f'\d:\d\d-\d\d:\d\d',
                                      sheet['График работы'][i])
                    if temp:
                        temp_work_time = temp[0]
                        # print(temp_work_time)
                        start_time = pd.to_datetime(re.findall(
                            f'\d:\d\d', temp_work_time)[0], format='%H:%M')
                        end_time = pd.to_datetime(re.findall(
                            f'\d\d:\d\d', temp_work_time)[0], format='%H:%M')

                    else:
                        temp = re.findall(f'\d\d:\d\d - \d\d:\d\d',
                                          sheet['График работы'][i])
                        if temp:
                            temp_work_time = temp[0]
                            start_stop = re.findall(
                                f'\d\d:\d\d', temp_work_time)
                            start_time = pd.to_datetime(
                                start_stop[0], format='%H:%M')
                            end_time = pd.to_datetime(
                                start_stop[1], format='%H:%M')
                        else:
                            print(sheet['PT_ID'][i])
                            continue
            else:
                continue

            try:
                dif = pd.Timedelta(hours=int(sheet['Разница во времени'][i]))
                start_time -= dif
                end_time -= dif
            except:
                pass

            off_time = 24 - int((end_time - start_time) /
                                pd.Timedelta('1 hour'))

            work_time = f'{str(start_time)[11:16]}-{str(end_time)[11:16]}'
            shops.append(
                (int(sheet['PT_ID'][i]), sheet['Магазин'][i], work_time, off_time))

        result = {'status': True, 'message': '', 'result': shops}
        return result

    except Exception as exc:
        result = {'status': False, 'message': exc}
        return result


def import_shops():
    try:
        # получение всех магазинов из Магазинов в цифрах
        shops_from_xls = get_all_shops_from_xls(EXPORT_XLS_FILE)
        if not shops_from_xls['status']:
            result = {'status': False,
                      'message': "Can't get shop list from xls"}
            return result
        shops_from_xls = shops_from_xls['result']
        shops_from_xls_dict = {}
        for i in range(len(shops_from_xls)):
            shops_from_xls_dict[shops_from_xls[i][0]] = shops_from_xls[i]

        # получение списка PIDов из WS
        shops_from_ws = get_shops_from_ws_db()
        if not shops_from_ws['status']:
            result = {'status': False,
                      'message': "Can't get shop list from WS"}
            return result
        shops_from_ws = shops_from_ws['result']
        pid_list = []
        for shop in shops_from_ws:
            pid_list.append(shop[0])

        # создание словаря из магазинов в WS
        actual_shop_dict = {}
        for pid in pid_list:
            if pid in shops_from_xls_dict:
                actual_shop_dict[pid] = shops_from_xls_dict[pid]
            else:
                logging.error('Shop not in xls ', i)

        # создание словаря магазинов из локальной БД
        query = """
            SELECT pid, shop, work_time, off_time FROM shops
        """
        shops_from_local_db_list = execute_db_query(query)
        if not shops_from_local_db_list['status']:
            result = {'status': False,
                      'message': "Can't get shop list from local DB"}
            return result
        shops_from_local_db_list = shops_from_local_db_list['result']
        shops_from_local_db_dict = {}
        for i in shops_from_local_db_list:
            shops_from_local_db_dict[i[0]] = i

        # сортировка магазинов на добавляемые и изменяемые
        add_shop_list = []
        change_shop_list = []
        for pid in actual_shop_dict:
            if pid not in shops_from_local_db_dict:
                add_shop_list.append(actual_shop_dict[pid])
            else:
                change_shop_list.append(actual_shop_dict[pid])

        # добавление отсутствующих магазинов
        query = f"""
                    INSERT INTO shops ('pid', 'shop', 'work_time', 'off_time') VALUES(?, ?, ?, ?);
                """
        add_count = len(add_shop_list)
        update_count = 0
        if add_shop_list:
            execute_db_query(query, add_shop_list)

        # обновление значений измененных магазинов
        for shop in change_shop_list:
            if shop not in shops_from_local_db_list:
                query = f"""
                            UPDATE shops SET (work_time, off_time) = ('{shop[2]}', '{shop[3]}')
                            WHERE pid = '{shop[0]}';
                        """
                update_count += 1
                execute_db_query(query)

        result = {'status': True,
                  'message': f'shops added: {add_count}, shops updated: {update_count}', 'result': ''}
        return result
    except Exception as exc:
        result = {'status': False, 'message': exc, 'result': ''}
        return result


# create_db()
print(import_shops())


# sas = get_shops_from_ws_db()
# for i in sas['result']:
#     print(i)

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
# available_values = []
# for i in a:
#     available_values.append
# host = 'Гл. касса'
# a = get_hosts_from_ws_db(host)['result']
# for i in a:
#     print(i)
# key = get_zabbix_auth_key()['result']
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

# logging.info('info')
# logging.error('error')

# from ...src.db_scripts.ws_db import get_hosts_from_ws_db
import os
from db_scripts import ws_db as db
import logging
from dotenv import load_dotenv
import pandas as pd
import re
print(db.get_hosts_from_ws_db('WAN2'))


logging.basicConfig(level=logging.INFO,
                    filename="log.txt", filemode="w", format=f'%(asctime)s %(levelname)s: %(message)s')

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

EXPORT_XLS_FILE = os.environ['EXPORT_XLS_FILE']


def import_host_parameters(file):
    try:
        sheet = pd.read_excel(file)
        # импорт groups
        query = f"""
                    SELECT * FROM groups
                    """
        groups_from_local_db = execute_db_query(query)
        if groups_from_local_db['status'] == False:
            result = {'status': False,
                      'message': "Can't get groups from local DB"}
            return result
        current_groups_list = []
        for group in groups_from_local_db['result']:
            current_groups_list.append(group[1])
        groups_to_add = []
        for cell in sheet['groups']:
            if cell not in current_groups_list and type(cell) == str:
                groups_to_add.append(tuple([cell]))
        groups_add_count = len(groups_to_add)
        query = f"""
                    INSERT INTO groups ('group') VALUES(?);
                """
        if groups_to_add:
            if execute_db_query(query, groups_to_add)['status'] == False:
                result = {'status': False,
                          'message': "Can't insert groups"}
                return result

        # импорт types
        query = f"""
                    SELECT * FROM groups
                    """
        groups_from_local_db = execute_db_query(query)
        if groups_from_local_db['status'] == False:
            result = {'status': False,
                      'message': "Can't get groups from local DB"}
            return result

        query = f"""
                    SELECT * FROM types
                """
        types_from_local_db = execute_db_query(query)
        if types_from_local_db['status'] == False:
            result = {'status': False,
                      'message': "Can't get types from local DB"}
            return result

        groups_dict = {}
        for group in groups_from_local_db['result']:
            groups_dict[group[1]] = group[0]

        current_types_dict = {}
        for host_type in types_from_local_db['result']:
            current_types_dict[host_type[1]] = tuple(
                [host_type[1], host_type[2]])
        types_to_add = []
        types_to_update = []
        for i in sheet.index:
            if type(sheet['types'][i]) == str:
                if sheet['type_group'][i] in groups_dict:
                    num = groups_dict[sheet['type_group'][i]]
                    if sheet['types'][i] not in current_types_dict:
                        types_to_add.append(
                            tuple([sheet['types'][i], groups_dict[sheet['type_group'][i]]]))
                    elif groups_dict[sheet['type_group'][i]] != current_types_dict[sheet['types'][i]][1]:
                        types_to_update.append(
                            tuple([sheet['types'][i], groups_dict[sheet['type_group'][i]]]))
                    else:
                        continue
                else:
                    result = {'status': False,
                              'message': "Unknown group in import file"}
                    return result

        # добавление отсутствующих типов
        query = f"""
                    INSERT INTO types ('type', 'group_id') VALUES(?, ?);
                """
        types_add_count = len(types_to_add)
        if types_to_add:
            if execute_db_query(query, types_to_add)['status'] == False:
                result = {'status': True,
                          'message': 'Error types adding', 'result': ''}

        # обновление значений измененных типов
        types_update_count = 0
        for host_type in types_to_update:
            query = f"""
                        UPDATE types SET (group_id) = ('{host_type[1]}')
                        WHERE type = '{host_type[0]}';
                    """
            groups_update_count += 1
            execute_db_query(query)

        # импорт tags
        query = """
            SELECT tag, value FROM tags
        """
        tags_from_local_db = execute_db_query(query)
        if tags_from_local_db['status'] == False:
            result = {'status': False,
                      'message': "Can't get tags from local DB"}
            return result

        current_tags_dict = {}
        for tag in tags_from_local_db['result']:
            current_tags_dict[tag[0]] = tag

        tags_to_add = []
        tags_to_update = []
        for i in sheet.index:
            if type(sheet['tags'][i]) == str:
                if sheet['tags'][i] not in current_tags_dict:
                    if type(sheet['tag_value'][i]) == str:
                        tags_to_add.append(tuple(
                            [sheet['tags'][i], sheet['tag_value'][i]]))
                    else:
                        tags_to_add.append(tuple(
                            [sheet['tags'][i], '']))
                elif sheet['tag_value'][i] != current_tags_dict[sheet['tags'][i]][1]:
                    if type(sheet['tag_value'][i]) == str or type(sheet['tag_value'][i]) == int:
                        tags_to_update.append(tuple(
                            [sheet['tags'][i], sheet['tag_value'][i]]))
                    elif type(sheet['tag_value'][i]) == float:
                        tags_to_update.append(tuple(
                            [sheet['tags'][i], '']))
                    else:
                        continue

        # добавление отсутствующих тегов
        query = f"""
                    INSERT INTO tags ('tag', 'value') VALUES(?, ?);
                """
        tags_add_count = len(tags_to_add)
        if tags_to_add:
            if execute_db_query(query, tags_to_add)['status'] == False:
                result = {'status': True,
                          'message': 'Error tags adding', 'result': ''}

        # обновление значений измененных тегов
        tags_update_count = 0
        for tag in tags_to_update:
            query = f"""
                        UPDATE tags SET (value) = ('{tag[1]}')
                        WHERE tag = '{tag[0]}';
                    """
            tags_update_count += 1
            execute_db_query(query)

        result = {'status': True, 'message': f"groups add: {groups_add_count}, types add/update: {types_add_count}/{types_update_count}, tags add/update: {tags_add_count}/{tags_update_count}"}
        return result

    except Exception as exc:
        result = {'status': False, 'message': exc}
        return result


def get_shops_from_xls(file):
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
                            # print(sheet['PT_ID'][i])
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
        shops_from_xls = get_shops_from_xls(EXPORT_XLS_FILE)
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
        if add_shop_list:
            execute_db_query(query, add_shop_list)

        # обновление значений измененных магазинов
        update_count = 0
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


def import_hosts(types=[]):
    # получение типов из WS
    try:
        types_from_ws = get_types_from_ws_db()
        if types_from_ws['status'] == False:
            result = {'status': False, 'message': "Can't get types from WS"}
            return result
        types_from_ws = types_from_ws['result']
        types_from_ws_list = []
        for host_type in types_from_ws:
            types_from_ws_list.append(host_type[0])

        # получение типов из локальной БД
        query = """
                SELECT * FROM types
            """
        types_from_local_db = execute_db_query(query)
        if types_from_local_db['status'] == False:
            result = {'status': False,
                      'message': "Can't get types from local DB"}
            return result
        types_from_local_db_dict = {}
        for host_type in types_from_local_db['result']:
            types_from_local_db_dict[host_type[1]] = host_type

        # проверка совпадения типов в локальной БД и БД WS
        for host_type in types_from_local_db_dict:
            if host_type not in types_from_ws_list:
                result = {'status': False,
                          'message': f"Unknown type in local DB: {host_type}"}
                return result
        for host_type in types_from_ws_list:
            if host_type not in types_from_local_db_dict:
                result = {'status': False,
                          'message': f"Unknown type in WS DB: {host_type}"}
                return result
        types_dict = types_from_local_db_dict

        # выбор финального списка типов для импорта
        if types:
            for host_type in types:
                if host_type not in types_dict:
                    result = {'status': False,
                              'message': f"Unknown type was given: {host_type}"}
                    return result
            types_list = types
        else:
            types_list = types_from_ws_list

        # получение всех хостов из локальной БД
        query = """
            SELECT hosts.ip, hosts.shop_pid, types.type FROM hosts
            INNER JOIN types ON hosts.type_id = types.id
        """
        hosts_from_local_db = execute_db_query(query)
        if hosts_from_local_db['status'] == False:
            result = {'status': False,
                      'message': "Can't get hosts from local DB"}
            return result
        hosts_from_local_db = hosts_from_local_db['result']
        hosts_from_local_db_dict = {}
        for host in hosts_from_local_db:
            hosts_from_local_db_dict[host[0]] = host
        import_results = {}
        update_count = 0
        add_count = 0
        spent_addresses = []
        for host_type in types_list:
            # получение хостов из WS по типу
            hosts_from_ws_db = get_hosts_from_ws_db(host_type)
            if hosts_from_ws_db['status'] == False:
                import_results[host_type] = {
                    'status': False, 'message': f"Can't get {host_type} from WS DB"}
                continue
            hosts_from_ws_db = hosts_from_ws_db['result']

            hosts_to_add = []
            hosts_to_update = []
            # сортировка хостов на добавляемые/обновляемые
            for host in hosts_from_ws_db:
                if host[2] in spent_addresses:
                    result = {'status': False,
                              'message': f"Duplicate host ip: {host}"}
                    return result
                else:
                    spent_addresses.append(host[2])
                if host[2] not in hosts_from_local_db_dict:
                    hosts_to_add.append(
                        tuple([host[2], host[0], types_dict[host[3]][0]]))
                elif host[3] != hosts_from_local_db_dict[host[2]][2] or host[0] != hosts_from_local_db_dict[host[2]][1]:
                    hosts_to_update.append(
                        tuple([host[2], host[0], types_dict[host[3]][0]]))
                else:
                    continue

            # добавление новых хостов
            add_count += len(hosts_to_add)
            query = f"""
                        INSERT INTO hosts ('ip', 'shop_pid', 'type_id') VALUES(?, ?, ?);
                    """
            if hosts_to_add:
                if execute_db_query(query, hosts_to_add)['status'] == False:
                    result = {'status': False,
                              'message': f"Can't add new hosts: {host_type}"}
                    return result

            # обновление измененных хостов
            for host in hosts_to_update:
                query = f"""
                            UPDATE hosts SET (shop_pid, type_id) = ('{host[1]}', '{host[2]}')
                            WHERE ip = '{host[0]}';
                        """
                update_count += 1
                if execute_db_query(query, hosts_to_add)['status'] == False:
                    result = {'status': False,
                              'message': f"Can't update hosts: {host_type}"}
                    return result
        result = {'status': True,
                  'message': f'hosts added: {add_count}, hosts updated: {update_count}', 'result': ''}
        return result
    except Exception as exc:
        result = {'status': False, 'message': exc, 'result': ''}
        return result

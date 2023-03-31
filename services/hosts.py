from services.host_parameters import compare_local_and_ws_types
from db_scripts.local_db import *
from zabbix_scripts.zabbix_operations import get_zabbix_auth_key
from zabbix_scripts.zabbix_groups import get_groups_from_zabbix, add_group_to_zabbix
from db_scripts.ws_db import get_hosts_from_ws_db
import logging


logging.basicConfig(level=logging.INFO,
                    filename="log.txt", filemode="w", format=f'%(asctime)s %(levelname)s: %(message)s')


def import_hosts():
    # проверка совпадения типов в локальной БД и БД WS
    compare_local_and_ws_types()

    hosts_from_ws_db = get_hosts_from_ws_db()
    hosts_from_local_db = get_hosts_from_local_db()

    addresses_from_local_db = []
    for host in hosts_from_local_db:
        addresses_from_local_db.append(host[1])

    types = get_types_from_local_db()
    types_dict = {types[i][1]: types[i][0] for i in range(len(types))}

    # сортировка хостов на добавляемые/обновляемые
    spent_addresses = []
    hosts_to_add = []
    hosts_to_update = []
    for host in hosts_from_ws_db:
        if host[1] in spent_addresses:
            raise Exception(f'Duplicate ip: {host}')
        spent_addresses.append(host[1])
        if host not in hosts_from_local_db:
            if host[1] not in addresses_from_local_db:
                hosts_to_add.append(
                    tuple([host[1], host[0], types_dict[host[2]]]))
            elif host[1] in addresses_from_local_db:
                hosts_to_update.append(
                    tuple([host[1], host[0], types_dict[host[2]]]))

    # добавление новых хостов
    if hosts_to_add:
        add_hosts_to_local_db(hosts_to_add)
    # обновление измененных хостов
    if hosts_to_update:
        update_hosts_from_local_db(hosts_to_update)
    return True


def delete_missing_hosts():
    hosts_from_ws_db = get_hosts_from_ws_db()
    hosts_from_local_db = get_hosts_from_local_db()
    # получение списков ip адресов из WS и локальной БД
    ip_from_ws = [hosts_from_ws_db[i][1]
                  for i in range(len(hosts_from_ws_db))]
    ip_from_local_db = [hosts_from_local_db[i][1]
                        for i in range(len(hosts_from_local_db))]

    # поиск отсутствующих в WS адресов из локальной БД
    ip_to_delete = []
    for ip in ip_from_local_db:
        if ip not in ip_from_ws:
            ip_to_delete.append(ip)

    if ip_to_delete:
        delete_hosts_from_local_db(ip_to_delete)
    return True


def create_import_list(type_id):
    hosts = get_hosts_from_local_db_to_import(type_id)

    # словарь типов и шаблонов в формате type:template
    type_template_dict = {note[0]: note[1]
                          for note in get_type_template_view()}
    # словарь магазинов в формате pid:[work_time, off_time]
    shops_dict = {shop[0]: [shop[2], shop[3]]
                  for shop in get_shops_from_local_db()}

    # шаблон в zabbix, присоединяемый к хосту
    # ! дописать присвоение нескольких шаблонов
    try:
        zabbix_template = type_template_dict[hosts[0][3]]
    except:
        raise Exception(f'No hosts with typeid{type_id}')

    key = get_zabbix_auth_key()
    # группы из zabbix
    groups_from_zabbix_dict = get_groups_from_zabbix(key)

    import_list = []

    for host in hosts:
        template_for_import_list = {
            'host': 'ip_address',
            'name': 'host_visible_name',
            'templates': [{"name": "template_name"}],
            # 'tags': [{'tag': 'aboba22282222', 'value': ''}],
            'groups': [{'name': 'group_name'}],
            'interfaces': [{'ip': 'ip_address', 'interface_ref': 'if1'}],
            'inventory_mode': 'DISABLED'}

        # уникальное имя хоста
        template_for_import_list['host'] = host[2]

        # отображаемое имя хоста
        template_for_import_list['name'] = f'{host[0]} {host[1]} {host[3]} ({host[2]})'

        # шаблон в zabbix, присоединяемый к хосту
        # ! дописать присвоение нескольких шаблонов
        template_for_import_list['templates'][0]['name'] = zabbix_template

        # группы в zabbix, присоединяемые к хосту
        work_time_group = f'WT {shops_dict[host[0]][0]}'
        if work_time_group not in groups_from_zabbix_dict:
            add_group_to_zabbix(key=key, group_name=work_time_group)
            groups_from_zabbix_dict = get_groups_from_zabbix(key)
        type_group = host[3]
        if type_group not in groups_from_zabbix_dict:
            add_group_to_zabbix(key=key, group_name=type_group)
            groups_from_zabbix_dict = get_groups_from_zabbix(key)
        template_for_import_list['groups'] = [
            {'name': work_time_group}, {'name': type_group}]
        # интерфейс хоста
        template_for_import_list['interfaces'][0]['ip'] = host[2]

        import_list.append(template_for_import_list)

    return import_list
# print(import_hosts())
# delete_missing_hosts()

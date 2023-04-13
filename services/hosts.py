from db_scripts.local_db import *
from zabbix_scripts.zabbix_operations import get_zabbix_auth_key
from zabbix_scripts.zabbix_groups import get_groups_from_zabbix, add_group_to_zabbix
from db_scripts.ws_db import get_hosts_from_ws_db


def import_hosts():

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
    # список ip адресов из WS
    ip_from_ws = [hosts_from_ws_db[i][1]
                  for i in range(len(hosts_from_ws_db))]
    # словарь адресов в формате ip:id из локальной БД
    ip_from_local_db_dict = {hosts_from_local_db[i][1]: hosts_from_local_db[i][3]
                             for i in range(len(hosts_from_local_db))}
    # список для удаления связей из host_template
    id_to_delete = []
    # поиск отсутствующих в WS адресов из локальной БД
    ip_to_delete = []
    for ip in ip_from_local_db_dict:
        if ip not in ip_from_ws:
            ip_to_delete.append(ip)
            id_to_delete.append(ip_from_local_db_dict[ip])
    # удаление хостов
    if ip_to_delete:
        delete_host_template_notes_from_local_db(id_to_delete)
        delete_hosts_from_local_db(ip_to_delete)
    return True


def create_import_list(type_id):
    hosts = get_hosts_from_local_db_to_import(type_id)
    # список шаблонов для выбранного типа хостов
    type_templates_list = [note[1] for note in get_type_template_view(type_id)]
    # словарь магазинов в формате pid:[work_time, off_time]
    shops_dict = {shop[0]: [shop[2], shop[3]]
                  for shop in get_shops_from_local_db()}
    # список ip адресов хостов с присоединенными шаблонами
    host_templates_ip_list = [host[0] for host in get_host_template_view()]

    key = get_zabbix_auth_key()
    # группы из zabbix
    groups_from_zabbix_dict = get_groups_from_zabbix(key)

    import_list = []

    for host in hosts:
        template_for_import_list = {
            'host': 'ip_address',
            'name': 'host_visible_name',
            # 'templates' содержит список словарей в формате {"name": "template_name"}
            'templates': [],
            # 'tags': [{'tag': 'aboba22282222', 'value': ''}],
            'groups': [{'name': 'group_name'}],
            'interfaces': [{'ip': 'ip_address', 'interface_ref': 'if1'}],
            'inventory_mode': 'DISABLED'}

        # уникальное имя хоста
        template_for_import_list['host'] = host[2]

        # отображаемое имя хоста
        template_for_import_list['name'] = f'{host[0]} {host[1]} {host[3]} ({host[2]})'

        # шаблоны в zabbix, присоединяемые к хосту
        templates = []
        # шаблоны для типов
        for template in type_templates_list:
            templates.append(template)
        # шаблоны для конкретного хоста
        host_templates = []
        if host[2] in host_templates_ip_list:
            host_templates = [host[1]
                              for host in get_host_template_view(host[4])]
        if host_templates:
            for template in host_templates:
                templates.append(template)
        # присвоение хосту шаблонов
        for template in templates:
            template_for_import_list['templates'].append({"name": template})

        # группы в zabbix, присоединяемые к хосту (группа типа и группа work_time)
        work_time_group = f'WT {shops_dict[host[0]][0]} {shops_dict[host[0]][1]}'
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

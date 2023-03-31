from services.host_parameters import *
from services.shops import *
from services.hosts import *
from zabbix_scripts.zabbix_hosts import *
from zabbix_scripts.zabbix_groups import *
from zabbix_scripts.zabbix_operations import get_zabbix_auth_key
from zabbix_scripts.zabbix_maintenance import update_zabbix_maintenance


def update_local_data():
    pass


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


def update_zabbix_data():
    key = get_zabbix_auth_key()
    # словарь типов в формате type:id
    types_dict = {type[1]: type[0] for type in get_types_from_local_db()}
    # словарь типов и шаблонов в формате type:template
    type_template_dict = {note[0]: note[1]for note in get_type_template_view()}

    # обновление хостов
    for host_type in types_dict:
        if host_type in type_template_dict:
            import_list = create_import_list(types_dict[host_type])
            import_hosts_to_zabbix(key=key, host_list=import_list)

    # обновление периодов и групп обслуживания
    update_zabbix_maintenance(key)
    return True


update_zabbix_data()

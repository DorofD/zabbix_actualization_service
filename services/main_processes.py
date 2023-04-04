from services.host_parameters import *
from services.shops import *
from services.hosts import *
from zabbix_scripts.zabbix_hosts import *
from zabbix_scripts.zabbix_groups import *
from zabbix_scripts.zabbix_operations import get_zabbix_auth_key
from zabbix_scripts.zabbix_maintenance import update_zabbix_maintenance
import logging

logging.basicConfig(level=logging.INFO,
                    filename="log.txt", filemode="a", format=f'%(asctime)s %(levelname)s: %(message)s')


def update_local_data(file):
    try:
        create_db()
        update_shops()
        import_groups_from_excel(file)
        import_types_from_excel(file)
        import_tags_from_excel(file)
        set_templates_to_types(file)
        import_hosts()
        delete_missing_hosts()
        logging.info('Local data update success')
        return True
    except Exception as exc:
        logging.error(f'Local data update fail: {exc}')
        raise Exception(exc)


def update_zabbix_data():
    try:
        key = get_zabbix_auth_key()
        # словарь типов в формате type:id
        types_dict = {type[1]: type[0] for type in get_types_from_local_db()}
        # словарь типов и шаблонов в формате type:template
        type_template_dict = {note[0]: note[1]
                              for note in get_type_template_view()}

        # обновление хостов
        for host_type in types_dict:
            if host_type in type_template_dict:
                import_list = create_import_list(types_dict[host_type])
                print('start import', host_type)
                import_hosts_to_zabbix(key=key, host_list=import_list)
                print('end import', host_type)

        # обновление периодов и групп обслуживания
        update_zabbix_maintenance(key)

        # удаление неактуальных хостов из Zabbix
        ip_to_delete = []
        ip_list_from_ws = [shop[1] for shop in get_hosts_from_ws_db()]
        ip_list_from_zabbix = [host['host']
                               for host in get_hosts_from_zabbix(key)]
        for ip in ip_list_from_zabbix:
            if ip not in ip_list_from_ws:
                ip_to_delete.append(ip)
        delete_hosts_from_zabbix(key=key, ip_list=ip_to_delete)

        logging.info('Zabbix data update success')
        return True
    except Exception as exc:
        logging.error(f'Zabbix data update fail: {exc}')
        raise Exception(exc)


update_local_data('data.xlsx')
update_zabbix_data()

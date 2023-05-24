from services.ws_entities.host_parameters import *
from services.ws_entities.shops import *
from services.ws_entities.hosts import *
from services.notifications.email_smtp import *
from services.notifications.telegram import *
from services.zabbix_scripts.zabbix_hosts import *
from services.zabbix_scripts.zabbix_groups import *
from services.zabbix_scripts.zabbix_api import get_zabbix_auth_key
from services.zabbix_scripts.zabbix_maintenance import update_zabbix_maintenance
from services.radius.radius_operations import *
from models.ws_db import get_hosts_from_ws_db

import logging

# общий лог файл
logging.basicConfig(level=logging.INFO,
                    filename="flask_log.txt", filemode="a", format=f'%(asctime)s %(levelname)s: %(message)s')
# лог для логики приложения
handler = logging.FileHandler('log.txt')
handler.setFormatter(logging.Formatter(
    f'%(asctime)s %(levelname)s %(message)s'))

app_logger = logging.getLogger('app_logger')
app_logger.setLevel(logging.INFO)
app_logger.addHandler(handler)


def update_local_data():
    try:
        update_shops()
        update_types()
        import_hosts()
        delete_missing_hosts()
        app_logger.info("Local data update success")
        return True
    except Exception as exc:
        app_logger.error(f"Local data update fail: {exc}")
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
                import_hosts_to_zabbix(key=key, host_list=import_list)

        # обновление обслуживания
        update_zabbix_maintenance(key)

        # удаление неактуальных хостов из Zabbix
        ip_to_delete = []
        ip_list_from_ws = [shop[1] for shop in get_hosts_from_ws_db()]
        ip_list_from_zabbix = [host['host']
                               for host in get_hosts_from_zabbix(key)]
        for ip in ip_list_from_zabbix:
            if ip not in ip_list_from_ws:
                ip_to_delete.append(ip)
        if ip_to_delete:
            delete_hosts_from_zabbix(key=key, ip_list=ip_to_delete)

        app_logger.info("Zabbix data update success")
        return True
    except Exception as exc:
        app_logger.error(f"Zabbix data update fail: {exc}")
        raise Exception(exc)


def actualize_radius():
    try:
        hosts = get_hosts_from_ws_db(types=['WAN', 'WAN2'])
        host_list_from_ws = []
        for host in hosts:
            host_list_from_ws.append(
                {'Name': f'{host[0]}-{host[2]}', 'Address': host[3]})
        client_list_from_radius = get_radius_clients()

        # удаление неактуальных клиентов
        clients_to_remove = []
        for client in client_list_from_radius:
            if client not in host_list_from_ws and client['Address'] != '172.16.0.0/16':
                clients_to_remove.append(client)
        remove_radius_clients(clients_to_remove)
        app_logger.info("RADIUS update success")
        # добавление отсутствующих клиентов
        clients_to_add = []
        for client in host_list_from_ws:
            if client not in client_list_from_radius:
                clients_to_add.append(client)
        add_radius_clients(clients_to_add)
        return True
    except Exception as exc:
        app_logger.error(f"RADIUS update fail: {exc}")
        raise Exception(exc)


def execute_main_operations():
    try:
        update_local_data()
        update_zabbix_data()
        actualize_radius()
        return True
    except Exception as exc:
        send_tg_message(str(exc))
        if send_email(str(exc)):
            app_logger.info("Error message sent to recipients")
        else:
            app_logger.error(f"Unexpected error, can't send error message")
        raise Exception(str(exc))

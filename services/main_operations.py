from services.host_parameters import *
from services.shops import *
from services.hosts import *
from services.notifications import *
from zabbix_scripts.zabbix_hosts import *
from zabbix_scripts.zabbix_groups import *
from zabbix_scripts.zabbix_operations import get_zabbix_auth_key
from zabbix_scripts.zabbix_maintenance import update_zabbix_maintenance
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
        create_db()
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


def execute_main_operations():
    try:
        update_local_data()
        update_zabbix_data()
        return True
    except Exception as exc:
        if send_email(str(exc)):
            app_logger.info("Error message sent to recipients")
        else:
            app_logger.error(f"Unexpected error, can't send error message")
        raise Exception(str(exc))
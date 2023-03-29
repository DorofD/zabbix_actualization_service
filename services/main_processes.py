from services.host_parameters import *
from services.shops import *
from services.hosts import *
from zabbix_scripts.zabbix_hosts import *
from zabbix_scripts.zabbix_operations import get_zabbix_auth_key


def update_local_data():
    pass


def update_hosts_in_zabbix():
    key = get_zabbix_auth_key()
    types_dict = {type[1]: type[0] for type in get_types_from_local_db()}
    print(types_dict)
    type_template_dict = {note[0]: note[1]
                          for note in get_type_template_view()}
    print(type_template_dict)

    for host_type in types_dict:
        if host_type in type_template_dict:
            hosts = create_import_host_list(types_dict[host_type])
            # for i in range(3):
            #     print(hosts[i])


update_hosts_in_zabbix()

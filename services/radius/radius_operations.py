import paramiko
from services.env_vars import get_var
from models.ws_db import get_hosts_from_ws_db


RADIUS_SERVER = get_var('RADIUS_SERVER')
RADIUS_USER = get_var('RADIUS_USER')
RADIUS_PASSWORD = get_var('RADIUS_PASSWORD')
RADIUS_SHARED_SECRET = get_var('RADIUS_SHARED_SECRET')


def get_ssh_connection():
    conn = paramiko.SSHClient()
    conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    conn.connect(hostname=RADIUS_SERVER, port=22,
                 username=RADIUS_USER, password=RADIUS_PASSWORD, timeout=2)
    return conn


def get_radius_clients():
    conn = get_ssh_connection()
    stdin, stdout, stderr = conn.exec_command('Get-NpsRadiusClient')
    out_message = stdout.read().decode('utf-8', errors='ignore')
    error_message = stderr.read().decode('utf-8', errors='ignore')
    if error_message:
        error_message = error_message.replace('\x1b[31;1m', '')
        error_message = error_message.replace('\x1b[0m\r', '')
        raise Exception(f'get radius client error: {error_message}')

    out_message = out_message.replace('\r', '')
    out_message = out_message.replace(' ', '')
    out_message = out_message.replace('\x1b[0m', '')
    out_message = out_message.replace('\x1b[32;1m', '')
    out_message = out_message.split('\n')
    while '' in out_message:
        out_message.remove('')
    clients_list = []
    new_dict = {}
    for note in out_message:
        if 'Name' in note and 'VendorName' not in note:
            new_dict['Name'] = note.split(':')[1]
        if 'Address' in note:
            new_dict['Address'] = note.split(':')[1]
        if 'Enabled' in note:
            clients_list.append(new_dict)
            new_dict = {}

    return clients_list


def add_radius_clients(clients_list: list):
    conn = get_ssh_connection()
    for client in clients_list:
        stdin, stdout, stderr = conn.exec_command(
            f'New-NpsRadiusClient -Address "{client["Address"]}" -Name "{client["Name"]}" -SharedSecret "{RADIUS_SHARED_SECRET}"')
        error_message = stderr.read().decode('utf-8', errors='ignore')
        if error_message:
            error_message = error_message.replace('\x1b[31;1m', '')
            error_message = error_message.replace('\x1b[0m\r', '')
            raise Exception(f'add radius client error: {error_message}')
    return True


def remove_radius_clients(clients_list: list):
    conn = get_ssh_connection()
    for client in clients_list:
        stdin, stdout, stderr = conn.exec_command(
            f'Remove-NpsRadiusClient -Name "{client["Name"]}"')
        error_message = stderr.read().decode('utf-8', errors='ignore')
        if error_message:
            error_message = error_message.replace('\x1b[31;1m', '')
            error_message = error_message.replace('\x1b[0m\r', '')
            raise Exception(f'remove radius client error: {error_message}')
    return True


def actualize_radius():
    hosts = get_hosts_from_ws_db(types=['WAN', 'WAN2'])
    host_list_from_ws = []
    for host in hosts:
        host_list_from_ws.append(
            {'Name': f'{host[0]}-{host[2]}', 'Address': host[3]})
    client_list_from_radius = get_radius_clients()
    print(len(client_list_from_radius))
    # добавление отсутствующих клиентов
    clients_to_add = []
    for client in host_list_from_ws:
        if client not in client_list_from_radius:
            clients_to_add.append(client)
    add_radius_clients(clients_to_add)

    # удаление неактуальных клиентов
    clients_to_remove = []
    for client in client_list_from_radius:
        if client not in host_list_from_ws:
            clients_to_remove.append(client)
    remove_radius_clients(clients_to_remove)


actualize_radius()
# clients = [{'Name': '979-WAN', 'Address': '176.211.110.66'},
#            {'Name': '979-WAN2', 'Address': '31.170.112.71'},
#            {'Name': '980-WAN', 'Address': '195.239.185.130'},
#            {'Name': '980-WAN2', 'Address': '90.154.0.230'},
#            {'Name': '981-WAN', 'Address': '178.185.143.2'}
#            ]
# add_radius_clients(clients)

# print({'Name': '40-3', 'Address': '46.34.150.163'} in clients)

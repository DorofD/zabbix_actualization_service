import paramiko
import os
import pandas as pd
from services.env_vars import get_var


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
        raise Exception(f'get radius clients error: {error_message}')

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


def add_radius_clients(clients_list):
    conn = get_ssh_connection()
    for client in clients_list:
        stdin, stdout, stderr = conn.exec_command(
            f'New-NpsRadiusClient -Address "{client["Address"]}" -Name "{client["Name"]}" -SharedSecret "{RADIUS_SHARED_SECRET}"')
        error_message = stderr.read().decode('utf-8', errors='ignore')
        if error_message:
            error_message = error_message.replace('\x1b[31;1m', '')
            error_message = error_message.replace('\x1b[0m\r', '')
            raise Exception(f'add radius clients error: {error_message}')
    return True


def remove_radius_clients(clients_list):
    conn = get_ssh_connection()
    for client in clients_list:
        stdin, stdout, stderr = conn.exec_command(
            f'Remove-NpsRadiusClient -Name "{client["Name"]}"')
        error_message = stderr.read().decode('utf-8', errors='ignore')
        if error_message:
            error_message = error_message.replace('\x1b[31;1m', '')
            error_message = error_message.replace('\x1b[0m\r', '')
            raise Exception(f'remove radius clients error: {error_message}')
    return True


def export_radius_clients_xlsx():
    if os.path.exists('export.xlsx'):
        os.remove('export.xlsx')

    clients = get_radius_clients()
    writer = pd.ExcelWriter("export.xlsx")
    data = pd.DataFrame({
        'Address': [client['Address'] for client in clients],
        'Name': [client['Name'] for client in clients],
        'SharedSecret': RADIUS_SHARED_SECRET,
    })
    data.to_excel(writer, 'Sheet1', index=False)
    writer.save()
    return 'export.xlsx'

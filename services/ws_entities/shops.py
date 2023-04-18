import pandas as pd
import re
from models.local_db import *
from models.ws_db import *
import os
from smbclient import shutil
from services.env_vars import get_var
from sys import platform

ZABBIX_USER = get_var('ZABBIX_USER')
ZABBIX_PASSWORD = get_var('ZABBIX_PASSWORD')


def get_shops_from_xls(file):
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
    return shops


def update_shops():
    # получение магазинов в цифрах
    if platform == "linux" or platform == "linux2":
        project_path = str(os.path.join(os.path.dirname(__file__))[0:(os.path.join(
            os.path.dirname(__file__)).index('zabbix_actualization_service') + 29)] + '/shops_in_numbers.xls')
    elif platform == "win32":
        project_path = str(os.path.join(os.path.dirname(__file__))[0:(os.path.join(
            os.path.dirname(__file__)).index('zabbix_actualization_service') + 29)] + 'shops_in_numbers.xls')

    if os.path.exists(project_path + 'shops_in_numbers.xls'):
        os.remove(project_path + 'shops_in_numbers.xls')
    excel_path_from_db = get_excel_path()
    excel_path = project_path + 'shops_in_numbers.xls'
    shutil.copyfile(excel_path_from_db[0][0], excel_path,
                    username='zabbix', password='@WSXzaq1')

    # получение всех магазинов из "Магазинов в цифрах"
    shops_from_xls = get_shops_from_xls(excel_path)
    shops_from_xls_dict = {}
    for i in range(len(shops_from_xls)):
        shops_from_xls_dict[shops_from_xls[i][0]] = shops_from_xls[i]

    # получение списка PIDов из WS
    shops_from_ws = get_shops_from_ws_db()
    pids_from_ws = [shop[0] for shop in shops_from_ws]

    # создание словаря из магазинов в WS
    actual_shop_dict = {}
    for pid in pids_from_ws:
        if pid in shops_from_xls_dict:
            actual_shop_dict[pid] = shops_from_xls_dict[pid]
        else:
            # PID есть в WS, но нет в "Магазинах в цифрах"
            raise Exception(
                f'Shop is missing in WS, but present in XLS file, PID: {pid}')

    # создание словаря магазинов из локальной БД
    shops_from_local_db = get_shops_from_local_db()
    shops_from_local_db_dict = {}
    for i in shops_from_local_db:
        shops_from_local_db_dict[i[0]] = i

    # сортировка магазинов на добавляемые и изменяемые
    shops_to_add = []
    shops_to_update = []
    for pid in actual_shop_dict:
        if pid not in shops_from_local_db_dict:
            shops_to_add.append(actual_shop_dict[pid])
        elif actual_shop_dict[pid] not in shops_from_local_db:
            shops_to_update.append(actual_shop_dict[pid])

    # создание списка PIDов неактуальных магазинов
    pids_to_delete = []
    pids_from_local_db = [shop[0] for shop in get_shops_from_local_db()]
    for pid in pids_from_local_db:
        if pid not in pids_from_ws:
            pids_to_delete.append(pid)

    # добавление отсутствующих магазинов
    if shops_to_add:
        add_shops_to_local_db(shops_to_add)

    # обновление значений измененных магазинов
    if shops_to_update:
        update_shops_from_local_db(shops_to_update)

    # удаление отсутствующих магазинов
    if pids_to_delete:
        delete_shops_from_local_db(pids_to_delete)
    os.remove(project_path + 'shops_in_numbers.xls')
    return True


def update_excel_path(new_excel_path):
    delete_excel_path()
    add_excel_path(new_excel_path)
    return True

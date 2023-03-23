import os
from dotenv import load_dotenv
import pandas as pd
import re
from db_scripts.local_db import *
from db_scripts.ws_db import *

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

EXPORT_XLS_FILE = os.environ['EXPORT_XLS_FILE']


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


def import_shops():
    # получение всех магазинов из "Магазинов в цифрах"
    shops_from_xls = get_shops_from_xls(EXPORT_XLS_FILE)
    shops_from_xls_dict = {}
    for i in range(len(shops_from_xls)):
        shops_from_xls_dict[shops_from_xls[i][0]] = shops_from_xls[i]

    # получение списка PIDов из WS
    shops_from_ws = get_shops_from_ws_db()
    pid_list = []
    for shop in shops_from_ws:
        pid_list.append(shop[0])

    # создание словаря из магазинов в WS
    actual_shop_dict = {}
    for pid in pid_list:
        if pid in shops_from_xls_dict:
            actual_shop_dict[pid] = shops_from_xls_dict[pid]
        else:
            # PID есть в WS, но нет в "Магазинах в цифрах"
            print('Shop not in xls:', pid)

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

    # добавление отсутствующих магазинов
    if shops_to_add:
        add_shops_to_local_db(shops_to_add)

    # обновление значений измененных магазинов
    if shops_to_update:
        update_shops_from_local_db(shops_to_update)

    return True


# import_shops()
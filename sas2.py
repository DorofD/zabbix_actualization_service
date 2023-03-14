import re
import pandas as pd

a = """Пн. - Пт. 09:00-22:00
    Сб. - Вскр. 09:00-21:00"""
difference = 3


def aboba(file):
    try:
        sheet = pd.read_excel(file)
        shops = []
        for i in sheet.index:
            if type(sheet['График работы'][i]) == str:
                temp = re.findall(f'\d\d:\d\d-\d\d:\d\d',
                                  sheet['График работы'][i])
                if temp:
                    work_time = temp[0]
                else:
                    print('Время не найдено')
                    continue
            else:
                continue
            start_stop = re.findall(f'\d\d:\d\d', work_time)

            start_time = pd.to_datetime(start_stop[0], format='%H:%M')
            end_time = pd.to_datetime(start_stop[1], format='%H:%M')

            try:
                dif = pd.Timedelta(hours=int(sheet['Разница во времени'][i]))
                start_time -= dif
                end_time -= dif
            except:
                pass

            off_time = (end_time - start_time)
            # print('Off time:', int(off_time / pd.Timedelta('1 hour')))
            wt = f'{str(start_time)[11:16]}-{str(end_time)[11:16]}'
            # print('WT:', wt)
            shops.append([sheet['PT_ID'][i], sheet['Магазин'][i], wt,
                          24 - int(off_time / pd.Timedelta('1 hour'))])

        return shops

    except Exception as exc:
        print(exc)
        return False


bobas = 'test магазины.xlsx'
bobas = r'\\bookcentre\root\IA_DIVIZION\Public\МАГАЗИНЫ\Магазины в цифрах ЧГ.xls'
sas = aboba(bobas)
# print(sas)
for i in sas:
    print(i)

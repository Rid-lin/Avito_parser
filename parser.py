# -*- coding: utf-8 -*-
import requests
from configparser import ConfigParser
from lxml import html
from openpyxl import load_workbook
import os
from datetime import datetime
from shutil import copyfile


TITLE = ['ID: ', ' Заголовок:', ' Цена:', ' Город размещения:', ' Дата размещения', ' Ссылка на товар: ',
         ' Ссылка на изображение:', 'Описание:']
FPATH = 'storage.xlsx'
conf_file = 'parser.ini'
URL = 'https://www.avito.ru/moskva/noutbuki?q=t430'
PROXY = {'http': 'http://10.57.254.103:8080', 'ftp': 'ftp://10.57.254.103:8080', 'https': 'http://10.57.254.103:8080'}
PAGES = 2
proxy = PROXY


def get_config(conf_file):
    config = ConfigParser()
    config.read(conf_file)
    # http_proxy = config.get('general', 'http_proxy')
    # https_proxy = config.get('general', 'https_proxy')
    url = config.get('general', 'url')
    pages = config.get('general', 'pages')
    backup = config.get('general', 'backup')
    new_file = config.get('general', 'new')
    return url, int(pages), int(backup), int(new_file)


def backup_existing_file(path):
    if os.path.exists(path):
        try:
            copyfile(path,
                     path[:-4] + str(datetime.today())[:16].replace(':', '').replace('-', "").replace(" ", '') + path[
                                                                                                                 -5:])
            print('Делаю бекап существующего файла', path)
        except:
            backup_existing_file(path)


def read_xls(full_filename):
    table = []
    wb = load_workbook(full_filename)
    # print(wb)
    ws = wb.active
    for row in ws.iter_rows():
        table_row = []
        for col in row:
            table_row.append(col.value)
        table.append(table_row)
    print("Файл считан")
    return table


def list_to_dict(project_list):
    project_dict = {}
    for row in project_list:
        project_dict[row[0]] = row[1:]
    return project_dict


def get_html(try_url, proxy, retry=5):
    while retry:
        try:
            response = requests.get(try_url, proxies=proxy)
            print('Получил страницу -', try_url)
            return html.document_fromstring(response.content)
        except:
            print('Не удалось получить страницу по ссылке', try_url, 'Пробую еще раз...')
            retry -= 1
    print('Попытки исчерпаны')
    pass


def get_next_url(url, count):
    try:
        index_sign = url.index('?')
    except ValueError:
        return url + '?p=' + str(count)
    return (url[:index_sign] + '?p=' + str(count) + '&' + url[(index_sign + 1):])


def get_row_table(url, proxy):
    rows_table = []
    doc = get_html(url, proxy)
    if doc is None: pass  # Если страница не получена то выходим с возвратом None
    items = doc.cssselect('div.js-catalog_after-ads .item_table')  # отсекаем всЁ до нужного нам раздела
    i = len(items)
    for item in items:
        id_item = int(item.get('id')[1:])  # узнаём ID товара
        href = 'https://www.avito.ru' + item.cssselect('div.description h3 a')[0].get('href')  # узнаём ссылку на товар
        title = item.cssselect('div.description h3 a')[0].get('title')  # узнаём заголовок объявления
        try:
            src = item.cssselect('div.b-photo a img')[0].get('src')  # узнаём ссылку на картинку для объявления
            if src[:5] != 'http:': src = 'http:' + src
        except:
            src = None

        try:
            price = (item.cssselect('div.description .about')[0].text)  # узнаём цену товара
            price = int(price.replace('\n', '').replace('руб.', '').replace(' ', ''))  # отсекаем лишние символы
        except:
            price = int(str('0'))

        try:
            podrazdel = str(item.cssselect('div.description > div.data > p:nth-child(1)')[0].text)
        except:
            podrazdel = 'Не удалось определить'  # узнаём подраздел или город

        try:
            city = item.cssselect('div.description div.data p:nth-child(2)')[0].text
            # узнаём город в котором продаётся товар
        except:
            city = podrazdel  # город не обнаружен, значит раздела нет,
            # а в переменную для раздела записан город, поэтому присваеваем
            # городу  значение, которое получил раздел,а
            podrazdel = 'Не удалось определить'  # разделу приваеваем значение 'Не удалось определить'

        try:
            # date_item = ''
            date_item = str((item.cssselect('.item_table .data .date')[0].text).replace('\n', '').replace(' ', ''))
            # узнаём дату публикации
            if date_item == None: date_item = ''
        except:
            date_item = ''

        rows_table.append([
            id_item
            , title
            , price
            , city
            , date_item
            , href
            , src
            # , ''
        ])
    return rows_table


def get_table(url, proxy, pages):
    project = []
    print('1.', end='')
    project.extend(get_row_table(url, proxy))
    for i in range(2, pages + 1):
        next_url = get_next_url(url, i)
        page = get_row_table(next_url, proxy)
        print(i, '.', end='')
        if not page: print("Страница пустая. Заканчиваем", '\n')
        project.extend(page)
    return project


def get_description(url, proxy):
    try:
        descripion_item = get_html(url, proxy).cssselect(
            'body > div.item-view-page-layout.item-view-page-layout_content > div.l-content.clearfix > div.item-view > div.item-view-content > div.item-view-left > div.item-view-main.js-item-view-main > div.item-view-block > div > div > p')[
            0].text_content()
    except:
        descripion_item = ''
    return descripion_item


def add_description(new_project, proxy):
    for i in range(len(new_project)):

        try:
            if len(new_project[i][7]) != 0:  continue
        except:
            # print(new_project[i])
            descript = str(get_description(new_project[i][5], proxy))
            new_project[i].append(descript)
        new_project[i][7] = descript
        # print(new_project[i])
    return new_project


def xls_write(project, full_filename):
    # with open(full_filename, 'wb') as wb:
    wb = load_workbook(full_filename)
    ws = wb.active
    for row in range(2, len(project)):
        # Первой и третьей ячейке присваеваем формат числовой
        ws.cell(row=row + 1, column=1).data_type = 'n'
        ws.cell(row=row + 1, column=1).value = project[row][0]
        # второй ячейке присваеваем гиперссылку из 6-ой ячейки
        ws.cell(row=row + 1, column=2).hyperlink = project[row][5]
        ws.cell(row=row + 1, column=2).value = project[row][1]
        # Третьей ячейке присваеваем формат числовой
        ws.cell(row=row + 1, column=3).data_type = 'n'
        ws.cell(row=row + 1, column=3).value = project[row][2]
        #
        ws.cell(row=row + 1, column=4).value = project[row][3]
        #
        ws.cell(row=row + 1, column=5).value = project[row][4]
        #
        ws.cell(row=row + 1, column=6).value = project[row][5]
        #
        ws.cell(row=row + 1, column=7).value = project[row][6]
        #
        ws.cell(row=row + 1, column=8).value = project[row][7]
    wb.save(full_filename)
    print('Файл успешно сохранён!')


def dict_to_list(input_dict):
    dictlist = []
    for key in input_dict:
        tmp = []
        tmp.append(key)
        for i in input_dict[key]:  tmp.append(i)
        dictlist.append(tmp)
    return dictlist


def main():
    path = FPATH
    url, pages, backup_file, new_file = get_config(conf_file)  # print("Прочитали и спарсили конфиг", conf_file)
    old_project = read_xls(path)  # print('Прочитали файл', path)
    # print(old_project)
    try:
        old_project.remove(TITLE)
    except:
        qqq = 'Делать ничего не нужно, т.к. заголовка уже нет.'
    old_table = list_to_dict(old_project)  # print("Преобразовали список в словарь.")
    new_project = get_table(url, proxy, pages)  # print("Получили все необходимые страницы")
    new_table = list_to_dict(new_project)  # print("Преобразовали полученный список в словарь")
    old_table.update(new_table)  # print("Совместили словари, исключив повторения")
    new_project = dict_to_list(old_table)  # print("Преобразовали словарь обратно в список")
    table = add_description(new_project, proxy)
    new_project.insert(0, TITLE)  # print('Добавили заголовок к списку')

    if backup_file:     backup_existing_file(path)
    if new_file:
        os.remove(path)
        copyfile('storage_template.xlsx', path)

    xls_write(table, path)  # print("Записали изменения в файл", path)

    input("Для выхода нажмите Enter")


if __name__ == '__main__':
    main()



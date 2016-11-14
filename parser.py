# -*- coding: utf-8 -*-
import requests
from configparser import ConfigParser
from lxml import html
from openpyxl import load_workbook
import os
from openpyxl.drawing.image import Image

TITLE = ['ID: ', ' Заголовок:', ' Цена:', ' Город размещения:', ' Дата размещения', ' Ссылка на товар: ',
         ' Ссылка на изображение:', 'Путь к локальной картинке']
FPATH = 'storage.xlsx'
conf_file = 'parser.ini'
URL = 'https://www.avito.ru/moskva/noutbuki?q=t430'
PROXY = {'http': 'http://proxy.loc:8080',
         'https': 'http://proxy.loc:8080'}
PAGES = 2
proxy = PROXY


def get_config(conf_file):
    config = ConfigParser()
    config.read(conf_file)
    # http_proxy = config.get('general', 'http_proxy')
    # https_proxy = config.get('general', 'https_proxy')
    url = config.get('general', 'url')
    pages = config.get('general', 'pages')
    return url, int(pages)


def parsing_avito_page(url, proxy):
    rows_table = []

    retry_conn = 5
    # запрашиваем страницу
    try:
        response = requests.get(url, proxies=proxy)
    except Exception:
        print('\n Ошибка соединения. Пробую снова...')
        while not retry_conn:
            retry_conn = - 1
            print('\n Ошибка соединения. Пробую снова...')
            parsing_avito_page(url, proxy)
        print('Соединение не удалось. \n Сохраняю проект.')
        # save(project, 'storage.csv')
        print('Проект сохранён.')
        input('Для выхода нажмите Enter')
        exit()

    # тут я не понял что делаем, но это нужно для дальнейших действий
    doc = html.document_fromstring(response.content)
    items = doc.cssselect('div.js-catalog_after-ads .item_table')  # отсекаем всЁ до нужного нам раздела

    for item in items:

        id_item = (item.get('id')[1:])  # узнаём ID товара
        id_item = int(id_item)

        href = 'https://www.avito.ru' + item.cssselect('div.description h3 a')[0].get('href')  # узнаём ссылку на товар
        title = item.cssselect('div.description h3 a')[0].get('title')  # узнаём заголовок объявления

        try:
            src = item.cssselect('div.b-photo a img')[0].get('src')  # узнаём ссылку на картинку для объявления
            if src[:5] != 'http:': src = 'http:' + src
        except:
            src = None

        try:
            price = (item.cssselect('div.description .about')[0].text)  # узнаём цену товара
            price = price.replace('\n', '').replace('руб.', '').replace(' ', '')  # отсекаем лишние символы
            price = int(price)
        except:
            price = str('0')
            price = int(price)

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
            if date_item == None: date_item = 'Не удалось определить'
        except:
            date_item = 'Не удалось определить'

        rows_table.append([
            id_item
            , title
            , price
            , city
            , date_item
            , href
            , src
        ])
    return rows_table


def get_next_url(url, count):
    try:
        index_sign = url.index('?')
    except ValueError:
        return url + '?p=' + str(count)
    return (url[:index_sign] + '?p=' + str(count) + '&' + url[(index_sign + 1):])


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


def xls_write_with_image(project, full_filename):
    # with open(full_filename, 'wb') as wb:
    wb = load_workbook(full_filename)
    ws = wb.active
    for row in range(2, len(project)):
        cols = len(project[0])
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
        try:
            img = Image(project[row][7])
            img.anchor(ws.cell(row=row + 1, column=1))
        except:
            qqq = '1'
        ws.add_image(img)
    wb.save(full_filename)
    print('Файл успешно сохранён!')


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


def get_table(url, proxy, pages):
    project = []
    for i in range(1, pages + 1):
        page = []
        if i == 1:
            project.extend(parsing_avito_page(url, proxy))
            print("Получена ", i, '-ая страница, по ссылке ', url)
            continue
        next_url = get_next_url(url, i)
        page = parsing_avito_page(next_url, proxy)
        print("Получена ", i, '-ая страница, по ссылке ', next_url)
        if not page:
            print("Страница пустая. Заканчиваем", '\n')
            break
        project.extend(page)
    return project


def dict_to_list(input_dict):
    dictlist = []
    for key in input_dict:
        tmp = []
        tmp.append(key)
        for i in input_dict[key]:  tmp.append(i)
        dictlist.append(tmp)
    return dictlist


def add_loc_img(new_project):
    for i in range(1, len(new_project)):
        if not new_project[i][6]:
            loc_filename = 'img\\No_image.png'
        elif str(new_project[i][6]).find('//') == -1:
            new_project[i][6] = None
            loc_filename = 'img\\No_image.png'
        else:
            loc_filename = 'img\\' + new_project[i][6].replace('http://', '_').replace('//', '_').replace('/',
                                                                                                          '_').replace(
                ':', '_')
        # print(loc_filename)
        try:
            new_project[i][7] = loc_filename
        except IndexError:
            new_project[i].append(loc_filename)


def get_loc_img(new_project, proxy):
    for row in new_project[1:]:
        url = row[6]
        filename = row[7]
        if not (url or filename): continue
        if url == 'None': continue
        if os.path.exists(filename): continue
        if url[:5] != 'http:': url = 'http:' + url
        print('url', url, 'filename', filename)
        r = requests.get(url, proxies=proxy)
        with open(filename, 'wb') as fd:
            fd.write(r.content)


def main():
    path = FPATH
    url, pages = get_config(conf_file)  # print("Прочитали и спарсили конфиг", conf_file)
    old_project = read_xls(path)  # print('Прочитали файл', path)
    print(old_project)
    del_item = ['ID: ', ' Заголовок:', ' Цена:', ' Город размещения:', ' Дата размещения', ' Ссылка на товар: ',
                ' Ссылка на изображение:', 'Путь к локальной картинке']
    try:
        old_project.remove(del_item)
    except:
        qqq = 'Не знаю что тут сделать'
    old_table = list_to_dict(old_project)  # print("Преобразовали список в словарь.")
    print("Получаем страницы по указанной ссылке", url)
    new_project = get_table(url, proxy, pages)  # print('Получили таблицу которую необходимо добавить в наш файл')
    # new_project =

    print("Получили все необходимые страницы")
    new_table = list_to_dict(new_project)  #
    print("Преобразовали полученный список в словарь")
    old_table.update(new_table)  #
    print("Совместили словари, исключив повторения")
    new_project = dict_to_list(old_table)  #
    print("Преобразовали словарь обратно в список")
    new_project.insert(0, TITLE)  #
    print('Добавили заголовок к списку')
    add_loc_img(new_project)
    # get_loc_img(new_project,proxy)
    xls_write(new_project, path)  #
    # xls_write_with_image(new_project, path)  #
    print("Записали изменения в файл", path)
    input("Для выхода нажмите Enter")


if __name__ == '__main__':
    main()

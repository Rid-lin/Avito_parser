# -*- coding: utf-8 -*-
import requests
from configparser import ConfigParser
from lxml import html
from openpyxl import load_workbook
from urllib.request import urlretrieve
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
            if src[:4] != 'http:': src = 'http:' + src
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
    wb = load_workbook(full_filename)
    ws = wb.active
    rows = len(project)
    for row in range(rows):
        cols = len(project[0])
        if row != 0:
            # второй ячейке присваеваем гиперссылку из 6-ой ячейки
            ws.cell(row=row + 1, column=2).hyperlink = project[row][5]
            # Первой и третьей ячейке присваеваем формат числовой
            ws.cell(row=row + 1, column=1).data_type = 'n'
            ws.cell(row=row + 1, column=3).data_type = 'n'
            # x,y = ws.cell(row=row + 1, column=2).anchor
            # try:
            #     img = Image(project[row][6], coordinates=((x, y), (x + 70, y + 53)), size=(0.5, 0.5))
            # except:
            #     img = Image('No_image.png', coordinates=((x, y), (x + 70, y + 53)), size=(0.5, 0.5))
            # ws.add_image(img)
        for col in range(cols):
            ws.cell(row=row + 1, column=col + 1).value = project[row][col]
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
            print(i, '-ая страница, по ссылке ', url)
            continue
        next_url = get_next_url(url, i)
        page = parsing_avito_page(next_url, proxy)
        print(i, '-ая страница, по ссылке ', next_url)
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
    for row in new_project:
        loc_filename = 'img\\' + row[6].replace('http://', '_').replace('//', '_').replace('/', '_').replace(':', '_')
        if row[6]:
            loc_filename = 'img\\No_image.png'
        urlretrieve(row[6], loc_filename)
        row.append(loc_filename)


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
    xls_write(new_project, path)  #
    print("Записали изменения в файл", path)
    input("Для выхода нажмите Enter")


if __name__ == '__main__':
    main()

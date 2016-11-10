# -*- coding: utf-8 -*-
import requests
from configparser import ConfigParser
from lxml import html
import csv
import os

conf_file = 'parser.ini'
URL = 'https://www.avito.ru/moskva/noutbuki?q=t430'
PROXY = {'http': 'http://proxy.loc:8080',
         'https': 'http://proxy.loc:8080'}
PAGES = 2
http_proxy = ''
https_proxy = ''
project = []
items_table = []


def read_conf_file(conf_file):
    config = ConfigParser()
    config.read(conf_file)
    #http_proxy = config.get('general', 'http_proxy')
    #https_proxy = config.get('general', 'https_proxy')
    url = config.get('general', 'url')
    pages = config.get('general', 'pages')
    return http_proxy, https_proxy, url, int(pages)


def get_html(url):
    # запрашиваем страницу
    try:
        response = requests.get(url, proxies=PROXY)
    except Exception:
        print('Connection Error. Save Project')
        save(project, 'storage.csv')
        exit()

    # тут я не понял что делаем, но это нужно для дальнейших действий
    return html.document_fromstring(response.content)


def parsing_page(doc):

    items = doc.cssselect('div.js-catalog_after-ads .item_table')  # отсекаем всЁ до нужного нам раздела

    for item in items:
        id_item = (item.get('id')[1:])  # узнаём ID товара
        href = 'https://www.avito.ru' + item.cssselect('div.description h3 a')[0].get('href')  # узнаём ссылку на товар
        title = item.cssselect('div.description h3 a')[0].get('title')  # узнаём заголовок объявления

        try:
            src = item.cssselect('div.b-photo a img')[0].get('src')  # узнаём ссылку на картинку для объявления
        except:
            src = 'Нет картинки'

        try:
            price = (item.cssselect('div.description .about')[0].text)  # узнаём цену товара
            price = price.replace('\n', '').replace('руб.', '').replace(' ', '')  # отсекаем лишние символы
        except:
            price = str('0')

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

        items_table.append([id_item
                            + ';' + title
                            + ';' + price
                            + ';' + city
                            + ';' + date_item
                            + ';' + href
                            + ';' + src
                            + ';' + podrazdel
                            ])
    return items_table


def prnt_to_screen(table):
    items = table[0]
    for item in items:
        print(item[0])


def save(projects, path):
    # Переименовываем старый файл
    if os.path.exists(path): os.replace(path, path + '.bak')
    try:
        with open(path, 'w') as csvfile:
            writer = csv.writer(csvfile, quoting=csv.QUOTE_NONE, delimiter='|', quotechar='')

            writer.writerow(['ID: ; Заголовок:; Цена:; Город размещения:; Дата размещения; Ссылка на товар: ;'
                             ' Ссылка на изображение:; Подраздел:'])
            # items = projects[0]
            for item in projects:
                writer.writerow(item)
        print('Файл успешно сохранён!')
    except IOError:
        print('Не могу открыть файл storage.csv. Файл может быть заблокирован другой программой')
        if input('Закройте все программы которые могут использовать файл и нажмите Enter чтобы поробовать еще раз.'
                 '(N , Enter - для отмены)') == None: raise
        print('Что-то пошло не так. сохранение не удалось')
    except:
        print('Что-то пошло не так. сохранение не удалось')


def get_next_url(url, count):
    try:
        index_sign = url.index('?')
    except ValueError:
        return url + '?p=' + str(count)
    return (url[:index_sign] + '?p=' + str(count) + '&' + url[(index_sign + 1):])


def main():
    http_proxy, https_proxy, url, pages = read_conf_file(conf_file)
    #print (http_proxy, https_proxy, url, pages)
    print("Page 1 - getting on URL", url)
    html_page = get_html(url)
    print("     ... parsing")
    page = parsing_page(html_page)
    project.extend(page)
    print("     ... Done!", '\n')
    # print('page = ', page)
    # print('project = ', project)
    # print('\n' * 2)
    for i in range(2, pages + 1):
        page.clear()
        next_url = get_next_url(url, i)
        print("Page", i, "getting on URL", next_url)
        html_page = get_html(next_url)
        print("     ... parsing")
        page = parsing_page(html_page)
        if not page:
            print("     ... is blank - no more find pages. Terminate program", '\n')
            break
        project.extend(page)
        print("     ... Done!", '\n')
        # print('page = ', page)
        # print('project = ', project)
        # print('\n'*2)
    save(project, 'storage.csv')


if __name__ == '__main__':
    main()

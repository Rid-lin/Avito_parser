# -*- coding: utf-8 -*-
import requests
from configparser import ConfigParser
from lxml import html
from openpyxl import load_workbook

TITLE = ['ID: ', ' Заголовок:', ' Цена:', ' Город размещения:', ' Дата размещения', ' Ссылка на товар: ',
         ' Ссылка на изображение:', ' Подраздел:']
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
            raise
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

        rows_table.append([
            id_item
            , title
            , price
            , city
            , date_item
            , href
            , src
            , podrazdel
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
        for col in range(cols):
            ws.cell(row=row + 1, column=col + 1).value = project[row][col]
    wb.save(full_filename)
    print('Файл успешно сохранён!')
    # try:
    #     wb = load_workbook(full_filename)
    #     ws = wb.active
    #     rows = len(project)
    #     for row in range(1, rows):
    #         cols = len(project[0])
    #         for col in range(cols):
    #             ws.col(row=row, column=col).value = project[row][col]
    #     wb.save(full_filename)
    #     print('Файл успешно сохранён!')
    # except IOError:
    #     print('Не могу открыть файл storage.csv. Файл может быть заблокирован другой программой')
    #     if input('Закройте все программы которые могут использовать файл и нажмите Enter чтобы поробовать еще раз.'
    #              '(N , Enter - для отмены)') == None: raise
    #     print('Что-то пошло не так. сохранение не удалось. except IOError:')
    # except:
    #     print('Что-то пошло не так. Сохранение не удалось. except')


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
        for i in input_dict[key]: tmp.append(i)
        dictlist.append(tmp)
    return dictlist


def main():
    path = FPATH
    url, pages = get_config(conf_file)  # print("Прочитали и спарсили конфиг", conf_file)
    old_project = read_xls(path)[1:]  # print('Прочитали файл', path)
    old_table = list_to_dict(old_project)  # print("Преобразовали список в словарь.")
    print("Получаем страницы по указанной ссылке", url)
    new_project = get_table(url, proxy, pages)  # получение таблицы которую необходимо добавить в наш файл
    # new_project = [['870158850', 'Мощный Acer LS11HC 17"3 Игровой 4 ядерный в Москве', '12990', 'Компания', 'Сегодня16:31', 'https://www.avito.ru/moskva/noutbuki/moschnyy_acer_ls11hc_173_igrovoy_4_yadernyy_870158850', '//71.img.avito.st/140x105/3156407271.jpg', 'Не удалось определить'], ['870346890', 'Hp Pro core I7 4510 Geforce Nvidia 820 4GB Ram в Москве', '23000', 'м.\xa0Добрынинская', 'Сегодня16:31', 'https://www.avito.ru/moskva/noutbuki/hp_pro_core_i7_4510_geforce_nvidia_820_4gb_ram_870346890', '//36.img.avito.st/140x105/3157134936.jpg', 'Не удалось определить'], ['685644229', 'Ноутбук Dell Latitude E6230 12.5" Corei5/8Gb/320Gb в Москве', '18000', 'м.\xa0Полянка', 'Сегодня16:29', 'https://www.avito.ru/moskva/noutbuki/noutbuk_dell_latitude_e6230_12.5_corei58gb320gb_685644229', '//21.img.avito.st/140x105/2443611321.jpg', 'Компания'], ['870345203', 'Lenovo S 10 - 3S в Москве', '7200', 'Не удалось определить', 'Сегодня16:29', 'https://www.avito.ru/moskva/noutbuki/lenovo_s_10_-_3s_870345203', '//16.img.avito.st/140x105/3157132016.jpg', 'Не удалось определить'], ['833208925', 'Qosmio X300 в Москве', '16000', 'м.\xa0Свиблово', 'Сегодня16:29', 'https://www.avito.ru/moskva/noutbuki/qosmio_x300_833208925', '//02.img.avito.st/140x105/2959871402.jpg', 'Компания'], ['870344251', 'Соврменный новый ноутбук Lenovo 4-х ядерный в Москве', '12900', 'м.\xa0Ботанический сад', 'Сегодня16:27', 'https://www.avito.ru/moskva/noutbuki/sovrmennyy_novyy_noutbuk_lenovo_4-h_yadernyy_870344251', '//49.img.avito.st/140x105/3157129649.jpg', 'Не удалось определить'], ['870344236', 'Ноутбук HP Pavilion DV6 в Москве', '15000', 'м.\xa0Калужская', 'Сегодня16:27', 'https://www.avito.ru/moskva/noutbuki/noutbuk_hp_pavilion_dv6_870344236', '//55.img.avito.st/140x105/3157134755.jpg', 'Не удалось определить'], ['870343725', 'MacBook Pro 13" Retina Early 2015 i5 2.7/SSD 512/8 в Москве', '86000', 'м.\xa0Бауманская', 'Сегодня16:26', 'https://www.avito.ru/moskva/noutbuki/macbook_pro_13_retina_early_2015_i5_2.7ssd_5128_870343725', '//05.img.avito.st/140x105/3157126805.jpg', 'Магазин'], ['870343646', 'Asus zenbook в Москве', '26000', 'м.\xa0Полежаевская', 'Сегодня16:26', 'https://www.avito.ru/moskva/noutbuki/asus_zenbook_870343646', '//25.img.avito.st/140x105/3157129625.jpg', 'Не удалось определить'], ['870343146', 'Игровой MSI (i7+ 8 Гб озу + Geforce GT 750 ) в Москве', '41000', 'м.\xa0Арбатская', 'Сегодня16:25', 'https://www.avito.ru/moskva/noutbuki/igrovoy_msi_i7_8_gb_ozu_geforce_gt_750_870343146', '//96.img.avito.st/140x105/3157127396.jpg', 'Не удалось определить'], ['870343097', 'Игровой танк HP G6 Тянет все - GTA 5, Fild 4 в Москве', '14000', 'м.\xa0ВДНХ', 'Сегодня16:25', 'https://www.avito.ru/moskva/noutbuki/igrovoy_tank_hp_g6_tyanet_vse_-_gta_5_fild_4_870343097', '//95.img.avito.st/140x105/3157125495.jpg', 'Не удалось определить'], ['870342316', 'Ноутбук Acer Aspire E1-531G в Москве', '11000', 'м.\xa0Полежаевская', 'Сегодня16:24', 'https://www.avito.ru/moskva/noutbuki/noutbuk_acer_aspire_e1-531g_870342316', '//61.img.avito.st/140x105/3157124261.jpg', 'Компания'], ['870342097', 'Acer в Москве', '7999', 'м.\xa0Академическая', 'Сегодня16:23', 'https://www.avito.ru/moskva/noutbuki/acer_870342097', '//18.img.avito.st/140x105/3157123618.jpg', 'Не удалось определить'], ['870342076', 'Тонкий бизнес ультрабук Acer в Москве', '12000', 'м.\xa0Алексеевская', 'Сегодня16:23', 'https://www.avito.ru/moskva/noutbuki/tonkiy_biznes_ultrabuk_acer_870342076', '//88.img.avito.st/140x105/3157119088.jpg', 'Не удалось определить'], ['870341528', 'Нетбук Asus Eee PC T101MT 2Gb/320Gb в Москве', '3500', 'м.\xa0Римская', 'Сегодня16:22', 'https://www.avito.ru/moskva/noutbuki/netbuk_asus_eee_pc_t101mt_2gb320gb_870341528', '//09.img.avito.st/140x105/3157112009.jpg', 'None'], ['852619929', 'По всем просьбам Мощный lenovo i5 c тачем, металл в Москве', '32030', 'м.\xa0Дмитровская', 'Сегодня16:21', 'https://www.avito.ru/moskva/noutbuki/po_vsem_prosbam_moschnyy_lenovo_i5_c_tachem_metall_852619929', '//33.img.avito.st/140x105/3073468933.jpg', 'None'], ['870338855', 'Нетбук Asus windows 7 в Москве', '4000', 'м.\xa0Бунинская аллея', 'Сегодня16:18', 'https://www.avito.ru/moskva/noutbuki/netbuk_asus_windows_7_870338855', '//61.img.avito.st/140x105/3157111761.jpg', 'Не удалось определить'], ['669995608', 'Игровые 4-ядерные HP и Acer, Core i5, i3 с гаранти в Москве', '11000', 'Компания', 'Сегодня16:16', 'https://www.avito.ru/moskva/noutbuki/igrovye_4-yadernye_hp_i_acer_core_i5_i3_s_garanti_669995608', '//66.img.avito.st/140x105/2024545066.jpg', 'Не удалось определить'], ['869587622', 'Acer для любой работы geforce Гарантия/Доставка в Москве', '8400', 'м.\xa0Павелецкая', 'Сегодня16:16', 'https://www.avito.ru/moskva/noutbuki/acer_dlya_lyuboy_raboty_geforce_garantiyadostavka_869587622', '//10.img.avito.st/140x105/3154385310.jpg', 'None'], ['869585009', 'Игровой Dell Intel Geforce Гарантия/Доставка в Москве', '13300', 'м.\xa0Павелецкая', 'Сегодня16:16', 'https://www.avito.ru/moskva/noutbuki/igrovoy_dell_intel_geforce_garantiyadostavka_869585009', '//30.img.avito.st/140x105/3154375130.jpg', 'None'], ['869579204', 'Тонкий Acer/Pacard bell 4 ядра 4 гига Гарантия/Дос в Москве', '14400', 'м.\xa0Павелецкая', 'Сегодня16:16', 'https://www.avito.ru/moskva/noutbuki/tonkiy_acerpacard_bell_4_yadra_4_giga_garantiyados_869579204', '//80.img.avito.st/140x105/3154354080.jpg', 'None'], ['870337341', 'Ноутбук dell inspiron 15-3521 в Москве', '14500', 'м.\xa0Славянский бульвар', 'Сегодня16:15', 'https://www.avito.ru/moskva/noutbuki/noutbuk_dell_inspiron_15-3521_870337341', '//60.img.avito.st/140x105/3157104260.jpg', 'Не удалось определить'], ['870335878', 'Ноутбук asus G55VW в Москве', '42000', 'м.\xa0Тушинская', 'Сегодня16:13', 'https://www.avito.ru/moskva/noutbuki/noutbuk_asus_g55vw_870335878', '//47.img.avito.st/140x105/3157089247.jpg', 'Не удалось определить'], ['870335487', 'Emachines e732g в Москве', '10500', 'м.\xa0Павелецкая', 'Сегодня16:12', 'https://www.avito.ru/moskva/noutbuki/emachines_e732g_870335487', '//24.img.avito.st/140x105/3157098624.jpg', 'Не удалось определить'], ['870333963', 'Ноутбук Аsus x750ln(90NB05N1-Мо1520) в Москве', '30000', 'м.\xa0Киевская', 'Сегодня16:09', 'https://www.avito.ru/moskva/noutbuki/noutbuk_asus_x750ln90nb05n1-mo1520_870333963', '//59.img.avito.st/140x105/3157083459.jpg', 'Не удалось определить'], ['870333489', 'Современный, мощный acer 4 ядра в Москве', '12500', 'м.\xa0Арбатская', 'Сегодня16:09', 'https://www.avito.ru/moskva/noutbuki/sovremennyy_moschnyy_acer_4_yadra_870333489', '//34.img.avito.st/140x105/3157094234.jpg', 'Не удалось определить'], ['870333326', 'MacBook Pro 13" Retina Early 2015 i5 2.7/8/SSD 256 в Москве', '79000', 'м.\xa0Бауманская', 'Сегодня16:08', 'https://www.avito.ru/moskva/noutbuki/macbook_pro_13_retina_early_2015_i5_2.78ssd_256_870333326', '//96.img.avito.st/140x105/3157097596.jpg', 'Магазин'], ['870333212', 'Ноутбук Asus x75vc Core i5 2600 мгц в Москве', '19000', 'м.\xa0Киевская', 'Сегодня16:08', 'https://www.avito.ru/moskva/noutbuki/noutbuk_asus_x75vc_core_i5_2600_mgts_870333212', '//72.img.avito.st/140x105/3157088672.jpg', 'Не удалось определить'], ['828788011', 'HP Pavilion 15-N214 A4 1.5Ghz 4Gb 500Gb (гарантия) в Москве', '12990', 'м.\xa0Динамо', 'Сегодня16:08', 'https://www.avito.ru/moskva/noutbuki/hp_pavilion_15-n214_a4_1.5ghz_4gb_500gb_garantiya_828788011', '//36.img.avito.st/140x105/2933932436.jpg', 'None'], ['870333059', 'Dell Precision M4600 I7-2760qm SSD Full HD 8GB RAM в Москве', '32000', 'м.\xa0Юго-Западная', 'Сегодня16:08', 'https://www.avito.ru/moskva/noutbuki/dell_precision_m4600_i7-2760qm_ssd_full_hd_8gb_ram_870333059', '//82.img.avito.st/140x105/3157087182.jpg', 'Не удалось определить'], ['739994926', 'Порт-репликатор Sony vaio VGP-PRS10 в Москве', '3000', 'м.\xa0Речной вокзал', 'Сегодня16:06', 'https://www.avito.ru/moskva/noutbuki/port-replikator_sony_vaio_vgp-prs10_739994926', '//17.img.avito.st/140x105/2355289117.jpg', 'Компания'], ['852600416', 'HP EliteBook 820 G2 i5 5300U 2.3GHz/8GB/256GB SSD в Москве', '46000', 'м.\xa0Молодежная', 'Сегодня16:06', 'https://www.avito.ru/moskva/noutbuki/hp_elitebook_820_g2_i5_5300u_2.3ghz8gb256gb_ssd_852600416', '//94.img.avito.st/140x105/3155542894.jpg', 'Не удалось определить'], ['870331700', 'Acer aspire 5733z в Москве', '10000', 'м.\xa0Выхино', 'Сегодня16:05', 'https://www.avito.ru/moskva/noutbuki/acer_aspire_5733z_870331700', '//01.img.avito.st/140x105/3157084701.jpg', 'Компания'], ['852572133', 'Всем нужен Medion 15.6" c видео nvgt740M в Москве', '19520', 'м.\xa0Дмитровская', 'Сегодня16:05', 'https://www.avito.ru/moskva/noutbuki/vsem_nuzhen_medion_15.6_c_video_nvgt740m_852572133', '//58.img.avito.st/140x105/3073185758.jpg', 'None'], ['870330529', 'MacBook Air 13 в Москве', '38000', 'м.\xa0Сокол', 'Сегодня16:03', 'https://www.avito.ru/moskva/noutbuki/macbook_air_13_870330529', '//14.img.avito.st/140x105/3157080514.jpg', 'Не удалось определить'], ['870330321', 'Hp envi DV 6 core i7 HD4000/GiForce GT635m в Москве', '24000', 'м.\xa0Алтуфьево', 'Сегодня16:03', 'https://www.avito.ru/moskva/noutbuki/hp_envi_dv_6_core_i7_hd4000giforce_gt635m_870330321', '//47.img.avito.st/140x105/3157077547.jpg', 'Не удалось определить'], ['870330254', 'Новый Тошиба 15.6"i3 3gb зарядка сумочка в Москве', '14000', 'м.\xa0Китай-город', 'Сегодня16:03', 'https://www.avito.ru/moskva/noutbuki/novyy_toshiba_15.6i3_3gb_zaryadka_sumochka_870330254', '//59.img.avito.st/140x105/3157084559.jpg', 'Не удалось определить'], ['870329832', 'Ультрабук Lenovo u310 в Москве', '11000', 'м.\xa0Калужская', 'Сегодня16:02', 'https://www.avito.ru/moskva/noutbuki/ultrabuk_lenovo_u310_870329832', '//94.img.avito.st/140x105/3157076194.jpg', 'Компания'], ['837497576', '10" Нетбук Asus 2 ядра/1Gb/160Gb/WiFI/Камера в Москве', '4900', 'м.\xa0Сходненская', 'Сегодня16:02', 'https://www.avito.ru/moskva/noutbuki/10_netbuk_asus_2_yadra1gb160gbwifikamera_837497576', '//45.img.avito.st/140x105/3139663345.jpg', 'Магазин'], ['870329426', 'Ноутбук Ультра игровой Нр 15.6"i7 6gb 640gb сумка в Москве', '23000', 'м.\xa0Автозаводская', 'Сегодня16:01', 'https://www.avito.ru/moskva/noutbuki/noutbuk_ultra_igrovoy_nr_15.6i7_6gb_640gb_sumka_870329426', '//36.img.avito.st/140x105/3157086136.jpg', 'Не удалось определить'], ['870329408', 'HP dv6 15.6" 2ядра 2GHz видео 1.8гб новый аккум в Москве', '8500', 'м.\xa0Динамо', 'Сегодня16:01', 'https://www.avito.ru/moskva/noutbuki/hp_dv6_15.6_2yadra_2ghz_video_1.8gb_novyy_akkum_870329408', '//69.img.avito.st/140x105/3157070269.jpg', 'Не удалось определить'], ['870329283', 'Нaдeжный Acer 2гига в отличном виде в Москве', '5000', 'м.\xa0Щелковская', 'Сегодня16:01', 'https://www.avito.ru/moskva/noutbuki/nadezhnyy_acer_2giga_v_otlichnom_vide_870329283', '//94.img.avito.st/140x105/3157075094.jpg', 'Не удалось определить'], ['870329150', 'Продам ноутбук в Москве', '5000', 'м.\xa0Юго-Западная', 'Сегодня16:00', 'https://www.avito.ru/moskva/noutbuki/prodam_noutbuk_870329150', '//03.img.avito.st/140x105/3157075303.jpg', 'Не удалось определить'], ['852609166', 'Игровой ноутбук Cонька SVE1511V1R в Москве', '21200', 'м.\xa0Севастопольская', 'Сегодня16:00', 'https://www.avito.ru/moskva/noutbuki/igrovoy_noutbuk_conka_sve1511v1r_852609166', '//01.img.avito.st/140x105/3073400501.jpg', 'Компания']]
    print("Получили все нужные страницы и вытащили из них данные")
    new_table = list_to_dict(new_project)  # print("Преобразовали полученный список в словарь")
    old_table.update(new_table)  # print("Совместили словари, исключив повторения")
    new_project = dict_to_list(old_table)  # print("Преобразовали словарь обратно в список")
    new_project.insert(0, TITLE)  # добавляем заголовок к списку
    xls_write(new_project, path)  # print("Записали изменения в файл", path)
    input("Для выхода нажмите Enter")


if __name__ == '__main__':
    main()

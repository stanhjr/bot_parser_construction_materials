import asyncio
import requests
from bs4 import BeautifulSoup

from parser_magazine.tools import format_text
from parser_magazine.work_excel_file import get_link_epicenter, set_price_to_book


async def get_text_epicenter(url):
    session_epicenter = requests.Session()
    data = {
        "cityId": 6634,
        "ID": 54,
        "ADDRESS": "Петриковский район, с. Елизаветовка, 14-й км дороги Каменское — Петриковка — Магдалиновка, 1{lang}Петриківський район, с. Єлизаветівка, 14-й км дороги Кам’янське — Петриківка — Магдалинівка, 1",
        "LOCATION_ID": 6631,
        "DESCRIPTION": "ТЦ «Эпицентр»{lang}ТЦ «Епіцентр»",
        "STORE": "Y",
        "AJAX": "Y",
        "VUE": "Y",
        "CHECKOUT": "Y",
        "SAVE": "N"
    }
    session_epicenter.post('https://epicentrk.ua/ajax/set_location.php', data=data)
    response = session_epicenter.get(url)

    if response is None:
        return url
    if response.status_code == 404:
        return ''

    selector = '#MAIN > div > div.p-block__row.p-block__row--price > div > div'
    soup = BeautifulSoup(response.text, "lxml")
    elem = soup.select(selector=selector)
    return elem[0].text


def set_cell_epicenter(last_row, original_file, copy_file):
    list_link = get_link_epicenter(last_row, original_file)
    for url, cell in list_link:
        try:
            text = get_text_epicenter(url)
            set_price_to_book(address=cell, price=text, file_path=copy_file)

        except AttributeError as e:
            print(e)
            print(url)
        except IndexError:
            text = ''
            set_price_to_book(address=cell, price=text, file_path=copy_file)


async def get_page_epik(url, cell, copy_file):
    try:
        text = await get_text_epicenter(url)
        text = format_text(text)
        set_price_to_book(address=cell, price=text, file_path=copy_file)

    except AttributeError as e:
        print(e)
        print(url)
    except IndexError:
        text = ''
        set_price_to_book(address=cell, price=text, file_path=copy_file)


async def parser_epicenter(last_row, copy_file, original_file):
    tasks = []
    list_link = await get_link_epicenter(last_row, original_file)
    for url, cell in list_link:
        task = asyncio.create_task(get_page_epik(url, cell, copy_file))

        tasks.append(task)

    await asyncio.gather(*tasks)
    return True


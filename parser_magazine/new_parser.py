import os
import shutil
import time
import io
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import asyncio
import aiohttp

from parser_magazine.epicenter import parser_epicenter
from parser_magazine.tools import SELECTOR_DICT, get_price, format_text
from parser_magazine.work_excel_file import find_last_row_excel, set_price_to_book, get_all_link_market, markup_excel_file
import encodings

encodings.aliases.aliases['cp_1251'] = 'cp1251'

sema = asyncio.BoundedSemaphore(5)


async def get_page_data(session, url, cell, key_selector, copy_file):
    ua = UserAgent()
    try:
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'User-Agent': ua.random,
            "Cookie": 'ymex=1962878606.yrts.1647518606#1962878606.yrtsi.1647518606; yandexuid=7334774781647518606; yuidss=7334774781647518606; i=QKr00Nm/0UePVn1eR2akaV7LfpJPzm2XBoDpHkoz7rvA4S8ceQ+5edhvhD536K6bWxGSx9btEMzxYa4C0yl4wxKZ5VM=; is_gdpr=0; is_gdpr_b=CLfGQxD7aA==; yabs-sid=2459537251652003522',
        }

    except IndexError:
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'User-Agent': ua.random
        }

    counter_except = 0
    counter_none = 0
    for proxy in range(4):
        try:
            async with session.get(url=url, headers=headers, allow_redirects=True, timeout=30) as response:
                selector = SELECTOR_DICT.get(key_selector)

                if key_selector == 'J':
                    response_text = await response.text(encoding='ISO-8859-1')
                else:
                    html = await response.text()
                    buffer = io.BufferedReader(io.BytesIO(html.encode("utf-8")))
                    text_wrapper = io.TextIOWrapper(buffer)
                    response_text = text_wrapper.read()

                if response.status == 404:
                    set_price_to_book(address=cell, price='', file_path=copy_file)
                    return

                if response is None:
                    set_price_to_book(address=cell, price='', file_path=copy_file)
                    counter_none += 1
                    return

                if response_text:
                    text = get_price(response_text, key_selector, cell, copy_file)

                    if not text:
                        soup = BeautifulSoup(response_text, "lxml")
                        elem = soup.select(selector=selector)
                        text = elem[0].text

                    text = text.strip()
                    text = text.strip()
                    text = text.strip()
                    if key_selector == 'J':
                        text = bytes(text, 'iso-8859-1').decode('utf-8')
                    text = format_text(text)
                    print(cell, text)
                    set_price_to_book(address=cell, price=text, file_path=copy_file)
                    return

        except aiohttp.ServerDisconnectedError as e:
            print(e, cell, counter_except)
            counter_except += 1
            await asyncio.sleep(4)
            if counter_except == 3:
                set_price_to_book(address=cell, price='', file_path=copy_file)
            continue

        except IndexError:
            set_price_to_book(address=cell, price='', file_path=copy_file)
            break

        except asyncio.TimeoutError as e:
            counter_except += 1
            await asyncio.sleep(4)
            if counter_except == 3:
                set_price_to_book(address=cell, price='', file_path=copy_file)
            continue
        except Exception as e:
            print(e)
            set_price_to_book(address=cell, price='', file_path=copy_file)
            break


async def parser(copy_file, first_row, last_row, all_data):
    connector = aiohttp.TCPConnector(limit=5)

    try:
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = []

            for url, cell, key_selector in all_data[first_row:last_row]:
                print(cell, key_selector)

                if url is None:
                    continue
                if key_selector == 'L':
                    continue
                if key_selector == 'G':
                    continue
                task = asyncio.create_task(get_page_data(session, url, cell, key_selector, copy_file))
                tasks.append(task)

            await asyncio.gather(*tasks)
            return first_row, last_row
    except aiohttp.ServerDisconnectedError as e:
        print(e)


async def all_parsing():
    try:

        shutil.copy('database.xlsx', 'temp/database_result.xlsx')
        shutil.copy('database.xlsx', 'temp/database_work.xlsx')
        original_file = "temp/database_work.xlsx"
        copy_file = "temp/database_result.xlsx"

        number_of_iterations, last_row = await find_last_row_excel(file_path=original_file)
        all_data = get_all_link_market(last_row=last_row, file_path=original_file)
        first_row_row_in_one_parse = 0
        last_row_in_one_parse = 80
        number_of_run = number_of_iterations // last_row_in_one_parse

        if number_of_iterations % number_of_run != 0:
            number_of_run += 1

        for i in range(number_of_run):

            first_row_row_in_one_parse, last_row_in_one_parse = await parser(copy_file=copy_file,
                                                                             first_row=first_row_row_in_one_parse,
                                                                             last_row=last_row_in_one_parse,
                                                                             all_data=all_data)

            time.sleep(3)
            first_row_row_in_one_parse += 80
            last_row_in_one_parse += 80

        await parser_epicenter(last_row=last_row, original_file=original_file, copy_file=copy_file)

        markup_excel_file(copy_file, last_row)
        if os.path.exists('tables/database_result.xlsx'):
            os.remove('tables/database_result.xlsx')
        shutil.copy(copy_file, 'tables/database_result.xlsx')
        os.remove(copy_file)
    except Exception as e:
        print(e)


if __name__ == "__main__":
    markup_excel_file('../tables/database_result.xlsx', 80)
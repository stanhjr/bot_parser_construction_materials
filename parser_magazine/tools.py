from bs4 import BeautifulSoup

from parser_magazine.work_excel_file import set_price_to_book

SELECTOR_DICT = {
    'D': '#prices > div > div > div.card-body.py-3.px-4 > dl > dd:nth-child(2)',
    'E': '#prices > div > div > div.card-body.py-3.px-4 > dl > dd:nth-child(4)',
    'F': '#content > div > div.col-md-5.col-sm-7.col-xs-6.col-50 > div.area-1 > div.price-block > ul > li:nth-child(2) > h2 > span.autocalc-product-special',
    'H': '#main > div.pc-product-single__summary-wrapper > div.pc-product-single__summary > div > div.pc-product-summary__body > div.pc-product-purchase > div.pc-product-purchase__header > div.product-price.product-price--lg > span',
    'I': '#main > div.pc-product-single__summary-wrapper > div.pc-product-single__summary > div > div.pc-product-summary__body > div.pc-product-purchase > div.pc-product-purchase__header > div.product-price--wholesale > div > span',
    'J': '#price',
    'K': '#price_base',
    'L': '#MAIN > div > div.p-block__row.p-block__row--price > div > div',
    'M': '#main-product-price',
    'N': '#fix_right_block > div.panel.panel-default.panel-body > div.price > span',
    'O': '#main > div.pc-product-single__summary-wrapper > div.pc-product-single__summary > div > div.pc-product-summary__body > div > div.pc-product-purchase__header > div > span',
    'P': 'body > main > article > div.cs-page__main-content > div.cs-product.js-productad > div.cs-product__info-row > div.cs-product__wholesale-price.cs-online-edit > div > p > span:nth-child(1)',
    'Q': '#body_text > div.catalog-detail > table > tbody > tr > td:nth-child(2) > div.price_buy_detail > div.catalog-detail-price > span.catalog-detail-item-price',
    'R': '#material > div.matLboxing.productCase-3471 > div.contentCase > div.productGcase > div.priceBox > span > span.price'
}


def get_price(page_text, liter_key, cell, copy_file):
    elem = None
    soup = BeautifulSoup(page_text, "lxml")
    if liter_key == 'D':
        elem = soup.find('span', class_='product-cat-price-current')

    if liter_key == 'Q':
        elem = soup.find('span', class_='catalog-detail-item-price')

    if liter_key == 'F':
        selector = '#content > div > div.col-md-5.col-sm-7.col-xs-6.col-50 > div.area-1 > div.price-block > ul > li:nth-child(2) > h2 > span.autocalc-product-special'
        elem = soup.select(selector=selector)
        elem = elem[0]

        old_price = soup.find('span', class_='old_price')

        if old_price:
            old_price = old_price.text
            text = old_price.strip()
            text = text.strip()
            text = text.strip()
            text = format_text(text)
            cell = 'G' + cell[1:]
            set_price_to_book(address=cell, price=text, file_path=copy_file)

    if liter_key == 'O':
        parent_block = soup.find('div', class_="product-price product-price--lg")
        elem_2 = parent_block.find_all('span', class_='woocommerce-Price-amount amount')
        if len(elem_2) == 2:
            elem = elem_2[1]
        else:
            elem = parent_block.find('span', class_='woocommerce-Price-amount amount')

    if liter_key == 'R':
        elem = soup.find('span', class_='price')

    if elem:
        return elem.text


def format_text(text):
    text = text.replace(' ', '')
    for symbol in text:
        if symbol.isalpha() or symbol == '/':
            text = text.replace(symbol, '')
    if text[-1] == '.':
        text = text[:len(text) - 1]
    text = text.replace(',', '.')
    text = text.replace('\n', '')
    text = text.replace('\t', '')
    text = text.replace(':', '')
    text = text.replace(';', '')
    return text


async def edit_message(chat_id, msg_id, text):
    from bot import bot
    await bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=text)


last_count = 1

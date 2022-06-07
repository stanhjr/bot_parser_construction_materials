from telethon import TelegramClient
from datetime import datetime
import time
import glob
import logging

import asyncio

from utils import get_user_groups

from handler import get_all_products

from config import API_ID, API_HASH, BOT_TOKEN, users, MEDIA_DIR

logging.basicConfig(filename=f"logs/AUTO_{datetime.now().strftime('%Y-%m-%d %H-%M')}.log", level="WARNING")


async def main():
    if True:
        bot.parse_mode = 'html'
        products = await get_all_products()
        if products:
            messages = {}
            curmsgs = {}
            for obj in products:
                if not obj.get('roz') and not obj.get('opt'):
                    continue

                if not messages.get(obj['group']):
                    messages[obj['group']] = []

                if not curmsgs.get(obj['group']):
                    curmsgs[obj['group']] = f'⏰ {datetime.now().strftime("%d/%m/%Y %H:%M")}\n'

                msg = f'\nГруппа товара: <b>{obj["group"]}</b>' \
                      f'\nНазвание товара: <b>{obj["product"]}</b>' \
                      f'\n<a href=\"{obj["roz"]["link"]}\">Наша розница:</a> <b>{obj["roz"]["price"]} грн.</b>' \
                      f'\n<a href=\"{obj["opt"]["link"]}\">Наш опт:</a> <b>{obj["opt"]["price"]} грн.</b>\n\n'
                conc = ''

                for key, value in obj.items():
                    if key not in ['group', 'product', 'roz', 'opt', 'image']:
                        prc = ''
                        roz = obj[key].get('roz')
                        opt = obj[key].get('opt')
                        if roz:
                            if roz.get('price'):
                                if obj['roz']['price'] == roz['price']:
                                    prc += f'<a href=\"{roz.get("link")}\">' \
                                           f'Розничная цена:</a> ⬜ <b>{roz["price"]} грн.</b>\n'
                                elif obj['roz']['price'] < roz['price']:
                                    prc += f'<a href=\"{roz.get("link")}\">' \
                                           f'Розничная цена:</a> 🟩 <b>{roz["price"]} грн.</b>\n'
                                else:
                                    prc += f'<a href=\"{roz.get("link")}\">' \
                                           f'Розничная цена:</a> 🟥 <b>{roz["price"]} грн.</b>\n'
                        if opt:
                            if opt.get('price'):
                                if obj['opt']['price'] == opt['price']:
                                    prc += f'<a href=\"{opt.get("link")}\">' \
                                           f'Оптовая цена:</a> ⬜ <b>{opt["price"]} грн.</b>\n'
                                elif obj['opt']['price'] < opt['price']:
                                    prc += f'<a href=\"{opt.get("link")}\">' \
                                           f'Оптовая цена:</a> 🟩 <b>{opt["price"]} грн.</b>\n'
                                else:
                                    prc += f'<a href=\"{opt.get("link")}\">' \
                                           f'Оптовая цена:</a> 🟥 <b>{opt["price"]} грн.</b>\n'
                        if len(prc) != 0:
                            conc += f'Сайт: {key}\n' + prc
                if not conc:
                    msg += 'Цены конкурентов не обнаружены.'
                else:
                    msg += conc

                if len(messages[obj["group"]]) == 0 and \
                        glob.glob(MEDIA_DIR + obj["group"] + '.jpg') and \
                        len(msg) + len(curmsgs[obj['group']]) > 2048 or \
                        len(msg) + len(curmsgs[obj['group']]) > 10000:
                    messages[obj["group"]].append(curmsgs[obj['group']])
                    curmsgs.pop(obj['group'])
                    curmsgs[obj['group']] = msg
                else:
                    curmsgs[obj['group']] += msg

            for key, value in curmsgs.items():
                messages[key].append(value)

            for user in users:
                groups = get_user_groups(user)
                for name, msglist in messages.items():
                    if not groups:
                        if glob.glob(MEDIA_DIR + name + '.jpg'):
                            await bot.send_message(entity=user, message=msglist[0], file=MEDIA_DIR + name + '.jpg',
                                                   link_preview=False, parse_mode="html")
                            msglist.pop(0)
                        for message in msglist:
                            await bot.send_message(entity=user, message=message, link_preview=False, parse_mode="html")
                            time.sleep(0.5)
                    elif name in groups:
                        if glob.glob(MEDIA_DIR + name + '.jpg'):
                            await bot.send_message(entity=user, message=msglist[0], file=MEDIA_DIR + name + '.jpg',
                                                   link_preview=False, parse_mode="html")
                            msglist.pop(0)
                        for message in msglist:
                            print(message)
                            await bot.send_message(entity=user, message=message, link_preview=False, parse_mode="html")
                            time.sleep(0.5)
            logging.info('Bot successfully finished.')
            await bot.disconnect()


bot = TelegramClient("bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)
if bot:
    logging.info('Bot successfully started.')
    asyncio.get_event_loop().run_until_complete(main())
else:
    logging.info('Could not start bot.')

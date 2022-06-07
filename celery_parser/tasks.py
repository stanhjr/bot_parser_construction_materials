import asyncio
import shutil
import os

from celery import Celery

from parser_magazine.new_parser import all_parsing

celery_app = Celery(
    "tasks",
    broker="redis://localhost:6379/5"
)


@celery_app.task
def add_table():
    shutil.copy('temp/database.xlsx', 'database.xlsx')
    os.remove('temp/database.xlsx')
    coro = all_parsing()
    return asyncio.run(coro)


@celery_app.task
def regular_parsing():
    if os.path.exists("temp/database_result.xlsx"):
        print("Пропускаю парсинг, сейчас выполняется другая очередь")
        return "Пропускаю парсинг, сейчас выполняется другая очередь"

    coro = all_parsing()
    return asyncio.run(coro)

# /home/stan/BOTS/stroy_bot_new/venv/bin/celery --app=celery_parser.tasks worker --loglevel=INFO



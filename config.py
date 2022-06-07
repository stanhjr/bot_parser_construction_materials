import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('TOKEN')
BOT_NICKNAME = os.getenv('BOT_NICKNAME')

TABLES_DIR = "tables/"
DATABASE_DIR = "database.xlsx"
MEDIA_DIR = "images/"
API_ID = 2090076
API_HASH = "5ddf576a361987bdffc6419a4aee4222"
users = ['dmsizov']

DATABASE_URL = f'postgresql://stan:stan@localhost:5432/bot_stroy'


import glob
import json
import os

import pandas as pd

from config import TABLES_DIR


class Pagination(object):
    def __init__(self, message_id, objects, size):
        self.message_id = message_id
        self.objects = objects
        self.page = 1
        self.size = size

    async def count(self):
        if len(self.objects) % self.size == 0:
            return len(self.objects) // self.size
        else:
            return len(self.objects) // self.size + 1

    async def get(self):
        return self.objects[self.size * (self.page - 1):self.size * self.page]

    async def next_page(self):
        self.page += 1
        return self.objects[self.size * (self.page - 1):self.size * self.page]

    async def previous_page(self):
        self.page -= 1
        return self.objects[self.size * (self.page - 1):self.size * self.page]


async def get_table():
    files = glob.glob(f'{TABLES_DIR}*.xlsx')
    tab = max(files, key=os.path.getctime)
    df = pd.read_excel(tab).fillna(0)
    for colname, col in df.items():
        for j in range(len(col)):
            if colname not in ['Группа товаров', 'URL картинки', 'товар']:
                if type(col[j]) is str:
                    try:
                        df.loc[j, colname] = float(col[j])
                    except ValueError:
                        df.loc[j, colname] = 0.0
            elif colname == 'URL картинки':
                if not col[j]:
                    df.loc[j, colname] = None
    return df


async def get_groups(df):
    groups = []
    for i in df['Группа товаров']:
        if i not in groups:
            groups.append(i)
    return groups


async def get_products(table, groups):
    products = []
    for index, row in table.iterrows():
        if row[0] in groups:
            products.append(row[2])
    return products


def get_data() -> dict:
    with open("data.json", "r") as f:
        return json.loads(f.read())


def save_data(data: dict):
    with open("data.json", "w") as f:
        f.write(json.dumps(data))


def get_access():
    return get_data()["access"]


def get_admins():
    return get_data()['admins']


def set_admin(cid):
    with open("data.json", 'r') as f:
        data = json.loads(f.read())
        f.close()
    with open("data.json", 'w') as f:
        data['admins'].append(cid)
        f.write(json.dumps(data))
        f.close()


def get_lsid():
    return get_data()['lsid']


def set_lsid(lsid):
    with open("data.json", 'r') as f:
        data = json.loads(f.read())
        f.close()
    with open("data.json", 'w') as f:
        data['lsid'] = lsid
        f.write(json.dumps(data))
        f.close()


def set_access(cid):
    with open("data.json", 'r') as f:
        data = json.loads(f.read())
        f.close()
    with open("data.json", 'w') as f:
        data['access'].append(cid)
        f.write(json.dumps(data))
        f.close()


def get_user_groups(username: str):
    return get_data()['usergroups'].get(username)


def set_user_groups(username: str, groups):
    data = get_data()
    data['usergroups'][username] = groups
    return save_data(data)

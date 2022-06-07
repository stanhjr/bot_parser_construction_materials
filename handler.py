import copy
import pandas as pd

from utils import get_table

from config import DATABASE_DIR


async def get_by_groups(table, groups):
    items = {}
    inds = []
    for colname, col in table.items():
        if colname not in ['Группа товаров', 'URL картинки', 'товар', 'цена', 'rems.market opt']:
            inds.append(colname)
    for ind in inds:
        if items.get(ind.split()[0]) is None:
            items[ind.split()[0]] = {}
        if ind.split()[1] == 'opt':
            items[ind.split()[0]]['opt'] = table.columns.get_loc(ind)
        else:
            items[ind.split()[0]]['roz'] = table.columns.get_loc(ind)
    output = []
    db = pd.read_excel(DATABASE_DIR).fillna(0)
    for index, row in table.iterrows():
        if row[0] in groups:
            out = copy.deepcopy(items)
            for key, value in out.items():
                if out[key].get('opt'):

                    out[key]['opt'] = {'price': row[out[key].get('opt')], 'link': db.loc[index, inds[out[key].get('opt') - 5]]}
                if out[key].get('roz'):
                    out[key]['roz'] = {'price': row[out[key].get('roz')], 'link': db.loc[index, inds[out[key].get('roz') - 5]]}
            out['group'] = row[0]
            out['image'] = db.loc[index, 'URL картинки']
            out['product'] = row[2]
            out['roz'] = {'price': row[3], 'link': db.loc[index, 'цена']}
            out['opt'] = {'price': row[4], 'link': db.loc[index, 'rems.market opt']}
            output.append(out)
    return output


async def get_by_products(table, groups, products):
    items = {}
    inds = []
    for colname, col in table.items():
        if colname not in ['Группа товаров', 'URL картинки', 'товар', 'цена', 'rems.market opt']:
            inds.append(colname)
    for ind in inds:
        if items.get(ind.split()[0]) is None:
            items[ind.split()[0]] = {}
        if ind.split()[1] == 'opt':
            items[ind.split()[0]]['opt'] = table.columns.get_loc(ind)
        else:
            items[ind.split()[0]]['roz'] = table.columns.get_loc(ind)
    output = []
    db = pd.read_excel(DATABASE_DIR).fillna(0)
    for index, row in table.iterrows():
        if row[0] in groups:
            if row[2] in products:
                out = copy.deepcopy(items)
                for key, value in out.items():
                    if out[key].get('opt'):
                        out[key]['opt'] = {'price': row[out[key].get('opt')],
                                           'link': db.loc[index, inds[out[key].get('opt') - 5]]}
                    if out[key].get('roz'):
                        out[key]['roz'] = {'price': row[out[key].get('roz')],
                                           'link': db.loc[index, inds[out[key].get('roz') - 5]]}
                out['group'] = row[0]
                out['image'] = db.loc[index, 'URL картинки']
                out['product'] = row[2]
                out['roz'] = {'price': row[3], 'link': db.loc[index, 'цена']}
                out['opt'] = {'price': row[4], 'link': db.loc[index, 'rems.market opt']}
                output.append(out)
    return output


async def get_all_products():
    table = await get_table()
    items = {}
    inds = []
    for colname, col in table.items():
        if colname not in ['Группа товаров', 'URL картинки', 'товар', 'цена', 'rems.market opt']:
            inds.append(colname)
    for ind in inds:
        if items.get(ind.split()[0]) is None:
            items[ind.split()[0]] = {}
        if ind.split()[1] == 'opt':
            items[ind.split()[0]]['opt'] = table.columns.get_loc(ind)
        else:
            items[ind.split()[0]]['roz'] = table.columns.get_loc(ind)
    output = []
    db = pd.read_excel(DATABASE_DIR).fillna(0)
    for index, row in table.iterrows():
        out = copy.deepcopy(items)
        for key, value in out.items():
            if out[key].get('opt'):
                out[key]['opt'] = {'price': row[out[key].get('opt')],
                                   'link': db.loc[index, inds[out[key].get('opt') - 5]]}
            if out[key].get('roz'):
                out[key]['roz'] = {'price': row[out[key].get('roz')],
                                   'link': db.loc[index, inds[out[key].get('roz') - 5]]}
        out['group'] = row[0]
        out['product'] = row[2]
        out['roz'] = {'price': row[3], 'link': db.loc[index, 'цена']}
        out['opt'] = {'price': row[4], 'link': db.loc[index, 'rems.market opt']}
        output.append(out)
    return output
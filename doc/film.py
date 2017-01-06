# -*- coding: utf-8 -*-
import os
import re
import sys
import time
import json
import logging

import xlrd
import xlwt
import xlutils
from xlutils.copy import copy

reload(sys)
sys.setdefaultencoding('utf8')

g_star_list = {}
g_star_to_film = {}
g_role_to_film = {}

type = sys.getfilesystemencoding()

def film_name(text):
    idx = 0
    split = re.split(r"《", text.encode("utf-8"))
    for item in split:
        if 0 == idx % 2:
            idx += 1
            continue
        idx += 1
        name = re.split(r"》", item)
        if name is None:
            return item
        return name[0]
    return text

# 加载明星列表
def load_star(path):
    global g_star_list

    f = file("star.json")
    data = json.load(f)
    for item in data:
        if 0 != item["id"]:
            if len(item["name"]):
                g_star_list[item["id"]] = item["name"]
                #print("id:%d %s" % (item["id"], item["name"]))
    return g_star_list

# 加载电影信息
def load_film(path):
    global g_star_list
    global g_star_to_film
    global g_role_to_film

    f = file("film.json")
    data = json.load(f)
    for item in data:
        # 构造"明星 -> 电影"映射
        if len(item["starring"]):
            if len(item["name_cn"]):
                stars = item["starring"].split(",")
                for star in stars:
                    if 0 == len(star):
                        continue
                    star_id = int(star)
                    if g_star_list.has_key(star_id):
                        name = g_star_list[star_id]
                        if g_star_to_film.has_key(name):
                            g_star_to_film[name][film_name(item["name_cn"])] = 1
                            continue
                        g_star_to_film[name] = {}
                        g_star_to_film[name][film_name(item["name_cn"])] = 1
                        #print("name:%s film:%s" % (name, film_name(item["name_cn"])))
        # 构造"角色 -> 电影"映射
        if len(item["starring_play"]):
            if len(item["name_cn"]):
                roles = item["starring_play"].split(",")
                for role in roles:
                    if len(role):
                        if g_role_to_film.has_key(role):
                            print("role:%s film:%s" % (role, film_name(item["name_cn"])))
                            g_role_to_film[role][film_name(item["name_cn"])] = 1
                            continue
                        g_role_to_film[role] = {}
                        g_role_to_film[role][film_name(item["name_cn"])] = 1

def film_list_by_star(star):
    global g_star_list
    global g_star_to_film
    global g_role_to_film

    if g_star_to_film.has_key(star):
        return g_star_to_film[star].keys()
    return {}

def film_list_by_role(role):
    global g_star_list
    global g_star_to_film
    global g_role_to_film

    if g_role_to_film.has_key(role):
        return g_role_to_film[role].keys()
    print("Didn't found!")
    return {}

if __name__ == "__main__":

    # 加载演员字典
    load_star("./star.json")
    # 加载电影字典
    load_film("./film.json")

    films = film_list_by_role("何侠");
    for film in films:
        print("film:%s" % film)


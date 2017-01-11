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

type = sys.getfilesystemencoding()

class Film(object):
    def __init__(self):
        self.star_dict = {} # 明星字典(明星名)
        self.role_dict = {} # 角色字典(角色名)
        self.film_dict = {} # 电影字典(电影名)
        self.id2star = {}   # ID->明星
        self.star2film = {} # 明星->电影
        self.role2film = {} # 角色->电影

    # 抽取电影名称
    def film_name(self, text):
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
    def load_star(self, path):
        f = file(path)
        data = json.load(f)
        for item in data:
            if 0 != item["id"]:
                if len(item["name"]):
                    self.star_dict[item["name"]] = 1 # 更新明星字典
                    self.id2star[item["id"]] = item["name"] # 更新ID->明星字典
                    #print("id:%d %s" % (item["id"], item["name"]))
        return self.id2star

    # 加载电影信息
    def load_film(self, path):
        f = file(path)
        data = json.load(f)
        for item in data:
            # 构造"影名词库"
            if len(item["name_cn"]):
                self.film_dict[self.film_name(item["name_cn"])] = 1 # 更新电影字典

            # 构造"明星 -> 电影"映射
            if len(item["starring"]):
                if len(item["name_cn"]):
                    stars = item["starring"].split(",")
                    for star in stars:
                        if 0 == len(star):
                            continue
                        star_id = int(star)
                        if self.id2star.has_key(star_id):
                            name = self.id2star[star_id]
                            if self.star2film.has_key(name):
                                self.star2film[name][self.film_name(item["name_cn"])] = 1 # 更新演员->电影字典
                                continue
                            self.star2film[name] = {}
                            self.star2film[name][self.film_name(item["name_cn"])] = 1 # 更新演员->电影字典
                            #print("id:%d name:%s film:%s" % (star_id, name, self.film_name(item["name_cn"])))
            # 构造"角色 -> 电影"映射
            if len(item["starring_play"]):
                if len(item["name_cn"]):
                    roles = item["starring_play"].split(",")
                    for role in roles:
                        if len(role):
                            self.role_dict[role] = 1 # 更新角色字典
                            if self.role2film.has_key(role):
                                #print("role:%s film:%s" % (role, self.film_name(item["name_cn"])))
                                self.role2film[role][self.film_name(item["name_cn"])] = 1 # 更新演员->电影字典
                                continue
                            self.role2film[role] = {}
                            self.role2film[role][self.film_name(item["name_cn"])] = 1 # 更新演员->电影字典

    # 通过明星查找电影列表
    def film_list_by_star(self, star):
        if self.star2film.has_key(star):
            return self.star2film[star].keys()
        return {}

    # 通过角色查找电影列表
    def film_list_by_role(self, role):
        if self.role2film.has_key(role):
            return self.role2film[role].keys()
        #print("Didn't found!")
        return {}

    # 判断是否是角色
    def is_role(self, name):
        if self.role_dict.has_key(name):
            return 1
        return 0

    # 判断是否是演员
    def is_star(self, name):
        if self.star_dict.has_key(name):
            return 1
        return 0

    # 判断是否是电影
    def is_film(self, name):
        if self.film_dict.has_key(name):
            return 1
        return 0

if __name__ == "__main__":
    film = Film()

    # 加载演员字典
    film.load_star("./star.json")
    # 加载电影字典
    film.load_film("./film.json")

    for name in film.film_dict.keys():
        if film.is_star(name):
            print("name:%s" % name)

    #films = film.film_list_by_role(u"何侠");
    #for name in films:
    #    print("role:何侠 film:%s" % name)

    #films = film.film_list_by_star(u"黎明");
    #for name in films:
    #    print("name:黎明 film:%s" % name)

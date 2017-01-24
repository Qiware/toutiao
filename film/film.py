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
        self.json_dict = {} # JSON字典 - unicode编码
        self.star_dict = {} # 明星字典(明星名) - unicode编码
        self.role_dict = {} # 角色字典(角色名) - unicode编码
        self.film_dict = {} # 电影字典(电影名) - unicode编码
        self.alias_dict = {} # 别名字典(电影别名,简称) - unicode编码
        self.id2star = {}   # ID->明星
        self.star2film = {} # 明星->电影
        self.role2film = {} # 角色->电影

    # 抽取电影名称
    def film_name(self, text):
        text = unicode(text)
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
                    name = unicode(item["name"].strip())
                    self.star_dict[name] = 1 # 更新明星字典
                    self.id2star[item["id"]] = name # 更新ID->明星字典
                    #print("id:%d %s" % (item["id"], name)
        return self.id2star

    # 加载电影信息
    def load_film(self, path):
        f = file(path)
        data = json.load(f)
        for item in data:
            # 构造"影名词库"
            name_cn = self.film_name(item["name_cn"].strip())
            if 0 == len(item["name_cn"]):
                continue
            if len(item["name_cn"]):
                self.film_dict[name_cn] = 1 # 更新电影字典
                if not self.json_dict.has_key(name_cn):
                    self.json_dict[name_cn] = {}
                    self.json_dict[name_cn]["actor"] = {}
                    self.json_dict[name_cn]["alias"] = {}
                    self.json_dict[name_cn]["starring"] = {}
                    self.json_dict[name_cn]["starring_play"] = {}
                if item.has_key("alias"):
                    if len(item["alias"]):
                        alias_list = item["alias"].split(",")
                        for alias in alias_list:
                            alias = alias.strip()
                            if 0 == len(alias):
                                continue
                            alias = unicode(alias)
                            self.json_dict[name_cn]["alias"][alias] = 1
                            if not self.alias_dict.has_key(alias):
                                self.alias_dict[alias] = {}
                            self.alias_dict[alias][name_cn] = 1 # 更新别名字典

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
                            self.json_dict[name_cn]["actor"][name] = 1
                            if self.star2film.has_key(name):
                                self.star2film[name][name_cn] = 1 # 更新演员->电影字典
                                continue
                            self.star2film[name] = {}
                            self.star2film[name][name_cn] = 1 # 更新演员->电影字典
                            #print("id:%d name:%s film:%s" % (star_id, name, self.film_name(item["name_cn"])))

            # 构造"明星 -> 电影"映射
            if item.has_key("actor"):
                if len(item["actor"]):
                    if len(item["name_cn"]):
                        stars = item["actor"].split(",")
                        for star in stars:
                            star = star.strip()
                            if 0 == len(star):
                                continue
                            name = unicode(star)
                            self.json_dict[name_cn]["actor"][name] = 1
                            self.star_dict[name] = 1 # 更新明星字典
                            #print("actor:%s film:%s" % (name, name_cn))
                            if self.star2film.has_key(name):
                                self.star2film[name][name_cn] = 1 # 更新演员->电影字典
                                continue
                            self.star2film[name] = {}
                            self.star2film[name][name_cn] = 1 # 更新演员->电影字典
                            #print("id:%d name:%s film:%s" % (star_id, name, self.film_name(item["name_cn"])))
            # 构造"角色 -> 电影"映射
            if len(item["starring_play"]):
                if len(item["name_cn"]):
                    roles = item["starring_play"].split(",")
                    for role in roles:
                        role = unicode(role.strip())
                        if len(role):
                            self.role_dict[role] = 1 # 更新角色字典
                            self.json_dict[name_cn]["starring_play"][role] = 1
                            if self.role2film.has_key(role):
                                #print("role:%s film:%s" % (role, self.film_name(item["name_cn"])))
                                self.role2film[role][name_cn] = 1 # 更新演员->电影字典
                                continue
                            self.role2film[role] = {}
                            self.role2film[role][name_cn] = 1 # 更新演员->电影字典
    # 通过别名查找电影列表
    def film_list_by_alias(self, alias):
        alias = unicode(alias)
        if self.alias_dict.has_key(alias):
            return self.alias_dict[alias].keys()
        #print("Didn't found!")
        return {}

    # 通过明星查找电影列表
    def film_list_by_star(self, star):
        star = unicode(star)
        if self.star2film.has_key(star):
            return self.star2film[star].keys()
        return {}

    # 通过角色查找电影列表
    def film_list_by_role(self, role):
        role = unicode(role)
        if self.role2film.has_key(role):
            return self.role2film[role].keys()
        #print("Didn't found!")
        return {}

    # 判断是否是角色
    def is_role(self, name):
        name = unicode(name)
        if self.role_dict.has_key(name):
            return 1
        return 0

    # 判断是否是演员
    def is_star(self, name):
        name = unicode(name)
        if self.star_dict.has_key(name):
            return 1
        return 0
    # 判断是否是电影
    def is_alias(self, name):
        name = unicode(name)
        if self.alias_dict.has_key(name):
            return 1
        return 0

    # 判断是否是电影
    def is_film(self, name):
        name = unicode(name)
        if self.film_dict.has_key(name):
            return 1
        return 0

    # 打印明星列表
    def star_print(self):
        for star in self.star_dict:
            print(star)

    # 打印明星列表
    def print_json(self):
        print("[")
        for name_cn in self.json_dict:
            print("    {")
            print("        \"name_cn\":\"%s\"," % name_cn)
            print("        \"alias\":\""),
            for alias in self.json_dict[name_cn]["alias"]:
                print("%s," % alias),
            print("\",")
            print("        \"starring\":\"\",")
            print("        \"actor\":\""),
            for actor in self.json_dict[name_cn]["actor"]:
                print("%s," % actor),
            print("\",")
            print("        \"starring_play\":\""),
            for role in self.json_dict[name_cn]["starring_play"]:
                print("%s," % role),
            print("\"")
            print("    },")
        print("]")
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

# -*- coding: utf-8 -*-
import os
import re
import cgi
import sys
import time
import json
import redis
import jieba
import thread
import logging
import urllib2
import jieba.posseg as pseg

#sys.path.append("3rd/xlrd")
#sys.path.append("3rd/xlwt")
#sys.path.append("3rd/xlutils")
import xlrd
import xlwt
import xlutils
from xlutils.copy import copy

from film.film import Film

reload(sys)
sys.setdefaultencoding('utf8')

type = sys.getfilesystemencoding()

# 对EXECL行列值进行转化
def execl_val_to_str(table, row_idx, col_idx):
    v = table.row(row_idx)[col_idx].value
    if type(v) is int or type(v) is float:
        return str(int(v))
    return v.encode("utf-8")

class Parser(object):
    # 对象初始化
    def __init__(self):
        self.film_set = {}

    # 提取url中有效信息
    def parse_url(self, url, iid, title):
        self.url = url
        self.title = title

        gid = url.split("/")[3]
        self.gid = gid.split("a")[1]
        self.iid = iid

        #print("gid:%s iid:%s" % (self.gid, self.iid))
        return

    # 抓取评论信息
    def fetch_comment(self, url):
        try:
            fd = urllib2.urlopen(url)
            comment = fd.read()

            #print("%s" % comment)
            comments = []
            data = json.loads(comment)
            for item in data['data']['comments']:
                comments.append(item['text'])
            return comments
        except:
            print("Get data failed!")
            return "{}"

    # 分析评论数据
    def analyze(self, url):
        # 获取评论数据
        comments = self.fetch_comment(url)

        # 逐行分析评论
        for comment in comments:
            self.parse(film, comment.strip(), False)
        film_name = "UNKNOWN"
        film_name_val = 0
        for key in parser.film_set.keys():
            print("num:%d name:%s" % (parser.film_set[key], key))
            if parser.film_set[key] > film_name_val:
                film_name = key
                film_name_val = parser.film_set[key]

        if film.is_star(film_name):
            print("star:%s" % (film_name))
        return film_name

    # 评论数据分析
    def parse(self, film, comment, is_title):
        print("comment:%s" % comment)
        # 规则匹配抽取
        if is_title:
            score = 8
        else:
            score = 5

        idx = 0
        split = re.split(r"《", comment.encode("utf-8"))
        for text in split:
            if 0 == idx % 2:
                idx += 1
                continue
            idx += 1
            name = re.split(r"》", text)
            if name is None:
                continue
            film_name = name[0]
            print("%s" % film_name)
            if self.film_set.has_key(film_name.encode('utf-8')):
                self.film_set[film_name] += score
            else:
                self.film_set[film_name] = score

        # 词性标注处理
        result = pseg.cut(comment)
        for word, flag in result:
            #print("word:%s flag:%s" % (word, flag))
            if "n" != flag:
                continue

            m = re.search("n", flag)
            if m is not None:
                print("word:%s flag:%s" % (word, flag))
                # 是否是电影名称
                if 1 == film.is_film(word):
                    print("This is film name. film:%s" % (word))
                    if self.film_set.has_key(word):
                        self.film_set[word] += 3
                    else:
                        self.film_set[word] = 3
                # 是否是演员名称
                if 1 == film.is_star(word):
                    film_list = film.film_list_by_star(word)
                    for name in film_list:
                        print("Get film by star. star:%s film:%s" % (word, name))
                        if self.film_set.has_key(name):
                            self.film_set[name] += 1
                        else:
                            self.film_set[name] = 1
                # 是否是角色名称
                if 1 == film.is_role(word):
                    film_list = film.film_list_by_role(word)
                    for name in film_list:
                        print("Get film by role. role:%s film:%s" % (word, name))
                        if self.film_set.has_key(name):
                            self.film_set[name] += 2
                        else:
                            self.film_set[name] = 2
            #else:
            #    m = re.search("i", flag)
            #    if m is not None:
            #        # 是否是电影名称
            #        if 1 == film.is_film(word):
            #            print("This is film name. film:%s" % (word))
            #            if self.film_set.has_key(word):
            #                self.film_set[word] += 3
            #            else:
            #                self.film_set[word] = 3
            #            continue
            #        # 是否是演员名称
            #        if 1 == film.is_star(word):
            #            film_list = film.film_list_by_star(word)
            #            for name in film_list:
            #                print("Get film by star. star:%s film:%s" % (word, name))
            #                if self.film_set.has_key(name):
            #                    self.film_set[name] += 1
            #                else:
            #                    self.film_set[name] = 1
            #            continue
            #        # 是否是角色名称
            #        if 1 == film.is_role(word):
            #            film_list = film.film_list_by_role(word)
            #            for name in film_list:
            #                print("Get film by role. role:%s film:%s" % (word, name))
            #                if self.film_set.has_key(name):
            #                    self.film_set[name] += 2
            #                else:
            #                    self.film_set[name] = 2
            #            continue
# 加载用户字典
def load_userdict():
    """
    Load user dictionary
    """
    # 姓名列表
    jieba.load_userdict("./dict/name/amuse.txt");
    jieba.load_userdict("./dict/name/sporter.txt");
    jieba.load_userdict("./dict/name/politicians.txt");

    # 体育项目
    jieba.load_userdict("./dict/film.txt"); # 体育项目
    jieba.load_userdict("./dict/sport.txt"); # 体育项目

    # 默认词典
    jieba.load_userdict("./dict/dict.txt");

    # 电影信息
    jieba.load_userdict("./film/film.list");
    jieba.load_userdict("./film/star.list");
    jieba.load_userdict("./film/role.list");

def load_film_dict(fname):
    film_dict = {}
    # 提取电影名称
    f = open(fname, "r")
    while True:
        line = f.readline()
        if line:
            film = line.split(' ')[0].strip()
            film_dict[film] = 1
            #print("film:%s" % (film))
        else:
            break
    f.close()

################################################################################
##函数名称: main
##功    能: 通过今日头条的评论信息提取电影名称
##输入参数:
##输出参数:
##返    回:
##实现描述:
##     1. 加载电影相关信息
##注意事项:
##作    者: # Qifeng.zou # 2014.03.11 #
################################################################################
if __name__ == "__main__":
    film = Film()

    # 获取评论文件
    if len(sys.argv) <= 1:
        print("Please special url!")
        exit(1)

    url = sys.argv[1]

    # 加载自定义分词库
    load_userdict();

    # 加载电影词典
    load_film_dict("./dict/film.txt") # 加载电影字典
    film.load_star("./film/star.json")      # 加载演员字典
    film.load_film("./film/film.json")      # 加载电影字典

    #if row < 133:
    #    continue
    #if row > 134:
    #    break
    parser = Parser()
    film_name = parser.analyze(url) # 分析信息

    print("name:%s url: %s" % (film_name, url))

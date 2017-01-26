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
        self.url = ""
        self.title = ""
        self.gid = ""
        self.iid = ""
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
        # 评论存储文件名
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
    def analyze(self, film, url):
        comments = []

        # 获取评论数据
        m = re.search("http", url)
        if m is not None:
            comments = self.fetch_comment(url)
        else:
            self.parse(film, unicode(url.strip()), True)

        # 逐行分析评论
        for comment in comments:
            self.parse(film, unicode(comment.strip()), False)
        film_name = "UNKNOWN"
        film_name_val = 0
        for key in parser.film_set.keys():
            #if self.iid == "6359738027887030272":
                #print("score:%d name:%s" % (parser.film_set[key], key))
            #if film.film_dict.has_key(key.encode('utf-8')):
            print("score:%d name:%s" % (parser.film_set[key], key))
            if parser.film_set[key] > film_name_val:
                film_name = key
                film_name_val = parser.film_set[key]

        if film.is_star(film_name):
            print("star:%s" % (film_name))
        #print("film name:%s" % (film_name))
        return film_name

    def has_keyword(self, comment):
        m = re.search("片名", comment)
        if m:
            return True

        m = re.search("电影名", comment)
        if m:
            return True

        m = re.search("电视名字", comment)
        if m:
            return True

        return False

    # 评论数据分析
    def parse(self, film, comment, is_title):
        print("comment:%s" % comment)

        score = 2
        if is_title:
            score = 4

        # 是否有"片名、电影名"等关键字
        has_keyword = self.has_keyword(comment)

        is_book_mark = False
        prev_is_book_mark = False
        # 词性标注处理, 并抽取电影名、电影别名、角色名、演员名等，并给影片打分.
        result = pseg.cut(comment)
        for word, flag in result:
            if "《" == word:
                is_book_mark = True
                continue
            prev_is_book_mark = is_book_mark
            is_book_mark = False

            print("word:%s flag:%s" % (word, flag))

            m = re.search("n", flag)
            if m is not None:
                #print("word:%s flag:%s" % (word, flag))
                # 是否是电影名称
                if 1 == film.is_film(word):
                    print("This is film name. film:%s" % (word))
                    if self.film_set.has_key(word):
                        self.film_set[word] += 3
                    else:
                        self.film_set[word] = 3
                    if has_keyword:
                        self.film_set[word] += 2
                    if prev_is_book_mark:
                        self.film_set[word] += score
                    if is_title:
                        self.film_set[word] += 2
                # 是否是别名名称
                if 1 == film.is_alias(word):
                    film_list = film.film_list_by_alias(word)
                    for name in film_list:
                        print("Get film by alias. alias:%s film:%s" % (word, name))
                        if self.film_set.has_key(name):
                            self.film_set[name] += 3
                        else:
                            self.film_set[name] = 3
                        if has_keyword:
                            self.film_set[name] += 2
                        if prev_is_book_mark:
                            self.film_set[name] += score
                        if is_title:
                            self.film_set[name] += 2
                # 是否是演员名称
                if 1 == film.is_star(word):
                    film_list = film.film_list_by_star(word)
                    for name in film_list:
                        print("Get film by star. star:%s film:%s" % (word, name))
                        if self.film_set.has_key(name):
                            self.film_set[name] += 1
                        else:
                            self.film_set[name] = 1
                        if is_title:
                            self.film_set[name] += 2
                # 是否是角色名称
                if 1 == film.is_role(word):
                    film_list = film.film_list_by_role(word)
                    for name in film_list:
                        print("Get film by role. role:%s film:%s" % (word, name))
                        if self.film_set.has_key(name):
                            self.film_set[name] += 2
                        else:
                            self.film_set[name] = 2
                        if is_title:
                            self.film_set[name] += 2
# 加载用户字典
def load_userdict():
    """
    Load user dictionary
    """

    # 默认词典
    jieba.load_userdict("./dict/dict.txt");
    jieba.load_userdict("./dict/dict.txt.big");

    # 电影信息
    jieba.load_userdict("./film/list/film.list");
    jieba.load_userdict("./film/list/star.list");
    jieba.load_userdict("./film/list/role.list");

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
    #fname = "./doc/影视－明星.xlsx"
    url = ""
    if len(sys.argv) > 1:
        url = sys.argv[1]

    # 加载自定义分词库
    load_userdict();

    # 加载电影词典
    film.load_film("./film/film.dict")  # 加载电影字典

    parser = Parser()
    film_name = parser.analyze(film, url) # 分析信息

    print("url:%s film:%s" % (url, film_name))

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
        self.film_incr = {}

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
    def fetch_comment(self):
        # 评论存储文件名
        url = "http://www.toutiao.com/api/comment/list/?group_id="+self.gid+"&item_id="+self.iid+"&offset=0&count=100"

        fd = urllib2.urlopen(url)
        comment = fd.read()

        #print("%s" % comment)
        comments = []
        data = json.loads(comment)
        for item in data['data']['comments']:
            comments.append(item['text'])
        return comments

    # 分析评论数据
    def mining(self, film, url, iid, title):
        # 提取有效信息
        self.parse_url(url, iid, title)

        # 分析标题数据
        self.parse(film, title.strip(), True)

        # 获取评论数据
        comments = self.fetch_comment()

        # 逐行分析评论
        for comment in comments:
            self.parse(film, comment.strip(), False)
        film_name = "UNKNOWN"
        film_name_val = 0
        for key in parser.film_incr.keys():
            #if self.iid == "6347993603079400448":
            #    print("num:%d name:%s" % (parser.film_incr[key], key))
            #if film.film_dict.has_key(key.encode('utf-8')):
                if parser.film_incr[key] > film_name_val:
                    film_name = key
                    film_name_val = parser.film_incr[key]

        #print("film name:%s" % (film_name))
        return film_name

    # 评论数据分析
    def parse(self, film, comment, is_title):
        # 规则匹配抽取
        if is_title:
            score = 20
        else:
            score = 10

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
            #print("%s" % film_name)
            if self.film_incr.has_key(film_name.encode('utf-8')):
                self.film_incr[film_name] += score
            else:
                self.film_incr[film_name] = score

        # 词性标注处理
        result = pseg.cut(comment)
        for word, flag in result:
            #print("word:%s flag:%s" % (word, flag))
            m = re.search("n", flag)
            if m is not None:
                # 是否是电影名称
                if 1 == film.is_film(word):
                    if self.film_incr.has_key(word):
                        self.film_incr[word] += 1
                    else:
                        self.film_incr[word] = 1
                    continue
                # 是否是演员名称
                if 1 == film.is_star(word):
                    film_list = film.film_list_by_star(word)
                    for name in film_list:
                        if self.film_incr.has_key(name):
                            self.film_incr[name] += 1
                        else:
                            self.film_incr[name] = 1
                    continue
                # 是否是角色名称
                if 1 == film.is_role(word):
                    film_list = film.film_list_by_role(word)
                    for name in film_list:
                        if self.film_incr.has_key(name):
                            self.film_incr[name] += 1
                        else:
                            self.film_incr[name] = 1
                    continue
            m = re.search("i", flag)
            if m is not None:
                # 是否是电影名称
                if 1 == film.is_film(word):
                    if self.film_incr.has_key(word):
                        self.film_incr[word] += 1
                    else:
                        self.film_incr[word] = 1
                    continue
                # 是否是演员名称
                if 1 == film.is_star(word):
                    film_list = film.film_list_by_star(word)
                    for name in film_list:
                        if self.film_incr.has_key(name):
                            self.film_incr[name] += 1
                        else:
                            self.film_incr[name] = 1
                    continue
                # 是否是角色名称
                if 1 == film.is_role(word):
                    film_list = film.film_list_by_role(word)
                    for name in film_list:
                        if self.film_incr.has_key(name):
                            self.film_incr[name] += 1
                        else:
                            self.film_incr[name] = 1
                    continue
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
    fname = "影视－明星.xlsx"
    if len(sys.argv) > 1:
        fname = sys.argv[1]

    # 加载自定义分词库
    load_userdict();

    # 加载电影词典
    load_film_dict("./dict/film.txt") # 加载电影字典
    film.load_star("./film/star.json")      # 加载演员字典
    film.load_film("./film/film.json")      # 加载电影字典

    # 从XLSX中提取有效数据
    bk = xlrd.open_workbook(fname)
    if bk is None:
        print("Open [%s] failed!" % fname)
        exit(0)
    table = bk.sheet_by_name(u'今日头条')
    if table is None:
        print("Sheet by name failed! fname:%s" % fname)
        exit(0)

    # 列字段定义
    COL_URL         = 0 # URL
    COL_ITEM_ID     = 1 # ITEM ID
    COL_TITLE       = 2 # 标题
    COL_FILM_NAME   = 3 # 片名

    wb = copy(bk)
    for row in xrange(table.nrows):
        if 0 == row:
            wb.get_sheet(2).write(0, COL_FILM_NAME, '片名')
            continue
        url = table.row(row)[COL_URL].value #execl_val_to_str(table, row, COL_URL) # 获取URL
        iid = str(int(table.row(row)[COL_ITEM_ID].value)) #execl_val_to_str(table, row, COL_ITEM_ID) # 获取ITEM ID
        title = table.row(row)[COL_TITLE].value #execl_val_to_str(table, row, COL_TITLE) # 获取标题

        parser = Parser()
        film_name = parser.mining(film, url, iid, title) # 挖掘信息

        wb.get_sheet(2).write(row, COL_FILM_NAME, film_name)
        print("[%03d] %s %s %s %s" % (row, url, iid, title, film_name))
    #wb.save("./output.xlsx")

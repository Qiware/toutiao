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

sys.path.append("3rd/xlrd")
sys.path.append("3rd/xlwt")
import xlrd
import xlwt

reload(sys)
sys.setdefaultencoding('utf8')

g_film_dict = {}

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
        self.film_dict = {}

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
    def mining(self, url, iid, title):
        # 提取有效信息
        self.parse_url(url, iid, title)

        # 获取评论数据
        comments = self.fetch_comment()

        # 逐行分析评论
        for comment in comments:
            self.parse(comment.strip())
        film_name = "UNKNOWN"
        film_name_val = 0
        for key in parser.film_dict.keys():
            #if g_film_dict.has_key(key):
                #print("num:%d name:%s" % (parser.film_dict[key], key))
                if parser.film_dict[key] > film_name_val:
                    film_name = key
                    film_name_val = parser.film_dict[key]

        #print("film name:%s" % (film_name))
        return film_name

    # 评论数据分析
    def parse(self, comment):
        result = pseg.cut(comment)
        for word, flag in result:
            m = re.search("n", flag)
            if m is not None:
                if self.film_dict.has_key(word):
                    self.film_dict[word] += 1
                else:
                    self.film_dict[word] = 1

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
    # 提取电影名称
    f = open(fname, "r")
    while True:
        line = f.readline()
        if line:
            film = line.split(' ')[0].strip()
            g_film_dict[film] = 1
            #print("film:%s" % (film))
        else:
            break
    f.close()

if __name__ == "__main__":
    # 获取评论文件
    fname = "影视－明星.xlsx"
    if len(sys.argv) > 1:
        fname = sys.argv[1]

    # 加载自定义字典
    load_userdict();

    # 加载电影字典
    load_film_dict("./dict/film.txt")

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

    for row in xrange(table.nrows):
        if 0 == row:
            continue
        url = table.row(row)[COL_URL].value #execl_val_to_str(table, row, COL_URL) # 获取URL
        iid = str(int(table.row(row)[COL_ITEM_ID].value)) #execl_val_to_str(table, row, COL_ITEM_ID) # 获取ITEM ID
        title = table.row(row)[COL_TITLE].value #execl_val_to_str(table, row, COL_TITLE) # 获取标题
    
        parser = Parser()
        film = parser.mining(url, iid, title) # 挖掘信息

        print("%s %s %s %s" % (url, iid, title, film))

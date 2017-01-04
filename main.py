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

reload(sys)
sys.setdefaultencoding('utf8')

type = sys.getfilesystemencoding()

class Parser(object):
    # 对象初始化
    def __init__(self):
        self.url = ""
        self.title = ""
        self.gid = ""
        self.iid = ""
        self.film_dict = {}

    # 提取url中有效信息
    def parse_url(self, url, title):
        self.url = url
        self.title = title

        gid = url.split("/")[3]
        self.gid = gid.split("a")[1]
        self.iid = url.split("/")[4]

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
    def mining(self, url, title):
        # 提取有效信息
        self.parse_url(url, title)

        # 获取评论数据
        comments = self.fetch_comment()

        # 逐行分析评论
        for comment in comments:
            self.parse(comment.strip())
        film_name = ""
        film_name_val = 0
        for key in parser.film_dict.keys():
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

if __name__ == "__main__":
    # 获取评论文件
    if len(sys.argv) > 1:
        fname = sys.argv[1]

    # 加载自定义字典
    load_userdict();

    # 提取URL并分析数据
    f = open(fname, "r")
    while True:
        line = f.readline()
        if line:
            url = line.split(' ')[0].strip()
            title = line.split(' ')[1].strip()

            parser = Parser()
            film = parser.mining(url, title) # 挖掘信息

            print("%s %s %s" % (url, title, film))
        else:
            break
    f.close()

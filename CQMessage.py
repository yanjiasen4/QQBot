# -*- coding:gbk -*-

import re

class CQAt:
    PATTERN = re.compile(r'\[CQ:at,qq=(\d+?)\]')

    def __init__(self, qq):
        self.qq = qq

    def __str__(self):
        return "[CQ:at,qq={}]".format(self.qq)

class CQImage:
    PATTERN = re.compile(r'\[CQ:image,file=(.+?)\]')

    def __init__(self, file):
        self.file = file

    def __str__(self):
        return "[CQ:image,file={}]".format(self.file)

class CQRecord:
    PATTERN = re.compile(r'\[CQ:record,file=(.+?)\]')

    def __init__(self, file):
        self.file = file

    def __str__(self):
        return "[CQ:record,file={}]".format(self.file)

class CQShare:
    PATTERN = re.compile(r'\[CQ:share,url=(.+?),title=(.+?),content=(.+?),image=(.+?)\]')

    def __init__(self, url, title, content, image):
        self.url = url
        self.title = title
        self.content = content
        self.image = image

    def __str__(self):
        return "[CQ:share,url={},title={},content={},image={}]".format(self.url, self.title, self.content, self.image)
        
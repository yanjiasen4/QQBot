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
        
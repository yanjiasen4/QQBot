# -*- coding:gbk -*-

import base64
from CQPack import CQUnpack

class CQStrangerInfo(object):
    QQID                    = None
    Nickname                = None
    Sex                     = None
    Age                     = None

    def __init__(self, data, is_base64 = True):
        data = base64.decodestring(data) if is_base64 else data
        info = CQUnpack(data)
        self.QQID                       = info.GetLong()
        self.Nickname                   = info.GetLenStr()
        self.Sex                        = info.GetInt()
        self.Age                        = info.GetInt()

    def __str__(self):
        t = {
            'QQ��' : self.QQID,
            '�ǳ�' : self.Nickname,
            '�Ա�' : self.Sex,
            '����' : self.Age,
        }
        lines = []
        for (k, v) in t.items():
            lines.append('{0}:{1}'.format(k, v))
        return '\n'.join(lines)

'''
EXAMPLE:

from CQStrangerInfo import CQStrangerInfo
info = CQStrangerInfo(CQSDK.GetStrangerInfo(fromQQ))
'''
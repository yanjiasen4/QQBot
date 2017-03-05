# -*- coding:gbk -*-

import base64
from CQPack import CQUnpack

class CQGroupMemberInfo(object):
    GroupID                 = None
    QQID                    = None
    Nickname                = None
    Card                    = None
    Sex                     = None
    Age                     = None
    Address                 = None
    JoinGroupTime           = None
    LastSpeakTime           = None
    LevelName               = None
    Authority               = None
    IsBad                   = None
    SpecialTitle            = None
    SpecialTitleExpiredTime = None
    IsAllowedToModifyCard   = None

    def __init__(self, data, is_base64 = True):
        data = base64.decodestring(data) if is_base64 else data
        info = CQUnpack(data)
        self.GroupID                    = info.GetLong()
        self.QQID                       = info.GetLong()
        self.Nickname                   = info.GetLenStr()
        self.Card                       = info.GetLenStr()
        self.Sex                        = info.GetInt()
        self.Age                        = info.GetInt()
        self.Address                    = info.GetLenStr()
        self.JoinGroupTime              = info.GetInt()
        self.LastSpeakTime              = info.GetInt()
        self.LevelName                  = info.GetLenStr()
        self.Authority                  = info.GetInt()
        self.IsGroupAdmin               = self.Authority in [ 2, 3 ]
        self.IsGroupOwner               = self.Authority in [ 3 ]
        self.IsBad                      = (info.GetInt() == 1)
        self.SpecialTitle               = info.GetLenStr()
        self.SpecialTitleExpiredTime    = info.GetInt()
        self.IsAllowedToModifyCard      = (info.GetInt() == 1)

    def __str__(self):
        t = {
            'Ⱥ��' : self.GroupID,
            'QQ��' : self.QQID,
            '�ǳ�' : self.Nickname,
            '��Ƭ' : self.Card,
            '�Ա�' : self.Sex,
            '����' : self.Age,
            '����' : self.Address,
            '��Ⱥʱ��' : self.JoinGroupTime,
            '�����ʱ��' : self.LastSpeakTime,
            '�ȼ�����' : self.LevelName,
            '����Ȩ��' : self.Authority,
            '�Ƿ�Ⱥ��' : self.IsGroupAdmin,
            '�Ƿ�Ⱥ��' : self.IsGroupOwner,
            '�Ƿ�����Ա' : self.IsBad,
            'ר��ͷ��' : self.SpecialTitle,
            'ר��ͷ�ι���ʱ��' : self.SpecialTitleExpiredTime,
            '�Ƿ������޸���Ƭ' : self.IsAllowedToModifyCard,
        }
        lines = []
        for (k, v) in t.items():
            lines.append('{0}:{1}'.format(k, v))
        return '\n'.join(lines)

'''
EXAMPLE:

from CQGroupMemberInfo import CQGroupMemberInfo
info = CQGroupMemberInfo(CQSDK.GetGroupMemberInfoV2(fromGroup, fromQQ))
'''
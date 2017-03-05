# -*- coding:gbk -*-

import _CQSDK

EVENT_IGNORE        = 0    
EVENT_BLOCK         = 1     

REQUEST_ALLOW       = 1     
REQUEST_DENY        = 2    

REQUEST_GROUPADD    = 1    
REQUEST_GROUPINVITE = 2    

CQLOG_DEBUG         = 0     
CQLOG_INFO          = 10    
CQLOG_INFOSUCCESS   = 11    
CQLOG_INFORECV      = 12   
CQLOG_INFOSEND      = 13   
CQLOG_WARNING       = 20    
CQLOG_ERROR         = 30    
CQLOG_FATAL         = 40    


def MessageBox(msg, title):
    return _CQSDK.MessageBox(msg, title)

def GetAppID():
    return _CQSDK.GetAppID()

def SendPrivateMsg(QQID, msg):
    return _CQSDK.SendPrivateMsg(QQID, msg)

def SendGroupMsg(groupid, msg):
    return _CQSDK.SendGroupMsg(groupid, msg)

def SendDiscussMsg(discussid, msg):
    return _CQSDK.SendDiscussMsg(discussid, msg)

def SendLike(QQID):
    return _CQSDK.SendLike(QQID)

def SetGroupKick(groupid, QQID, rejectaddrequest):
    return _CQSDK.SetGroupKick(groupid, QQID, rejectaddrequest)

def SetGroupBan(groupid, QQID, duration):
    return _CQSDK.SetGroupBan(groupid, QQID, duration)

def SetGroupAdmin(groupid, QQID, setadmin):
    return _CQSDK.SetGroupAdmin(groupid, QQID, setadmin)

def SetGroupWholeBan(groupid, enableban):
    return _CQSDK.SetGroupWholeBan(groupid, enableban)

def SetGroupAnonymousBan(groupid, anomymous, duration):
    return _CQSDK.SetGroupAnonymousBan(groupid, anomymous, duration)

def SetGroupAnonymous(groupid, enableanomymous):
    return _CQSDK.SetGroupAnonymous(groupid, enableanomymous)

def SetGroupCard(groupid, QQID, newcard):
    return _CQSDK.SetGroupCard(groupid, QQID, newcard)

def SetGroupLeave(groupid, isdismiss):
    return _CQSDK.SetGroupLeave(groupid, isdismiss)

def SetGroupSpecialTitle(groupid, QQID, newspecialtitle, duration):
    return _CQSDK.SetGroupSpecialTitle(groupid, QQID, newspecialtitle, duration)

def SetDiscussLeave(discussid):
    return _CQSDK.SetDiscussLeave(discussid)

def SetFriendAddRequest(responseflag, responseoperation, remark):
    return _CQSDK.SetFriendAddRequest(responseflag, responseoperation, remark)

def SetGroupAddRequestV2(responseflag, requesttype, responseoperation, reason):
    return _CQSDK.SetGroupAddRequestV2(responseflag, requesttype, responseoperation, reason)

def GetGroupMemberInfoV2(groupid, QQID, nocache = False):
    return _CQSDK.GetGroupMemberInfoV2(groupid, QQID, nocache)

def GetStrangerInfo(QQID, nocache = False):
    return _CQSDK.GetStrangerInfo(QQID, nocache)

def AddLog(priority, category, content):
    return _CQSDK.AddLog(priority, category, content)

def GetCookies():
    return _CQSDK.GetCookies()

def GetCsrfToken():
    return _CQSDK.GetCsrfToken()

def GetLoginQQ():
    return _CQSDK.GetLoginQQ()

def GetLoginNick():
    return _CQSDK.GetLoginNick()

def GetAppDirectory():
    return _CQSDK.GetAppDirectory()

def SetFatal(errorinfo):
    return _CQSDK.SetFatal(errorinfo)

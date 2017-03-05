# -*- coding:gbk -*-
import requests
import json
import os
import sys
reload(sys)
sys.setdefaultencoding('gbk')

import os
import logging
logging.basicConfig(
    level       = logging.INFO,
    format      = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
    datefmt     = '%Y-%m-%d %H:%M:%S',
    filename    = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'CQHanlder.log'),
    filemode    = 'w+'
)

ignoreList = []

groupID = [79177174, 259641925]
yande_url = 'https://yande.re/post.json'
danbooru_url = 'http://danbooru.donmai.us/'
ignore_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'ignore.json')
maxImageSize = 4000000
maxExposionTime = 1

import CQSDK
from CQGroupMemberInfo import CQGroupMemberInfo
from CQMessage import CQAt, CQImage, CQRecord

import math
from datetime import *
import re
import random

expTable = [100, 300, 800, 1500, 3800, 9000, 22000, 48000, 90000, 140000, 200000]
levelTable = ['淬体', '炼气', '筑基', '金丹', '辟谷', '元婴', '洞虚', '分神', '大乘', '渡劫', '仙人']
subLevelTable = ['一层', '二层', '三层', '四层', '五层', '六层', '七层', '八层', '九层', '圆满']

idolTable = ['Abe Nana', 'Aiba Yumi', 'Anastasia', 'Futaba Anzu', 'Shibuya Rin', 'Honda Mio', 'Igarashi Kyoko', 'Kanzaki Ranko', 'Jougasaki Mika', 'Mifune Miyu', 'Moroboshi Kirari', 'Shirasaka Koume', 'Tada Riina', 'Ninomiya Asuka', 'Takagaki Kaede']
audioPath = 'F:/酷Q Pro/data/record/'
imagePath = 'F:/酷Q Pro/data/image/comic/'

systemQQID = 1000000
anonymousQQID = 80000000

class Member:
    info = None
    exp = 0
    level = 0
    fatigueRate = 0
    expRate = 0
    expBaseRate = 1
    nextLevelExp = 100
    expMsg = 0
    maxExpMsg = 300
    firstMsgTime = 0
    lastMsgTime = 0
    exposionNum = 0
    rollSum = 0
    rollNum = 0

    def __init__(self, data):
        self.info = data

    def __cmp__(self, other):
        if self.level > other.level:
            return 1
        elif self.level == other.level:
            return cmp(self.exp, other.exp)
        else:
            return -1

    def addExp(self, h, timestamp):
        if self.expMsg >= self.maxExpMsg:
            return
        self.expMsg += 1
        timeRate = 1
        if h >= 0 and h <= 6:
            timeRate += h*0.1
        xxRate = 1
        hourDiff = (timestamp - self.lastMsgTime)/3600
        if hourDiff > 1:
            self.firstMsgTime = timestamp
        else:
            xxRate += (timestamp - self.firstMsgTime)/3600/5
        self.lastMsgTime = timestamp

        self.exp += self.expBaseRate * timeRate * xxRate * (1 + self.expRate)
        if self.exp > self.nextLevelExp:
            self.level += 1
            self.exp = self.exp - self.nextLevelExp
            self.nextLevelExp = expTable[self.level]

    def addExpR(self, exp):
        self.exp += exp
        if self.exp > self.nextLevelExp:
            self.level += 1
            self.exp = self.exp - self.nextLevelExp
            self.nextLevelExp = expTable[self.level]
    
    def decreaseExpR(self, exp):
        if exp > self.exp:
            self.level -= 1
            restExp = exp - self.exp
            self.nextLevelExp = expTable[self.level]
            self.exp = self.nextLevelExp - restExp

    def load(self, exp, level, msg, expTime):
        self.exp = exp
        self.level = level
        self.nextLevelExp = expTable[self.level]
        self.expMsg = msg
        self.exposionNum = expTime

    def refresh(self):
        self.expMsg = 0
        self.exposionNum = 0
        self.luckyRate = 0

    @property
    def levelName(self):
        content = levelTable[self.level]
        subLevel = subLevelTable[int(math.floor(10*self.exp/self.nextLevelExp))]
        return content + subLevel

    @property
    def remainingExp(self):
        return self.nextLevelExp - self.exp

    @property
    def levelExp(self):
        return expTable[self.level]

    @property
    def luckyRate(self):
        rollAve = self.rollSum / self.rollNum
        return rollAve * math.pow((0.95 + 0.001*rollAve), self.rollNum)

class CQHandler(object):
    members = {}
    saveRoutine = 10

    def __init__(self):
        logging.info('__init__')
        self._key_regex = re.compile('^.xx|!save|!idol|!drive|!rank|!roll')
        self._data_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'xx.data')
        self.exProbility = 0.003
        self.msgCount = 0
        self.isRefresh = 0
        self.ignoreList = []
        self.loadExp = {}
        self.saveExp = {}
        self.load()
        self.load_members(groupID[0])
        self.driveOn = True
        logging.info('__init_finished__')

    def __del__(self):
        logging.info('__del__')
        self.save()
    
    def load(self):
        with open(self._data_file, 'r') as f:
            for line in f:
                res = line.split(':')
                paras = res[1].split(',')
                member = {'exp': float(paras[0]), 'level': int(paras[1]), 'msg': int(paras[2]), 'expTime': int(paras[3])}
                self.loadExp[int(res[0])] = member
            f.close()
            self.saveExp = self.loadExp

    def save(self):
        with open(self._data_file,'w+') as f:
            for key in self.saveExp:
                if key in self.members:
                    self.saveExp[key]['exp'] = self.members[key].exp
                    self.saveExp[key]['level'] = self.members[key].level
                    self.saveExp[key]['msg'] = self.members[key].expMsg
                    self.saveExp[key]['expTime'] = self.members[key].exposionNum
            for (key, value) in self.members.items():
                if key not in self.saveExp:
                    self.saveExp[key] = {'exp': value.exp, 'level': value.level, 'msg': value.expMsg, 'expTime': value.exposionNum}
            for (key, value) in self.saveExp.items():
                content = str(key) + ':' + str(value['exp']) + ',' + str(value['level']) + ',' + str(value['msg']) + ',' + str(value['expTime']) + '\n'
                f.writelines(content)
            f.close()

    def load_ignore(self):
        with open(ignore_file, 'r') as f:
            data = json.load(f)
            self.ignoreList = [int(n) for n in data]
            f.close()

    def refresh(self):
        for key in self.members:
            self.members[key].refresh()
        for (key, value) in self.saveExp.items():
            value['msg'] = 0
            value['expTime'] = 0
            value['luckyRate'] = 0

    def explosion(self, QQID):
        member = self.members[QQID]
        if member.exposionNum >= maxExposionTime:
            return
        if member:
            preLevel = member.levelName
            exp = random.randint(0, 30 + int(member.levelExp/10))
            member.addExpR(exp)
            member.exposionNum += 1
            return preLevel, member.levelName
        return "?", "?"

    def harm(self, QQID):
        member = self.members[QQID]
        if member:
            preLevel = member.levelName
            exp = random.randint(int(member.levelExp/10), 30 + int(member.levelExp)/5)
            member.decreaseExpR(exp)
            return preLevel, member.levelName
        return "?", "?"
    
    def load_members(self, fromGroup):
        if self.loadExp is None or len(self.loadExp) == 0:
            return
        hour = datetime.now().hour
        for (key, value) in self.loadExp.items():
            info = CQGroupMemberInfo(CQSDK.GetGroupMemberInfoV2(fromGroup, key))
            member = Member(info)
            member.firstMsgHour = hour
            member.lastMsgHour = hour
            member.load(value['exp'], value['level'], value['msg'], value['expTime'])
            self.members[key] = member

    def rank(self, fromGroup, limit=None):
        content = '-----------------------辣条榜-----------------------\n'
        members = sorted(self.members.items(), lambda x, y: cmp(x[1], y[1]), reverse=True)
        listNum = 10
        if limit is not None and str.isdigit(limit):
            listNum = int(limit)
        count = 0
        for (key, value) in members:
            count += 1            
            content += str(count) + '.' + str(value.info.Card) + '({0})'.format(key) + ': ' + str(value.levelName) + '\n'
            if count >= listNum:
                break
        content = content[:-1]
        try:
            CQSDK.SendGroupMsg(fromGroup, content)
        except Exception as e:
            logging.exception(e)

    def roll(self, fromGrouop, QQID, para=None):
        max = 100
        if para is not None:
            max = re.findall(r"\d+", para)[0]
        result = random.randint(0, max)
        res_normlize = 100 * result / max
        member = self.members[QQID]
        if member is None:
            return
        member.rollSum += res_normlize
        member.rollNum += 1
        try:
            CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '掷出了' + str(result) + '\n今天的运气指数为(还没做)')
        except Exception as e:
            logging.exception(e)

    def speak(self, fromGroup, QQID, tag=None):
        path = audioPath
        speaker = ''
        if tag is not None:
            findTag = False
            for key in idolTable:
                keyLower = key.lower()
                if keyLower.find(tag.lower()) >= 0:
                    speaker = key
                    path += speaker
                    findTag = True
                    logging.info(path)
                    break
            if findTag == False:
                try:
                    CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '语音库中还没有这个音源%>_<%')
                except Exception as e:
                    logging.exception(e)
                return
        else:
            speaker = idolTable[random.randint(0, len(idolTable) - 1)]
            path += speaker
        files = os.listdir(path)
        num = random.randint(0, len(files))
        filename = '/' + speaker + '/' + str(files[num])
        try:
            CQSDK.SendGroupMsg(fromGroup, speaker)
            CQSDK.SendGroupMsg(fromGroup, str(CQRecord(filename)))
        except Exception as e:
            logging.exception(e)

    def drive(self, fromGroup, QQID, tag=None):
        files = os.listdir(imagePath)
        num = random.randint(0, len(files))
        filename = '/comic/' + str(files[num])
        try:
            CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + str(CQImage(filename)))
        except Exception as e:
            logging.exception(e)
    
    def drive_from_danbooro(self, fromGroup, QQID, tag=None):
        full_url = danbooru_url + 'posts.json'
        if tag is not None:
            tagPara = '?tags=' + str(tag)
            full_url += tagPara
        else:
            page = random.randint(0, 100)
            pagaPara = '?page=' + str(page)
            full_url += pagePara
        full_url += '&limit=100'
        try:
            response = requests.get(full_url)
        except requests.exceptions.ConnectTimeout:
            CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '老司机翻车啦！')
            return
        except Exception as e:
            CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '找不到你想要的tag哦，请重新输入')
            return
        logging.info(response.text)
        json_result = json.loads(response.text)
        if len(json_result) == 0:
            try:
                CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '找不到你想要的tag哦，请重新输入')
            except Exception as e:
                logging.exception(e)
            return
        illust = json_result[random.randint(0, len(json_result) - 1)]
        id = illust['id']
        image_url = illust['file_url']
        extension = illust['file_ext']
        image_size = illust['file_size']
        if image_size >= maxImageSize:
            return False
        image_url = danbooru_url + image_url
        filename = str(id) + '_danbooro.' + extension
        logging.info(image_url)
        filepath = imagePath + filename
        if not os.path.exists(filepath):
            image = requests.get(image_url)
            open(filepath, 'wb').write(image.content)
        relativePath = '/comic/' + filename
        try:
            CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + str(CQImage(relativePath)))
        except Exception as e:
            logging.exception(e)
        return True

    def drive_online(self, fromGroup, QQID, tag=None):
        full_url = yande_url
        if tag is not None:
            tagPara = '?tags=' + str(tag)
            full_url += tagPara
        else:
            page = random.randint(0, 100)
            pagePara = '?page=' + str(page)
            full_url += pagePara
        full_url += '&limit=100'
        try:
            response = requests.get(full_url)
        except requests.exceptions.ConnectTimeout:
            CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '老司机翻车啦！')
            return
        except Exception as e:
            CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '神秘的东方力量导致此次开车失败')
            return

        json_result = json.loads(response.text)
        if len(json_result) == 0:
            ret = self.drive_from_danbooro(fromGroup, QQID, tag)
            if ret == False:
                try:
                    CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '找不到你想要的tag哦，请重新输入')
                except Exception as e:
                    logging.exception(e)
            return
        illust = json_result[random.randint(0, len(json_result) - 1)]
        id = illust['id']
        image_url = illust['file_url']
        extension = illust['file_ext']
        size = illust['file_size']
        if size >= maxImageSize:
            sample_size = illust['sample_file_size']
            logging.info(sample_size)
            if sample_size >= maxImageSize:
                try:
                    CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '这张图片太大了，再试一次吧')
                except Exception as e:
                    logging.exception(e)
                return
        image_url = illust['sample_url']
        filename = str(id) + '_yande.' + extension
        filepath = imagePath + filename
        if not os.path.exists(filepath):
            image = requests.get(image_url)
            open(filepath, 'wb').write(image.content)
        relativePath = '/comic/' + filename
        try:
            CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + str(CQImage(relativePath)))
        except Exception as e:
            logging.exception(e)
        
    def pk(self, founder, target):
        pass

    def OnEvent_Enable(self):
        logging.info('OnEvent_Enable')

    def OnEvent_Disable(self):
        logging.info('OnEvent_Disable')

    def OnEvent_PrivateMsg(self, subType, sendTime, fromQQ, msg, font):
        logging.info('OnEvent_PrivateMsg: subType={0}, sendTime={1}, fromQQ={2}, msg={3}, font={4}'.format(subType, sendTime, fromQQ, msg, font))

    def OnEvent_GroupMsg(self, subType, sendTime, fromGroup, fromQQ, fromAnonymous, msg, font):
        logging.info("???")
        if fromQQ == systemQQID or fromQQ == anonymousQQID or fromQQ in self.ignoreList:
            return
        hour = datetime.now().hour
        logging.info('OnEvent_GroupMsg: subType={0}, sendTime={1}, fromGroup={2}, fromQQ={3}, fromAnonymous={4}, msg={5}, font={6}'.format(subType, hour, fromGroup, fromQQ, fromAnonymous, msg, font))
        if fromGroup in groupID:
            if hour == 23 and self.isRefresh == 0:
                self.isRefresh = 1
            elif hour == 0 and self.isRefresh == 1:
                self.refresh()
                self.save()
                self.isRefresh = 0
            self.msgCount += 1
            if self.msgCount == self.saveRoutine:
                self.save()
                self.msgCount = 0
            if fromQQ not in self.members:
                info = CQGroupMemberInfo(CQSDK.GetGroupMemberInfoV2(fromGroup, fromQQ))
                newMember = Member(info)
                newMember.firstMsgHour = hour
                newMember.lastMsgHour = hour
                self.members[fromQQ] = newMember
                if fromQQ in self.loadExp:
                    loadData = self.loadExp.pop(fromQQ)
                    newMember.load(loadData['exp'], loadData['level'], loadData['msg'], loadData['expTime'])
            self.members[fromQQ].addExp(int(hour), sendTime)
            content = msg.replace(' ','')
            result = re.findall(self._key_regex, content)
            if result:
                cmd = result[0]
                para = content[len(cmd):]
                if cmd == '.xx':
                    retMsg = '你现在的境界为 ' + self.members[fromQQ].levelName + str(CQAt(fromQQ))
                    try:
                        CQSDK.SendGroupMsg(fromGroup, retMsg)
                    except Exception as e:
                        logging.exception(e)
                elif cmd == '!save':
                    self.save()
                    try:
                        CQSDK.SendGroupMsg(fromGroup, "数据保存成功")
                    except Exception as e:
                        logging.exception(e)
                elif cmd == '!idol':
                    self.speak(fromGroup, fromQQ, para)
                elif cmd == '!drive':
                    if self.driveOn:
                        self.drive_online(fromGroup, fromQQ, para)
                elif cmd == '!rank':
                    self.rank(fromGroup, para)
                elif cmd == '!roll':
                    self.roll(fromGroup, fromQQ, para)
            
            p = random.random()
            if p < self.exProbility:
                preLevel, afterLevel = self.explosion(fromQQ)
                if preLevel != afterLevel:
                    retMsg = str(CQAt(fromQQ)) + "在修炼中顿悟，实力获得大幅提升，由 " + preLevel + " 提升到 " + afterLevel
                else:
                    retMsg = str(CQAt(fromQQ)) + "在修炼中顿悟，感觉内力有了小幅提升"
                try:
                    CQSDK.SendGroupMsg(fromGroup, retMsg)
                except Exception as e:
                    logging.exception(e)

    def OnEvent_DiscussMsg(self, subType, sendTime, fromDiscuss, fromQQ, msg, font):
        logging.info('OnEvent_DiscussMsg: subType={0}, sendTime={1}, fromDiscuss={2}, fromQQ={3}, msg={4}, font={5}'.format(subType, sendTime, fromDiscuss, fromQQ, msg, font))

    def OnEvent_System_GroupAdmin(self, subType, sendTime, fromGroup, beingOperateQQ):
        logging.info('OnEvent_System_GroupAdmin: subType={0}, sendTime={1}, fromGroup={2}, beingOperateQQ={3}'.format(subType, sendTime, fromGroup, beingOperateQQ))

    def OnEvent_System_GroupMemberDecrease(self, subType, sendTime, fromGroup, fromQQ, beingOperateQQ):
        logging.info('OnEvent_System_GroupMemberDecrease: subType={0}, sendTime={1}, fromGroup={2}, fromQQ={3}, beingOperateQQ={4}'.format(subType, sendTime, fromGroup, fromQQ, beingOperateQQ))

    def OnEvent_System_GroupMemberIncrease(self, subType, sendTime, fromGroup, fromQQ, beingOperateQQ):
        logging.info('OnEvent_System_GroupMemberIncrease: subType={0}, sendTime={1}, fromGroup={2}, fromQQ={3}, beingOperateQQ={4}'.format(subType, sendTime, fromGroup, fromQQ, beingOperateQQ))

    def OnEvent_Friend_Add(self, subType, sendTime, fromQQ):
        logging.info('OnEvent_Friend_Add: subType={0}, sendTime={1}, fromQQ={2}'.format(subType, sendTime, fromQQ))

    def OnEvent_Request_AddFriend(self, subType, sendTime, fromQQ, msg, responseFlag):
        logging.info('OnEvent_Request_AddFriend: subType={0}, sendTime={1}, fromQQ={2}, msg={3}, responseFlag={4}'.format(subType, sendTime, fromQQ, msg, responseFlag))

    def OnEvent_Request_AddGroup(self, subType, sendTime, fromGroup, fromQQ, msg, responseFlag):
        logging.info('OnEvent_Request_AddGroup: subType={0}, sendTime={1}, fromGroup={2}, fromQQ={3}, msg={4}, responseFlag={5}'.format(subType, sendTime, fromGroup, fromQQ, msg, responseFlag))

    def OnEvent_Menu01(self):
        logging.info("???")
        self.refresh()
        self.save()
        logging.info('OnEvent_Menu01: refresh members info')

    def OnEvent_Menu02(self):
        logging.info("!!!")
        if self.driveOn == True:
            self.driveOn = False
            CQSDK.SendGroupMsg(groupID[0], '群主关闭了群开车')
            logging.info('OnEvent_Menu02: drive function off')
        else:
            self.driveOn = True
            CQSDK.SendGroupMsg(groupID[0], '群主开启了群开车')
            logging.info('OnEvent_Menu02: drive function on')

    def OnEvent_Menu03(self):
        logging.info('OnEvent_Menu03')

    def OnEvent_Menu04(self):
        logging.info('OnEvent_Menu04')

    def OnEvent_Menu05(self):
        logging.info('OnEvent_Menu05')

    def OnEvent_Menu06(self):
        logging.info('OnEvent_Menu06')

    def OnEvent_Menu07(self):
        logging.info('OnEvent_Menu07')

    def OnEvent_Menu08(self):
        logging.info('OnEvent_Menu08')

    def OnEvent_Menu09(self):
        logging.info('OnEvent_Menu09')

# -*- coding:gbk -*-
import requests
import json
import os
import sys
reload(sys)
sys.setdefaultencoding('gbk')

import os
import logging
import base64
from bs4 import BeautifulSoup
logging.basicConfig(
    level       = logging.INFO,
    format      = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
    datefmt     = '%Y-%m-%d %H:%M:%S',
    filename    = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'CQHanlder.log'),
    filemode    = 'w+'
)

ignoreList = []

groupID = [79177174, 487308083, 259641925, 484271101, 649028414, 305875334]
yande_url = 'https://yande.re/'
danbooru_url = 'http://danbooru.donmai.us/'
str_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'config.json')
ignore_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'ignore.json')
admin_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'admin.json')
bface_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'bface.data')
voice_config = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'voice.json')
invoker_skill = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'invoker.json')
card_data = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'cards.data')

maxImageSize = 4000000
maxExposionTime = 1
defaultTimeout = 10

import CQSDK
from CQGroupMemberInfo import CQGroupMemberInfo
from CQMessage import CQAt, CQImage, CQRecord, CQShare

from Card import CardManager

from pypinyin import pinyin, lazy_pinyin
import pypinyin
from wapresult import WolframAlphaResult

import math
import time
from datetime import *
import re
import random

#import PIL
#from PIL import Image
# from PIL import ImageDraw
# from PIL import ImageFont

expTable = [100, 300, 800, 1500, 3800, 9000, 22000, 48000, 90000, 140000, 200000, 450000]
levelTable = ["淬体", "炼气", "筑基", "金丹", "辟谷", "元婴", "洞虚", "分神", "大乘", "渡劫", "仙人"]
subLevelTable = ["一层", "二层", "三层", "四层", "五层", "六层", "七层", "八层", "九层", "圆满"]
drawLimitTable = [1,3,6,10,15,20,30,40,50,60,80,110]
invokerSkillIndex = [0, 3, 5, 7, 9, 11, 13, 15, 19, 21, 27]
audioTable = {
    'aya': 'Chatwheel_ay_ay_ay.wav',
    '哎呀呀呀呀': 'Chatwheel_ay_ay_ay.wav',
    'ehtogg': 'Chatwheel_ehto_g_g.wav',
    '爱咋给给': 'Chatwheel_ehto_g_g.wav',
    'patience from zhou': 'Chatwheel_patience.wav',
    '耐心': 'Chatwheel_patience.wav',
    '捏吧': 'Chatwheel_eto_prosto_netchto.wav',
    'brutal': 'Chatwheel_brutal.wav',
    '野性': 'Chatwheel_brutal.wav',
    '加油': 'Chatwheel_jia_you.wav',
    '玩不了啦': 'Chatwheel_wan_bu_liao_la.wav',
    '天火': 'Chatwheel_tian_huo.wav',
    '走好不送': 'Chatwheel_zou_hao_bu_song.wav',
    '破两路更好打': 'Chatwheel_po_liang_lu.wav',
    '油腻威尔斯': 'Chatwheel_universe.wav',
    'universe': 'Chatwheel_universe.wav'
}

sourcePath = 'F:/酷Q Pro/data/image/'
audioPath = 'F:/酷Q Pro/data/record/'
imagePath = 'F:/酷Q Pro/data/image/comic/'
specAudioPath = 'special/'

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
    drawTimes = 0
    drawLimit = 0

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
            xxRate += (timestamp - self.firstMsgTime)/3600/2
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
        self.drawLimit = drawLimitTable[self.level] + int(float(math.floor(10*self.exp/self.nextLevelExp))*(drawLimitTable[self.level+1]-drawLimitTable[self.level])/10)

    def refresh(self):
        self.expMsg = 0
        self.exposionNum = 0
        self.luckyRate = 0
        self.drawTimes = 0

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
        self._key_regex = re.compile('^.xx|!save|!idol|!drive|!rank|!roll|!learn|!forget|!list|!tag|!banword|!calc|!invoke|!draw|!check')
        self.keywords = []
        self.banwords = []
        self._data_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'xx.data')
        self.exProbility = 0.003
        self.msgCount = 0
        self.isRefresh = 0
        self.drawPool = {}
        self.ignoreList = []
        self.adminList = []
        self.idolTable = []
        self.loadExp = {}
        self.saveExp = {}
        self.wordMap = {}
        self.bfaceMap = {}
        self.invokerSkill = {}
        self.learnBuffer = {}
        self.lastRepeat = {}
        self.load()
        logging.info("flag4")
        self.load_members(groupID[0])
        logging.info("flag5")
        self.msgBuffer = {}
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
                member = {'exp': float(paras[0]), 'level': int(paras[1]), 'msg': int(paras[2]), 'expTime': int(paras[3]), 'drawTime': int(paras[4])}
                self.loadExp[int(res[0])] = member
            f.close()
            self.saveExp = self.loadExp
        self.load_bface()
        self.load_voice()
        self.load_ignore()
        self.load_admin()
        self.load_invoker()
        self.load_cards()
        #self.load_config()

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
                    self.saveExp[key] = {'exp': value.exp, 'level': value.level, 'msg': value.expMsg, 'expTime': value.exposionNum, 'drawTime': value.drawTimes}
            for (key, value) in self.saveExp.items():
                content = str(key) + ':' + str(value['exp']) + ',' + str(value['level']) + ',' + str(value['msg']) + ',' + str(value['expTime']) + ',' + str(value['drawTime']) + '\n'
                f.writelines(content)
            f.close()
        if len(self.bfaceMap) > 0:
            with open(bface_file, 'w+') as f:
                for (key, value) in self.bfaceMap.items():
                    content = str(key) + '#' + value + '\n'
                    f.writelines(content)
                f.close()
        self.save_ignore()
    
    def save_ignore(self):
        with open(ignore_file, 'w+') as f:
            data = { 'QQID': self.ignoreList, 'keywords': self.keywords, 'pinyinwords': self.banwords }
            logging.info(data)
            f.write(json.dumps(data))
            f.close()

    # def load_config(self):
    #     with open(config_file, 'r') as f:
    #         data = json.load(f)
    #         self.spyIP = str(data['spyIP'])

    def load_ignore(self):
        with open(ignore_file, 'r') as f:
            data = json.load(f)
            self.ignoreList = [int(n) for n in data['QQID']]
            self.keywords = [str(n) for n in data['keywords']]
            self.banwords = [str(n) for n in  data['pinyinwords']]
            f.close()

    def load_admin(self):
        with open(admin_file, 'r') as f:
            data = json.load(f)
            self.adminList = [int(n) for n in data]
            f.close()
    
    def load_bface(self):
        with open(bface_file, 'r') as f:
            for line in f:
                res = line.split('#')
                if res is None or len(res) <= 1:
                    continue
                key = res[0]
                value = res[1]
                self.bfaceMap[key] = value[:-1]
            f.close()

    def load_voice(self):
        with open(voice_config, 'r') as f:
            data = json.load(f)
            self.idolTable = [str(s) for s in data['voice']]
            self.speakerImage = [str(s) for s in data['v_image']]
            f.close()

    def load_invoker(self):
        with open(invoker_skill, 'r') as f:
            data = json.load(f)
            for (key, value) in data.items():
                skillName = str(value['skill_name'])
                audioNum = int(value['audio_files_num'])
                self.invokerSkill[str(key)] = {'skillName': skillName, 'audioNum': audioNum}
            f.close()

    def load_cards(self):
        self.cm = CardManager(card_data)
        logging.info('card info load success')

    def check_keywords(self, key):
        if 'CQ' in key:
            return True
        for word in self.keywords:
            if word in key:
                return True
        for word in self.banwords:
            if word in key:
                return True
        pystr = "".join(lazy_pinyin(unicode(key, 'gbk'), errors='ignore'))
        for word in self.banwords:
            if word in pystr:
                return True
        return False

    def refresh(self):
        for key in self.members:
            self.members[key].refresh()
        for (key, value) in self.saveExp.items():
            value['msg'] = 0
            value['expTime'] = 0
            value['luckyRate'] = 0
            value['drawTime'] = 0

    def explosion(self, QQID):
        member = self.members[QQID]
        if member is None or member.exposionNum >= maxExposionTime: 
            return "?", "?"
        preLevel = member.levelName
        exp = random.randint(0, 30 + int(member.levelExp/10))
        member.addExpR(exp)
        member.exposionNum += 1
        return preLevel, member.levelName

    def harm(self, QQID):
        member = self.members[QQID]
        if member:
            preLevel = member.levelName
            exp = random.randint(int(member.levelExp/10), 30 + int(member.levelExp)/5)
            member.decreaseExpR(exp)
            return preLevel, member.levelName
        return "?", "?"
    
    def load_members(self, fromGroup):
        logging.info("!!!")
        if self.loadExp is None or len(self.loadExp) == 0:
            return
        hour = datetime.now().hour
        logging.info("???")
        for (key, value) in self.loadExp.items():
            logging.info(key)
            info = CQGroupMemberInfo(CQSDK.GetGroupMemberInfoV2(fromGroup, key))
            logging.info(info)
            if info:
                member = Member(info)
                member.firstMsgHour = hour
                member.lastMsgHour = hour
                member.load(value['exp'], value['level'], value['msg'], value['expTime'])
                self.members[key] = member

    def authority(self, fromGroup, QQID):
        if QQID in self.adminList:
            return True
        else:
            CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '你无权进行此操作' )
            return False

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

    def addBanword(self, fromGroup, QQID, word):
        if self.authority(fromGroup, QQID):
            value = ''.join(lazy_pinyin(unicode(word, 'gbk'), errors='ignore'))
            logging.info(value)
            self.banwords.append(value)
            try:
                CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + "知道了，我会无视" + str(word) + "的")
            except Exception as e:
                logging.exception(e)

    def downloadCalcImg(url):
        logging.info(url)
        r = requests.get(str(url))
        logging.info("yes")
        filename = sourcePath + 'calc.gif'
        logging.info(filename)
        open(filename, "wb").write(r.content)

    def calc(self, fromGroup, QQID, inpt):
        wapr = WolframAlphaResult(inpt)
        result, img = wapr.calcResult()
        if result:
            CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '结果是：' + str(result))
            if img:
                logging.info("???")
                r = requests.get(str(img))
                logging.info("yes")
                filename = sourcePath + 'calc.gif'
                logging.info(filename)
                open(filename, "wb").write(r.content)
                CQSDK.SendGroupMsg(fromGroup, str(CQImage('calc.gif')))
        else:
            CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '输入有误')

    def emojiGeneration(self, fromGroup, QQID, para):
        pass

    def calcInvokerSkill(self, inpt):
        sum = 0
        stable = {'q': 9, 'w': 3, 'e': 1}
        for s in inpt:
            sum += stable[s]
        return sum

    def invoker(self, fromGroup, QQID, para=None):
        logging.info("invoke")
        path = 'Invoker/'
        logging.info(para)
        audioPrefix = path + 'Invo_ability_'
        logging.info(audioPrefix)
        audioFilePath = ''
        skillName = ''
        logging.info(para)
        if para is None:
            skillIndex = str(invokerSkillIndex[0, random.randint(0, len(invokerSkillIndex) - 1)])
            skill = self.invokerSkill[skillIndex]
            audioIndex = str(random.randint(1, skill['audioNum']))
            audioPostfix = audioIndex.zfill(2)
            skillName = skill['skillName']
            audioFilePath = audioPrefix + skill['skillName'] + '_' + audioPostfix + '.mp3'
        else:
            if len(para) != 3:
                CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '施法出现错误？')
                self.invokerFail(fromGroup)
                return
            regix = '^[qwe]{0,3}$'
            pat = re.compile(regix)
            if pat.match(para):
                ret = str(self.calcInvokerSkill(para))
                skill = self.invokerSkill[ret]
                audioIndex = str(random.randint(1, skill['audioNum']))
                audioPostfix = audioIndex.zfill(2)
                skillName = skill['skillName']
                audioFilePath = audioPrefix + skill['skillName'] + '_' + audioPostfix + '.mp3'
            else:
                CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '咒语记混了')
                self.invokerFail(fromGroup)
                return
        try:
            CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '释放了' + skillName)
            CQSDK.SendGroupMsg(fromGroup, str(CQRecord(audioFilePath)))
        except Exception as e:
            logging.exception(e)

    def invokerFail(self, fromGroup):
        index = str(random.randint(1, 13)).zfill(2)
        audioFilePath = 'Invoker/' + 'Invo_failure_' +  index + '.mp3'
        CQSDK.SendGroupMsg(fromGroup, str(CQRecord(audioFilePath)))

    def drawQuery(self, fromGroup, QQID):
        member = self.members[QQID]
        remainingDrawTimes = member.drawLimit - member.drawTimes
        CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '\n每日抽卡次数：' + str(member.drawLimit) + '\n今日已用次数：' + str(member.drawTimes) + '\n剩余可用次数：' + str(remainingDrawTimes))

    def draw(self, fromGroup, QQID, para):
        logging.info(para)
        member = self.members[QQID]
        if member.drawTimes >= member.drawLimit:
            try:
                CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '不氪金还想抽卡？')
            except Exception as e:
                return
        else:
            para = para.lower()
            if 'x' in para:
                index = para.rindex('x')
                key = para[0:index]
                times = para[index+1:]
                key = self.cm.findPool(key)
                if key is None:
                    logging.info("f0")
                    CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '没有此卡池' + str(key))
                    return
                if not times.isdigit() or int(times) <= 0:
                    CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '抽卡次数有误')
                    return
                times = int(times)
                if times > 10:
                    times = 10
                remainingDrawTimes = member.drawLimit - member.drawTimes
                if times > remainingDrawTimes:
                    times = remainingDrawTimes
                logging.info(times)
                result = self.cm.draw(key, times)
                if result is not None:
                    member.drawTimes += times
                    remainingDrawTimes = member.drawLimit - member.drawTimes
                    retInfo = ''
                    if remainingDrawTimes == 0:
                        retInfo = '你今日的抽卡次数已经用完'
                    else:
                        retInfo = '你今日还有' + str(remainingDrawTimes) + '次抽卡机会'
                    retCards = ''
                    for card in result:
                        retCards += str(CQImage(card.image))
                    logging.info(retCards)
                    CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '\n' + retCards + '\n' + retInfo)
                else:
                    CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '你的老婆神秘失踪了')
                

    def downloadBface(self, url, name):
        try:
            r = requests.get(url, timeout=defaultTimeout)
        except Exception as e:
            return False
        logging.info(sourcePath + name)
        open(sourcePath + name, 'wb').write(r.content)
        return True

    def getBfaceUrl(self, imageName):
        url = ''
        with open(sourcePath + imageName + '.cqimg', 'r+') as f:
            lineCount = 0
            for line in f:
                lineCount += 1
                if lineCount % 6 == 0:
                    url = line[4:]
                    logging.info(url)
                    break
            f.close()
        return url

    def learnBface(self, fromGroup, QQID, para):
        if para is None or para == '' or para.find('#') == -1:
            return
        results = para.split('#')
        key = results[0]
        if self.check_keywords(key):
            CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '讨厌，群主娘不学%>_<%')
            return
        if self.bfaceMap.has_key(key):
            if self.authority(fromGroup, QQID) == False:
                return
        value = results[1]
        if value == '':
            logging.info("???")
            self.learnBuffer[QQID] = key
            return
        if value.find('\n') == 1 or len(value) > 500:
            CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '这个太难了，群主娘学不会T_T')
            return
        # image
        url = ''
        logging.info("f1")
        if value.find('CQ:image'):
            imageName = value[value.index('=')+1:-1]
            logging.info(imageName)
            url = self.getBfaceUrl(imageName)
            logging.info(url)
            self.downloadBface(url, imageName)
            logging.info("f2")
        self.bfaceMap[key] = value
        try:
            CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '知道了!' + str(key) + '->' + value)
        except Exception as e:
            logging.exception(e)

    def learnBfaceAsyn(self, fromGroup, QQID, value):
        if value is None or value == '':
            return
        if value.find('\n') == 1 or len(value) > 500:
            CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '这个太难了，群主娘学不会T_T')
            return
        # image
        url = ''
        if value.find('CQ:image'):
            imageName = value[value.index('=')+1:-1]
            url = self.getBfaceUrl(imageName)
            self.downloadBface(url, imageName)
        key = self.learnBuffer[QQID]
        self.bfaceMap[key] = value
        del self.learnBuffer[QQID]
        try:
            CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '知道了!' + str(key) + '->' + value)
        except Exception as e:
            logging.exception(e)

    def forget(self, fromGroup, QQID, para):
        if para is None or para == '':
            return
        if self.authority(fromGroup, QQID) == False:
            return
        key = str(para)
        if self.bfaceMap.has_key(key):
            del self.bfaceMap[key]
            retMsg = str(CQAt(QQID)) + str(key) + '代表的是什么呢?_?，我已经记不清楚了呢(遗忘成功!)'
        else:
            retMsg = str(CQAt(QQID)) + '我还没学过这个词呀( ⊙ o ⊙ )！'
        try:
            CQSDK.SendGroupMsg(fromGroup, retMsg)
        except Exception as e:
            logging.exception(e)

    def list(self, fromGroup):
        if len(self.bfaceMap) > 0:
            content = '现在记住的姿势有\n'
            for key in self.bfaceMap.keys():
                content += (str(key) + ' ')
        else:
            content = '我还什么都不会呢%>_<%'
        try:
            CQSDK.SendGroupMsg(fromGroup, content)
        except Exception as e:
            logging.exception(e)

    def roll(self, fromGroup, QQID, para=None):
        max = 100
        if para is not None and para != '':
            nums = re.findall(r"\d+", para)
            if nums:
                max = int(nums[0])
        logging.info(max)
        result = random.randint(0, max)
        res_normlize = 100 * result / max
        member = self.members[QQID]
        if member is None:
            return
        member.rollSum += res_normlize
        member.rollNum += 1
        try:
            CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '掷出了' + str(result) + '\n')
        except Exception as e:
            logging.exception(e)

    def sendAudio(self, fromGroup, para):
        if para not in audioTable.keys():
            return
        audioFile = '/' + specAudioPath + audioTable[para]
        logging.info(audioFile)
        try:
            CQSDK.SendGroupMsg(fromGroup, str(CQRecord(audioFile)))
        except Exception as e:
            logging.exception(e)


    def speak(self, fromGroup, QQID, tag=None):
        path = audioPath
        speaker = ''
        if tag is not None and tag != '':
            findTag = False
            for key in self.idolTable:
                keyLower = key.lower()
                if keyLower.find(tag.lower()) >= 0:
                    speaker = key
                    path += speaker
                    findTag = True
                    break
            if findTag == False:
                try:
                    CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '语音库中还没有这个音源%>_<%')
                except Exception as e:
                    logging.exception(e)
                return
        else:
            speakerNum = random.randint(0, len(self.idolTable) - 1)
            speaker = self.idolTable[speakerNum]
            path += speaker
        files = os.listdir(path)
        num = random.randint(0, len(files) - 1)
        filename = '/' + speaker + '/' + str(files[num])
        retMsg = speaker
        if speaker in self.speakerImage:
            speakerImgDist = sourcePath + speaker
            imgFiles = os.listdir(speakerImgDist)
            imgNum = random.randint(0, len(imgFiles) - 1)
            imgFilename = '/' + speaker + '/' + str(imgFiles[imgNum])
            retMsg += '\n' + str(CQImage(imgFilename))
        try:
            CQSDK.SendGroupMsg(fromGroup, retMsg)
            CQSDK.SendGroupMsg(fromGroup, str(CQRecord(filename)))
        except Exception as e:
            logging.exception(e)

    def repeat(self, fromGroup, msg):
        if self.msgBuffer.has_key(fromGroup) and self.msgBuffer[fromGroup] == msg:
            if not self.lastRepeat.has_key(fromGroup) or (self.lastRepeat.has_key(fromGroup) and self.lastRepeat[fromGroup] != msg):
                CQSDK.SendGroupMsg(fromGroup, msg)
                self.lastRepeat[fromGroup] = msg
        self.msgBuffer[fromGroup] = msg

    def drive(self, fromGroup, QQID, tag=None):
        files = os.listdir(imagePath)
        num = random.randint(0, len(files))
        filename = '/comic/' + str(files[num])
        try:
            CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + str(CQImage(filename)))
        except Exception as e:
            logging.exception(e)

    def tagRecommend(self, fromGroup, QQID, tag=None):
        full_url = yande_url + 'tag.json?order=count&limit=40'
        content = ''
        if tag is None:
            pageNumber = random.randint(0, 10)
            full_url += '&page=' + str(pageNumber)
            tagIndex = [random.randint(0, 39) for _ in range(5)]
            try:
                response = requests.get(full_url, timeout=10)
            except Exception as e:
                CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '咋回事儿啊,网络好像开小差了')
                return
            json_result = json.loads(response.text)
            if len(json_result) == 0:
                try:
                    CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '1')
                except Exception as e:
                    logging.exception(e)
                return False
            else:
                content += '1\n'
                for k in tagIndex:
                    content += str(json_result[k]['name']) + ' '
        else:
            full_url += '&name=' + str(tag)
            try:
                response = requests.get(full_url, timeout=10)
            except Exception as e:
                CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '1')
                return
            json_result = json.loads(response.text)
            result_length = len(json_result)
            if json_result is None or result_length == 0:
                try:
                    CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '1')
                except Exception as e:
                    logging.info(e)
                return False
            else:
                content += '1\n'
                maxTag = 5 if result_length >= 5 else result_length
                for k in range(0, maxTag):
                    content += str(json_result[k]['name']) + ' '
        try:
            CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + content)
        except Exception as e:
            logging.exception(e)
        return True

    
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
            response = requests.get(full_url, timeout=defaultTimeout)
        except requests.exceptions.Timeout:
            CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '1')
            return
        except Exception as e:
            CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '1')
            return
        json_result = json.loads(response.text)
        logging.info(json_result)
        if len(json_result) == 0:
            return False
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
            try:
                image = requests.get(image_url, timeout=defaultTimeout)
            except Exception as e:
                CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '1')
                return
            open(filepath, 'wb').write(image.content)
        relativePath = '/comic/' + filename
        try:
            CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + str(CQImage(relativePath)))
        except Exception as e:
            logging.exception(e)
        return True

    def drive_online(self, fromGroup, QQID, tag=None):
        full_url = yande_url + 'post.json'
        if tag is not None:
            tagPara = '?tags=' + str(tag)
            full_url += tagPara
        else:
            page = random.randint(0, 100)
            pagePara = '?page=' + str(page)
            full_url += pagePara
        full_url += '&limit=100'
        try:
            response = requests.get(full_url, timeout=defaultTimeout)
        except requests.exceptions.Timeout:
            CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '1')
            return
        except Exception as e:
            CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '1')
            return     

        json_result = json.loads(response.text)
        if len(json_result) == 0:
            ret = self.drive_from_danbooro(fromGroup, QQID, tag)
            if ret == False:
                try:
                    CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '1%>_<%1')
                except Exception as e:
                    logging.exception(e)
                self.tagRecommend(fromGroup, QQID, tag)
            return
        illust = json_result[random.randint(0, len(json_result) - 1)]
        id = illust['id']
        image_url = illust['file_url']
        extension = illust['file_ext']
        size = illust['file_size']
        logging.info("sss: " + str(size))
        if size >= maxImageSize:
            sample_size = illust['sample_file_size']
            logging.info(sample_size)
            if sample_size >= maxImageSize:
                try:
                    CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '1')
                except Exception as e:
                    logging.exception(e)
                return
        image_url = illust['sample_url']
        filename = str(id) + '_yande.' + extension
        filepath = imagePath + filename
        if not os.path.exists(filepath):
            try:
                logging.info("begin download")
                image = requests.get(image_url, timeout=defaultTimeout)
            except Exception as e:
                CQSDK.SendGroupMsg(fromGroup, '1')
                return
            open(filepath, 'wb').write(image.content)
        relativePath = '/comic/' + filename
        try:
            CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + str(CQImage(relativePath)))
        except Exception as e:
            logging.exception(e)

    def spy(self, fromGroup, QQID, sendTime):
        # avatarUrl = base64.b64encode('http://q.qlogo.cn/headimg_dl?dst_uin=' + str(QQID) + '&spec=100')
        # url = self.spyIP + '/1.php?username=' + str(sendTime) + '&url=' + str(avatarUrl)
        # CQSDK.SendGroupMsg(fromGroup, str(CQShare(' ', '??????', '???????????...', url)))
        # dataUrl = self.spyIP + '/' + str(sendTime) + '.txt'
        # tLast = datetime.now() + timedelta(seconds = 5)
        # count = 0
        # while datetime.now() < tLast:
        #     count = count + 1
        # r = requests.get(dataUrl)
        # while not r:
        #     r = requests.get(dataUrl)
        # r = requests.get(dataUrl)
        # data = str(r.text)
        # IPArray = [str(l.split(',')[0]) for l in data.split('#')[:-1]]
        # retMsg = '??????锟斤拷????IP???\n'
        # for ip in IPArray:
        #     r = requests.get('http://ip138.com/ips138.asp?ip=' + str(ip))
        #     r.encoding = 'GBK'
        #     soup = BeautifulSoup(r.text, 'html.parser')
        #     data = soup.find('ul', class_='ul1')
        #     address = data.find('li').text
        #     logging.info(address)
        #     retMsg += str(ip) + ' ' + str(address) + '\n'
        # CQSDK.SendGroupMsg(fromGroup, retMsg)
        pass
        
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
            logging.info("flag0")
            if hour == 23 and self.isRefresh == 0:
                self.isRefresh = 1
            elif hour == 0 and self.isRefresh == 1:
                self.refresh()
                self.save()
                self.isRefresh = 0
            logging.info("flag1")
            self.msgCount += 1
            if self.msgCount == self.saveRoutine:
                self.save()
                self.msgCount = 0
            logging.info("flag2")

            if fromGroup == groupID[0]:
                if fromQQ not in self.members:
                    info = CQGroupMemberInfo(CQSDK.GetGroupMemberInfoV2(fromGroup, fromQQ))
                    newMember = Member(info)
                    newMember.firstMsgHour = hour
                    newMember.lastMsgHour = hour
                    self.members[fromQQ] = newMember
                self.members[fromQQ].addExp(int(hour), sendTime)
                p = random.random()
                if p < self.exProbility and self.members[fromQQ].exposionNum < maxExposionTime:
                    preLevel, afterLevel = self.explosion(fromQQ)
                    if preLevel != afterLevel:
                        retMsg = str(CQAt(fromQQ)) + "在修炼中顿悟，实力获得大幅提升，由 " + preLevel + " 提升到 " + afterLevel
                    else:
                        retMsg = str(CQAt(fromQQ)) + "在修炼中顿悟，感觉内力有了小幅提升"
                    try:
                        CQSDK.SendGroupMsg(fromGroup, retMsg)
                    except Exception as e:
                        logging.exception(e)
            
            self.repeat(fromGroup, msg)

            msg = msg.replace('！', '!')

            if fromQQ in self.learnBuffer.keys():
                self.learnBfaceAsyn(fromGroup, fromQQ, msg)
            
            logging.info("flag3")
            content = msg.lower()
            result = re.findall(self._key_regex, content)
            if result:
                cmd = result[0]
                logging.info(cmd)
                para = msg[len(cmd):]
                if len(para) > 0:
                    while para[0] == ' ':
                        para = para[1:]
                if cmd == '.xx' and fromGroup == groupID[0]:
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
                elif cmd == '!learn':
                    self.learnBface(fromGroup, fromQQ, para)
                elif cmd == '!forget':
                    self.forget(fromGroup, fromQQ, para)
                elif cmd == '!list':
                    self.list(fromGroup)
                elif cmd == '!tag':
                    self.tagRecommend(fromGroup, fromQQ, para)
                elif cmd == '!banword':
                    self.addBanword(fromGroup, fromQQ, para)
                elif cmd == '!calc':
                    self.calc(fromGroup, fromQQ, para)
                elif cmd == '!invoke':
                    self.invoker(fromGroup, fromQQ, para)
                elif cmd == '!draw':
                    self.draw(fromGroup, fromQQ, para)
                elif cmd == '!check':
                    self.drawQuery(fromGroup, fromQQ)
                elif cmd == '!spy':
                    msg='没有' #

            
            logging.info("flag4")

            if msg in self.bfaceMap.keys():
                try:
                    CQSDK.SendGroupMsg(fromGroup, self.bfaceMap[msg])
                except Exception as e:
                    logging.exception(e)

            if msg in audioTable.keys():
                self.sendAudio(fromGroup, msg)

            logging.info("flag6")


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
            CQSDK.SendGroupMsg(groupID[0], '1')
            logging.info('OnEvent_Menu02: drive function off')
        else:
            self.driveOn = True
            CQSDK.SendGroupMsg(groupID[0], '2')
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

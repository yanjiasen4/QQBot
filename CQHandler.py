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

groupID = [79177174, 487308083, 259641925, 484271101]
yande_url = 'https://yande.re/'
danbooru_url = 'http://danbooru.donmai.us/'
ignore_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'ignore.json')
admin_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'admin.json')
bface_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'bface.data')
config_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'config.json')
voice_config = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'voice.json')
invoker_skill = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'invoker.json')

maxImageSize = 4000000
maxExposionTime = 1

import CQSDK
from CQGroupMemberInfo import CQGroupMemberInfo
from CQMessage import CQAt, CQImage, CQRecord, CQShare

from pypinyin import pinyin, lazy_pinyin
import pypinyin
from wapresult import WolframAlphaResult

import math
import time
from datetime import *
import re
import random

expTable = [100, 300, 800, 1500, 3800, 9000, 22000, 48000, 90000, 140000, 200000]
levelTable = ['淬体', '炼气', '筑基', '金丹', '辟谷', '元婴', '洞虚', '分神', '大乘', '渡劫', '仙人']
subLevelTable = ['一层', '二层', '三层', '四层', '五层', '六层', '七层', '八层', '九层', '圆满']
invokerSkillIndex = [0, 3, 5, 7, 9, 11, 13, 15, 19, 21, 27]

sourcePath = 'F:/酷Q Pro/data/image/'
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
        self._key_regex = re.compile('^.xx|!save|!idol|!drive|!rank|!roll|!learn|!forget|!list|!tag|!banword|!calc|!invoke|!spy')
        self.keywords = []
        self.banwords = []
        self._data_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'xx.data')
        self.exProbility = 0.003
        self.msgCount = 0
        self.isRefresh = 0
        self.ignoreList = []
        self.adminList = []
        self.idolTable = []
        self.loadExp = {}
        self.saveExp = {}
        self.wordMap = {}
        self.bfaceMap = {}
        self.invokerSkill = {}
        self.load()
        self.load_members(groupID[0])
        self.driveOn = True
        logging.info(self.adminList)
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
        self.load_bface()
        self.load_voice()
        self.load_ignore()
        self.load_admin()
        self.load_invoker()
        self.load_config()

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

    def load_config(self):
        with open(config_file, 'r') as f:
            data = json.load(f)
            self.spyIP = str(data['spyIP'])

    def load_ignore(self):
        with open(ignore_file, 'r') as f:
            data = json.load(f)
            self.ignoreList = [int(n) for n in data['QQID']]
            self.keywords = [str(n) for n in data['keywords']]
            self.banwords = [str(n) for n in  data['pinyinwords']]
            logging.info(self.banwords)
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
            logging.info("???")
            for (key, value) in data.items():
                skillName = str(value['skill_name'])
                audioNum = int(value['audio_files_num'])
                self.invokerSkill[str(key)] = {'skillName': skillName, 'audioNum': audioNum}
                logging.info("{0},{1}".format(skillName,audioNum))
            f.close()
        logging.info(self.invoker)

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
        if self.loadExp is None or len(self.loadExp) == 0:
            return
        hour = datetime.now().hour
        for (key, value) in self.loadExp.items():
            logging.info("t")
            logging.info(key)
            info = CQGroupMemberInfo(CQSDK.GetGroupMemberInfoV2(fromGroup, key))
            member = Member(info)
            member.firstMsgHour = hour
            member.lastMsgHour = hour
            member.load(value['exp'], value['level'], value['msg'], value['expTime'])
            self.members[key] = member

    def authority(self, fromGroup, QQID):
        logging.info(QQID)
        logging.info(QQID in self.adminList)
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
            CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '结果是: ' + str(result))
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
            logging.info("Invo1")
            skillIndex = str(invokerSkillIndex[0, random.randint(0, len(invokerSkillIndex) - 1)])
            skill = self.invokerSkill[skillIndex]
            audioIndex = str(random.randint(1, skill['audioNum']))
            audioPostfix = audioIndex.zfill(2)
            skillName = skill['skillName']
            audioFilePath = audioPrefix + skill['skillName'] + '_' + audioPostfix + '.mp3'
        else:
            logging.info("Invo2")
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
            logging.info("Invo3")
            CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '释放了' + skillName)
            CQSDK.SendGroupMsg(fromGroup, str(CQRecord(audioFilePath)))
        except Exception as e:
            logging.exception(e)

    def invokerFail(self, fromGroup):
        index = str(random.randint(1, 13)).zfill(2)
        audioFilePath = 'Invoker/' + 'Invo_failure_' +  index + '.mp3'
        CQSDK.SendGroupMsg(fromGroup, str(CQRecord(audioFilePath)))

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
        logging.info(value)
        if value.find('\n') == 1 or len(value) > 500:
            CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '这个太难了，群主娘学不会T_T')
            return
        self.bfaceMap[key] = value
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
            CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '掷出了' + str(result) + '\n今天的运气指数为(还没做)')
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
            logging.info("in")
            speakerImgDist = sourcePath + speaker
            logging.info(speakerImgDist)
            imgFiles = os.listdir(speakerImgDist)
            logging.info(imgFiles)
            imgNum = random.randint(0, len(imgFiles) - 1)
            imgFilename = '/' + speaker + '/' + str(imgFiles[imgNum])
            logging.info(imgFilename)
            retMsg += '\n' + str(CQImage(imgFilename))
        try:
            CQSDK.SendGroupMsg(fromGroup, retMsg)
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

    def tagRecommend(self, fromGroup, QQID, tag=None):
        full_url = yande_url + 'tag.json?order=count&limit=40'
        content = ''
        if tag is None:
            pageNumber = random.randint(0, 10)
            full_url += '&page=' + str(pageNumber)
            tagIndex = [random.randint(0, 39) for _ in range(5)]
            try:
                response = requests.get(full_url)
            except Exception as e:
                CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '咋回事儿啊,网络好像开小差了')
                return
            json_result = json.loads(response.text)
            if len(json_result) == 0:
                try:
                    CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '已经没有什么tag可以推荐了')
                except Exception as e:
                    logging.exception(e)
                return False
            else:
                content += '群主娘为你推荐了几个tag哦\n'
                for k in tagIndex:
                    content += str(json_result[k]['name']) + ' '
        else:
            logging.info("f1")
            full_url += '&name=' + str(tag)
            try:
                response = requests.get(full_url)
            except Exception as e:
                CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '咋回事儿啊,网络好像开小差了')
                return
            json_result = json.loads(response.text)
            result_length = len(json_result)
            if json_result is None or result_length == 0:
                try:
                    CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '还是找不到相关tag哦')
                except Exception as e:
                    logging.info(e)
                return False
            else:
                content += '你要找的tag是不是\n'
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
            response = requests.get(full_url)
        except requests.exceptions.ConnectTimeout:
            CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '老司机翻车啦！')
            return
        except Exception as e:
            CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '神秘的东方力量导致此次开车失败')
            return
        json_result = json.loads(response.text)
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
            image = requests.get(image_url)
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
                    CQSDK.SendGroupMsg(fromGroup, str(CQAt(QQID)) + '找不到你想要的tag%>_<%，群主娘在尝试为你推荐相关tag哦↖(^ω^)↗')
                except Exception as e:
                    logging.exception(e)
                self.tagRecommend(fromGroup, QQID, tag)
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

    def spy(self, fromGroup, QQID, sendTime):
        avatarUrl = base64.b64encode('http://q.qlogo.cn/headimg_dl?dst_uin=' + str(QQID) + '&spec=100')
        url = self.spyIP + '/1.php?username=' + str(sendTime) + '&url=' + str(avatarUrl)
        CQSDK.SendGroupMsg(fromGroup, str(CQShare(' ', '谁在窥屏', '正在收集数据...', url)))
        dataUrl = self.spyIP + '/' + str(sendTime) + '.txt'
        tLast = datetime.now() + timedelta(seconds = 5)
        count = 0
        while datetime.now() < tLast:
            count = count + 1
        r = requests.get(dataUrl)
        while not r:
            r = requests.get(dataUrl)
        logging.info(r.text)
        r = requests.get(dataUrl)
        logging.info(r.text)
        r = requests.get(dataUrl)
        data = r.text
        IPArray = [str(l.split(',')[0]) for l in data.split('#')[:-1]]
        logging.info(IPArray)
        retMsg = '窥屏的小伙伴的IP地址\n'
        for ip in IPArray:
            r = requests.get('http://ip138.com/ips138.asp?ip=' + str(ip))
            r.encoding = 'GBK'
            soup = BeautifulSoup(r.text, 'html.parser')
            data = soup.find('ul', class_='ul1')
            address = data.find('li').text
            logging.info(address)
            retMsg += str(ip) + ' ' + str(address) + '\n'
        CQSDK.SendGroupMsg(fromGroup, retMsg)
        
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

            logging.info("flag3")
            msg = msg.replace('！', '!')
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
                    self.tagRecommend(fromGroup, fromQQ)
                elif cmd == '!banword':
                    self.addBanword(fromGroup, fromQQ, para)
                elif cmd == '!calc':
                    self.calc(fromGroup, fromQQ, para)
                elif cmd == '!invoke':
                    self.invoker(fromGroup, fromQQ, para)
                elif cmd == '!spy':
                    self.spy(fromGroup, fromQQ, sendTime)
            
            logging.info("flag4")

            logging.info("flag5")

            if msg in self.bfaceMap.keys():
                try:
                    CQSDK.SendGroupMsg(fromGroup, self.bfaceMap[msg])
                except Exception as e:
                    logging.exception(e)
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

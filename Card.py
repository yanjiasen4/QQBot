# -*- coding:gbk -*-

import random
import math
import json

LatiaoPools = ['Summer17']

class Card:

    def __init__(self, index, name, image, probability, rare, type):
        self.index = index
        self.name = name
        self.image = image
        self.probability = probability
        self.rare = rare
        self.type = type # 0: normal, 1: special, 2: unlocked
        self.rewards = []

class CardPool:

    def __init__(self, name):
        self.name = name
        self.cards = []
        self.cardsNum = 0
        self.rewardCards = []
        self.rewardCardsNum = 0
        self.probabilityAcc = []
        self.rareName = []
        self.maxRareLevel = 0
        self.rewardsMap = {}

    def loadConfig(self, config):
        self.maxRareLevel = int(config[0])
        self.rareName = config[1:]

    def loadCards(self, pkg):
        for line in pkg:
            # cards collection rule
            if line[0] == '!':
                paras = line[1:].split(':')
                needs = paras[0].split(',')
                rewards = paras[1].split(',')
                for rc in rewards:
                    self.rewardsMap[rc] = needs
                for card in needs:
                    for pcard in self.cards:
                        print(pcard.index)
                        if pcard.index == card:
                            pcard.type = 1
                            pcard.rewards = rewards
                            break
            else:
                paras = line.split(',')
                card = Card(paras[0],paras[1],self.name[0] + '/' + paras[2],float(paras[3]),int(paras[4]),int(paras[5]))
                self.addCard(card)

    def normalizeProb(self, cardsProb):
        totalProb = 0
        for prob in cardsProb:
            totalProb += prob
        for i in range(len(cardsProb)):
            cardsProb[i] /= totalProb
        return cardsProb
        
    def addCard(self, card):
        if card.type == 2:
            self.rewardCards.append(card)
            self.rewardCardsNum += 1
        else:
            self.cards.append(card)
            self.cardsNum += 1

    def getCardByIndex(self, index):
        for card in self.cards:
            if index == card.index:
                return card

    def getRewardCardByIndex(self, index):
        for card in self.rewardCards:
            if index == card.index:
                return card

    def calcProbAcc(self, cardsProb):
        cardsNum = len(cardsProb)
        currProb = 0
        index = 0
        probabilityAcc = [0 for i in range(cardsNum)]
        for prob in cardsProb:
            currProb += prob
            probabilityAcc[index] = currProb
            index += 1
        return probabilityAcc

    def draw(self, times, unlockedCards=None):
        if len(self.cards) == 0: return
        else:
            result = []
            resultRare = [0 for i in range(self.maxRareLevel+1)]
            cardsProb =  []
            cards = []
            for card in self.cards:
                cardsProb.append(card.probability)
                cards.append(card)
            if unlockedCards is not None and len(unlockedCards) > 0:
                for index in unlockedCards:
                    card = self.getRewardCardByIndex(index)
                    cardsProb.append(card.probability)
                    cards.append(card)
            cardsProb = self.normalizeProb(cardsProb)
            probabilityAcc = self.calcProbAcc(cardsProb)
            for i in range(times):
                res = random.random()
                index = 0
                for prob in probabilityAcc:
                    if prob < res:
                        index += 1
                    else:
                        result.append(cards[index])
                        resultRare[cards[index].rare] += 1
                        break
        return result, resultRare

    def canUnlockReward(self, indics):
        targetRewards = []
        target = []
        cards = []
        for id in indics:
            cards.append(self.getCardByIndex(id))
        for card in cards:
            if card.type != 1:
                return False
            if card.rewards not in targetRewards:
                tmp = {'rewards': card.rewards, 'collect': []}
                tmp['collect'].append(card.index)
                targetRewards.append(card.rewards)
                target.append(tmp)
            else:
                for tmp in target:
                    if tmp['rewards'] == card.rewards:
                        tmp['collect'].append(card.index)

        result = []
        for tmp in target:    
            for reward in tmp['rewards']:
                if reward in self.rewardsMap.keys():
                    tmp['collect'].sort()
                    if tmp['collect'] == self.rewardsMap[reward]:
                        result.append(reward)

        return result

class CardManager:

    def __init__(self, filename):
        self.cardsPools = {}
        with open(filename, 'r+') as f:
            cardsPoolsData = f.read().split('#')
            for pools in cardsPoolsData:
                if pools is None or pools == '': continue
                lines = pools.splitlines()
                prefix = lines[0].split(',')
                config = lines[1].split(',')
                content = lines[2:]
                cp = CardPool(prefix)
                cp.loadConfig(config)
                cp.loadCards(content)
                self.cardsPools[prefix[0]] = cp
            
            f.close()

    def draw(self, pool, times, unlockedCards=None):
        if pool in self.cardsPools.keys():
            return self.cardsPools[pool].draw(times, unlockedCards)
        else:
            return None

    def getPoolRareName(self, pool):
        key = self.findPool(pool)
        if key in self.cardsPools.keys():
            return self.cardsPools[key].rareName
        else:
            return None

    def findPool(self, para):
        for (key,value) in self.cardsPools.items():
            if para in value.name:
                return key
        return None

    def getUnlockedCards(self, pool, scards):
        key = self.findPool(pool)
        if key in self.cardsPools.keys():
            return self.cardsPools[key].canUnlockReward(scards)
        else:
            return None

    def getRewardCardByIndex(self, pool, index):
        key = self.findPool(pool)
        if key in self.cardsPools.keys():
            return self.cardsPools[key].getRewardCardByIndex(index)
        else:
            return None


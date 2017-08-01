# -*- coding:gbk -*-

import random
import math
import json

class Card:

    def __init__(self, name, image, probability):
        self.name = name
        self.image = image
        self.rare = 0
        self.probability = probability

class CardPool:

    def __init__(self, name):
        self.name = name
        self.cards = []
        self.cardsNum = 0
        self.probabilityAcc = []

    def loadCards(self, pkg):
        for line in pkg:
            paras = line.split(',')
            card = Card('/' + paras[0],self.name[0] + '/' + paras[1],float(paras[2]))
            self.addCard(card)
            self.cardsNum += 1

        self.normalizeProb()
        self.calcProbAcc()

    def normalizeProb(self):
        totalProb = 0
        for card in self.cards:
            totalProb += card.probability
        for card in self.cards:
            card.probability /= totalProb
        
    def addCard(self, card):
        self.cards.append(card)

    def calcProbAcc(self):
        currProb = 0
        index = 0
        self.probabilityAcc = [0 for i in range(self.cardsNum)]
        for card in self.cards:
            currProb += card.probability
            self.probabilityAcc[index] = currProb
            index += 1

    def draw(self, times):
        if len(self.cards) == 0: return
        else:
            result = []
            probabilityAcc = []
            for i in range(times):
                res = random.random()
                index = 0
                for prob in self.probabilityAcc:
                    if prob < res:
                        index += 1
                    else:
                        result.append(self.cards[index])
                        break
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
                content = lines[1:]
                cp = CardPool(prefix)
                cp.loadCards(content)
                self.cardsPools[prefix[0]] = cp
            
            f.close()

    def draw(self, pool, times):
        if pool in self.cardsPools.keys():
            return self.cardsPools[pool].draw(times)
        else:
            return None

    def findPool(self, para):
        for (key,value) in self.cardsPools.items():
            if para in value.name:
                return key
        return None


__author__ = 'Johannes'

import os
import json
import numpy as np
from sklearn.neural_network import BernoulliRBM

class DictionaryImporter(object):

    chars = {'\'':0, 'a':1, 'b':2, 'c':3, 'd':4, 'e':5, 'f':6, 'g':7, 'h':8, 'i':9, 'j':10, 'k':11, 'l':12, 'm':13, 'n':14, 'o':15, 'p':16, 'q':17, 'r':18, 's':19, 't':20, 'u':21, 'v':22, 'w':23, 'x':24, 'y':25, 'z':26, 'nochar':27}

    def __init__(self, file, prefixLength, suffixLength):
        dictionaryFHandle = open(file, 'r')
        self.prefixLength = prefixLength
        self.suffixLength = suffixLength
        self.dict = json.load(dictionaryFHandle)
        self.length = len(self.dict)
        self._train()

    def _getInputVec(self, word):
        nrChars = len(DictionaryImporter.chars)
        vec = np.zeros(shape=(nrChars * (self.prefixLength + self.suffixLength)), dtype=np.float16)
        pos = 0
        word = word.lower()
        for i in range(0, self.prefixLength):
            if i < len(word):
                vec[pos+DictionaryImporter.chars[word[i]]] = 1.0
            else:
                vec[pos+DictionaryImporter.chars['nochar']] = 1.0
            pos += nrChars

        pos = len(vec)-nrChars
        for i in range(1, self.suffixLength+1):
            if i-1 < len(word):
                vec[pos+DictionaryImporter.chars[word[-i]]] = 1.0
            else:
                vec[pos+DictionaryImporter.chars['nochar']] = 1.0
            pos -= nrChars
        return vec

    def _train(self):
        nrChars = len(DictionaryImporter.chars)
        data = np.zeros(shape=(self.length, nrChars * (self.prefixLength + self.suffixLength)), dtype=np.float16)
        for rowIdx in range(0, data.shape[0]):
            data[rowIdx] = self._getInputVec(self.dict[rowIdx][0])

        self.model = BernoulliRBM(n_components=13,learning_rate=0.17, n_iter=60)
        self.transformed = self.model.fit_transform(data)
        print np.shape(self.transformed);

    def getNearest(self, word, topK):

        encInput = self.model.transform(self._getInputVec(word))
        dists = np.ones(shape=self.length, dtype=np.float16)
        for rowIdx in range(0, len(self.transformed)):
            dists[rowIdx] = np.linalg.norm(self.transformed[rowIdx]-encInput)

        nearestIdxs = np.argsort(dists)[:topK]
        nearest = []
        for idx in nearestIdxs:
            nearest.append((str(self.dict[idx][0]), dists[idx]))

        return nearest

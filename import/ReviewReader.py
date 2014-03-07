__author__ = 'Johannes'
import json
import exceptions
import re
from operator import itemgetter

chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
struc = '.;,:-!?()\"+'
dictionary = {}
pattern = re.compile('"\b([a-zA-Z]+)\b"')


def num(s):
    try:
        flos = float(s)
        try:
            ints = int(s)
            return ints
        except exceptions.ValueError:
            return flos
    except exceptions.ValueError:
        return s


def convertData(filename):

    data = []
    dataObj = {}
    nrobjects = 0
    nrbytes = 0
    outputFile = open(filename + '_c.txt', 'w')
    outputFile.write('[')
    with open(filename + '.txt', 'rb') as inputFile:
        for line in inputFile:
            nrbytes += len(line)
            if line == '\n':
                #data.append(dataObj)
                nrobjects += 1
                outputFile.write(json.dumps(dataObj))
                outputFile.write(',\n')
                dataObj = {}
            else:
                sepPos = line.find(':')
                fieldsPath = line[:sepPos]
                value = str.strip(line[sepPos+1:len(line)-1])
                fields = fieldsPath.split('/')
                if fields[1] == 'text':
                    words = value.split(' ')
                    addToDictionary(words)
                if fields[0] not in dataObj:
                    dataObj[fields[0]] = {}
                dataObj[fields[0]][fields[1]] = num(value)
    if nrbytes > 0:
        outputFile.seek(-3, 2)
    outputFile.write(']')
    outputFile.close()

    print "totlinesize: " + str(nrbytes)
    print "#dataobjects: " + str(len(data))

def addToDictionary(words):
    for word in words:
        w = word.lower()
        match = re.search(r'[a-zA-Z\']+', w)
        if match:
            g = match.group()
            if g in dictionary:
                dictionary[g] += 1
            else:
                dictionary[g] = 1
        #m = re.match('"\b[a-zA-Z]+\b"', w, re.I)

convertData('../../data/Office_Products')

print str(len(dictionary.keys())) + " distinct words in dictionary"

dictFile = open('../../data/dict.txt', 'w+')
dictFile.write(json.dumps(dictionary))
dictFile.close()

sdictionary = []
for key in dictionary:
    sdictionary.append((key, dictionary[key]))

sdictionary = sorted(sdictionary, key=itemgetter(1), reverse=True)

sdictFile = open('../../data/sorted_dict.txt', 'w+')
sdictFile.write(json.dumps(sdictionary))
sdictFile.close()
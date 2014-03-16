__author__ = 'Johannes'

import os
import exceptions
import re
import json
import fnmatch
import elasticsearch
from operator import itemgetter


class AmazonReader(object):
    """
    Reads raw data from amazon reviews and puts them into a elasticsearch-database
    """
    index = 'amazon'
    outputFolder = 'dictionaries'
    outputFolderSamples = 'samples'
    outputDictName = 'dict.txt'
    outputSortedDictName = 'sorted_dict.txt'
    dataFileFormat = 'txt'

    dictionaryThreshold = 10

    def __init__(self, dataDir):
        self.es = elasticsearch.Elasticsearch()
        self.pathToData = dataDir
        self.dictionary = {}

    def _findDataFiles(self):
        filenames = []
        if os.path.exists(self.pathToData):
            for file in os.listdir(self.pathToData):
                if fnmatch.fnmatch(file, '*.'+AmazonReader.dataFileFormat):
                    filenames.append(file)
        return filenames

    def _num(self, s):
        try:
            flos = float(s)
            try:
                ints = int(s)
                return ints
            except exceptions.ValueError:
                return flos
        except exceptions.ValueError:
            return s

    def _addToDictionary(self, words, dict):
        for word in words:
            w = word.lower()
            match = re.search(r'[a-z]+[\'a-z]+', w)
            if match:
                g = match.group()
                if g in dict:
                    dict[g] += 1
                else:
                    dict[g] = 1

    def importAll(self):
        filenames = self._findDataFiles()

        data = []
        doc = {}
        nrDocs = 0
        nrBytes = 0
        for file in filenames:
            with open(self.pathToData + '/' + file, 'rb') as inputFile:
                for line in inputFile:
                    nrBytes += len(line)
                    if line == '\n':
                        nrDocs += 1
                        # put doc into indexedDB
                        try:
                            if doc:
                                myId = str(doc['product']['productId']) + ':' + str(doc['review']['userId'])
                                self.es.index(index=AmazonReader.index, doc_type=file, body=doc, id=myId)
                        except elasticsearch.exceptions.RequestError:
                            print doc
                        doc = {}
                    else:
                        sepPos = line.find(':')
                        fieldsPath = line[:sepPos]
                        value = line[sepPos+2:len(line)-1]
                        fields = fieldsPath.split('/')
                        if fields[1] == 'text':
                            words = value.split(' ')
                            self._addToDictionary(words)
                        if fields[0] not in doc:
                            doc[fields[0]] = {}
                        doc[fields[0]][fields[1]] = self._num(value);
        print "totlinesize: " + str(nrBytes)
        print "#dataobjects: " + str(nrDocs)

    def createCleanedDatasets(self):
        if not self.es.indices.exists(index=self.index):
            self.importAll()

        if not os.path.exists(self.pathToData + '/' + AmazonReader.outputFolderSamples):
            os.makedirs(self.pathToData + '/' + AmazonReader.outputFolderSamples)

        filenames = self._findDataFiles()
        for file in filenames:
            outputFile = open(self.pathToData + '/' + AmazonReader.outputFolderSamples + '/' + 'CL_' + file, 'w')
            recordCounter = 0
            queryBody = {"fields": ["review.text", "review.score"], "query": { "match_all": {}}}
            scrollingOpener = self.es.search(index=self.index, doc_type=file, body=queryBody,params={"scroll":"2m","search_type":"scan","size":100})
            firstScrollId = scrollingOpener['_scroll_id']
            totNrRecords = scrollingOpener['hits']['total']
            print "total#Records: " + str(totNrRecords)
            res = self.es.scroll(scroll_id=firstScrollId, params={"scroll":"2m"})

            myObj = {}
            while res['hits']['hits']:
                for record in res['hits']['hits']:
                    recordCounter += 1
                    myObj['id'] = record['_id']
                    myObj['text'] = record['fields']['review.text'][0]
                    myObj['score'] = record['fields']['review.score'][0]
                    outputFile.write(json.dumps(myObj))
                    outputFile.write('\n')
                res = self.es.scroll(scroll_id=res['_scroll_id'], params={"scroll":"2m"})
            outputFile.close()
            print "Exported " + str(recordCounter) + " Records of " + str(file) + "."

    def createDictionaries(self, threshold):
        if not self.es.indices.exists(index=self.index):
            self.importAll()

        if not os.path.exists(self.pathToData + '/' + AmazonReader.outputFolder):
            os.makedirs(self.pathToData + '/' + AmazonReader.outputFolder)

        filenames = self._findDataFiles()
        for file in filenames:
            dictionary = {}
            outputFile = open(self.pathToData + '/' + AmazonReader.outputFolder + '/' + 'DICT_' + file, 'w')
            recordCounter = 0
            queryBody = {"fields": ["review.text"], "query": { "match_all": {}}}
            scrollingOpener = self.es.search(index=self.index, doc_type=file, body=queryBody,params={"scroll":"2m","search_type":"scan","size":100})
            firstScrollId = scrollingOpener['_scroll_id']
            totNrRecords = scrollingOpener['hits']['total']
            print "total#Records: " + str(totNrRecords)
            res = self.es.scroll(scroll_id=firstScrollId, params={"scroll":"2m"})

            while res['hits']['hits']:
                for record in res['hits']['hits']:
                    recordCounter += 1
                    words = record['fields']['review.text'][0].split(' ')
                    self._addToDictionary(words, dictionary)
                res = self.es.scroll(scroll_id=res['_scroll_id'], params={"scroll":"2m"})

            sdictionary = []
            for key in dictionary:
                if dictionary[key] >= threshold:
                    sdictionary.append((key, dictionary[key]))
            sdictionary = sorted(sdictionary, key=itemgetter(1), reverse=True)
            outputFile.write(json.dumps(sdictionary))
            outputFile.close()
            print str(len(sdictionary)) + " distinct words in dictionary of " + str(file) + "."
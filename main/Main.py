__author__ = 'Johannes'
import preprocessing.DictionaryImporter as dictio

#amazonReader = dataio.AmazonReader('../../data')
#amazonReader.importAll()
#amazonReader.createCleanedDatasets()
#amazonReader.createDictionaries(3)

dictimporter = dictio.DictionaryImporter('../../data/dictionaries/DICT_Office_Products.txt', 4, 4)

print "Type 'exit' to quit."
userInput = ""
while userInput != "exit":
    userInput = raw_input("Syntactically similar words for: ")
    nearest = dictimporter.getNearest(userInput, 100)
    for neighbor in nearest:
        print neighbor
from constants import *
import pymongo

class Engine(object):

    def __init__(self):

        self.connection = pymongo.MongoClient(MONGO_URI % (USER, PASSWORD))
        db = self.connection[MONGO_DB]

        self.schools = db[SCHOOL_COLLECTION]

    def register(self, school):

        self.schools.insert_one(school)

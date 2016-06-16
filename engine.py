from constants import *

import pymongo
import time

def comp(x, y):

    if x[0] != y[0]:

        return x[0] - y[0]

    else:

        return y[1] - x[1]



class Engine(object):

    ''' Engine of the app.'''

    def __init__(self):

        ''' Initialize all Database connections'''

        connection = pymongo.MongoClient(MONGODB_SERVER, MONGODB_PORT)
        connection["admin"].authenticate(USER, PASSWORD, mechanism="SCRAM-SHA-1")
        db = connection[MONGO_DB]

        self.userCollection = db[USER_COLLECTION]     # User credentials: Username, Password, ID, current Level, list of level completion times, last completed time, dq or not, logged in or not
        self.questionCollection = db[QUESTIONS_COLLECTION] # Levels: Level#, Question (HTML String), Answer
        self.userLoginCollection = db[LOGIN_LOG_COLLECTION] # Login logs: Username, Entered Password, Valid login or not, time, IP Address
        self.userLogoutCollection = db[LOGOUT_LOG_COLLECTION] # Logout logs: Username, time, IP Address
        self.ansLogCollection = db[ANS_LOG_COLLECTION] # Answer attempts logs: Username, level #, answer, time, IP Address
        self.miscCollection = db[MISC_COLLECTION] # Misc data

    def getTimes(self):

        t = self.miscCollection.find_one({"_id":"times"})

        return (t["startTime"], t["endTime"])



    def logLogin(self, uname, password, valid, IP):

        ''' Log a login attempt

        Params: uname: Username as a String
                password: entered password as a String
                valid: Boolean, valid login or not
                IP: IP address of the user

        '''

        self.userLoginCollection.insert_one({"username":uname,
                                            "password":password,
                                            "valid":valid,
                                            "time":time.time(),
                                            "IP":IP})

    def logLogout(self, uname, IP):

        ''' Log a logout

            Params: uname: Username as a String
                    IP: IP address of the user
        '''

        self.userLogoutCollection.insert_one({"username":uname,
                                            "time":time.time(),
                                            "IP":IP})

    def logAnswer(self, user_id, levelNo, ans, valid, IP):

        ''' Log an answer attempt

            Params: user_id: The ID of the User
                    levelNo: The level for which the answer was attempted
                    ans: The answer that was entered
                    valid: Whether the answer was correct
                    IP: The IP Address of the user

        '''

        uname = self.userCollection.find_one({"_id":user_id})['username']

        if valid:
            self.questionCollection.find_one_and_update({"_id":levelNo},
                                                        {"$inc":{
                                                            "correctAttempts":1
                                                            }
                                                                })

        self.ansLogCollection.insert_one({"username":uname,
                                        "level":levelNo,
                                        "answer":ans,
                                        "time":time.time(),
                                        "valid":valid,
                                        "IP":IP})

    def authenticate(self, uname, password, IPAddress):

        ''' Authenticate the user

            params: uname: Username as a string
                    password: password as a string
                    IPAddress: IP of the user

            Returns: user_id: A string of the user's ID id the login is valid
                     "DQ": The user is disqualified
                     None: Invalid Login
         '''

        user = self.userCollection.find_one({"username":uname, "password":password})

        if user:

            self.logLogin(uname, password, True, IPAddress) # Log the attempt

            if user['disqualified']: # User is disqualified

                return "DQ"

            #self.userCollection.find_one_and_update({"username":uname}, {"$set":{"loggedIn":True}})

            return user['_id'] # Valid login

        self.logLogin(uname, password, False, IPAddress) # Log the attempt

        return None # Invalid login

    def isDQd(self, user_id):

        return (self.userCollection.find_one({"_id":user_id})['disqualified'])

    def logout(self, user_id, IP):

        # TODO: REVIEW THIS

        #uname = self.userCollection.find_one_and_update({"_id":user_id}, {"$set":{"loggedIn":False}})['username']  # Set Logged In to False and get username

        uname = self.userCollection.find_one({"_id":user_id})['username']
        self.logLogout(uname, IP)

    def isLoggedIn(self, user_id):

        # TODO: REVIEW THIS

        return (self.userCollection.find_one({"_id":user_id})['loggedIn'])


    def incrementLevel(self, user_id):

        ''' Increase the user's level by 1 '''

        self.userCollection.find_one_and_update({"_id":user_id},
                                                {"$inc" : {"currentLevel" : 1}})

    def setLastAnswerTime(self, user_id, time):

        ''' Set the time of the last answered question '''

        self.userCollection.find_one_and_update({"_id":user_id},
                                                {"$set" : {"lastLevelTime":time},
                                                "$push" :{"answerTimes":time}})

    def getLeaderBoard(self):

        tempList = []

        for user in self.userCollection.find():

            tempList.append((user['currentLevel'], user['lastLevelTime'], user['NAME']))

        tempList.sort(reverse=True, cmp=comp)

        return [(x[2], x[0]) for x in tempList]



    def getLevel(self, user_id):

        ''' Get current level of the user '''

        return self.userCollection.find_one({"_id":user_id})['currentLevel']

    def getQuestion(self, level):

        ''' Get question for given level '''

        return self.questionCollection.find_one({"_id":level})['question']

    def getAnswer(self, level):

        ''' Get answer for given level '''

        return self.questionCollection.find_one_and_update({"_id":level}, {"$inc":{"attempts":1}})['answer']

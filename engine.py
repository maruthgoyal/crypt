from constants import *

import pymongo
import time
import random
import string
import hashlib
import smtplib


def comp(x, y):

    if x[0] != y[0]:

        return x[0] - y[0]

    else:

        return y[1] - x[1]


class Engine(object):

    ''' Engine of the app.'''

    def __init__(self):

        ''' Initialize all Database connections'''

        #self.connection = pymongo.MongoClient(MONGODB_SERVER, MONGODB_PORT)
        #self.connection["admin"].authenticate(USER, PASSWORD, mechanism="SCRAM-SHA-1")
        self.connection = pymongo.MongoClient(MONGO_URI % (USER, PASSWORD))
        db = self.connection[MONGO_DB]

        self.userCollection = db[USER_COLLECTION]     # User credentials: Username, Password, ID, current Level, list of level completion times, last completed time, dq or not, logged in or not
        self.questionCollection = db[QUESTIONS_COLLECTION] # Levels: Level#, Question (HTML String), Answer
        self.userLoginCollection = db[LOGIN_LOG_COLLECTION] # Login logs: Username, Entered Password, Valid login or not, time, IP Address
        self.userLogoutCollection = db[LOGOUT_LOG_COLLECTION] # Logout logs: Username, time, IP Address
        self.ansLogCollection = db[ANS_LOG_COLLECTION] # Answer attempts logs: Username, level #, answer, time, IP Address
        self.miscCollection = db[MISC_COLLECTION] # Misc data. Contains start time and end time, blacklisted IPs

        self.adminCollection = db[ADMIN_COLLECTION]
        self.adminLoginCollection = db[ADMIN_LOGIN_COLLECTION]
        self.adminLogoutCollection = db[ADMIN_LOGOUT_COLLECTION]


        #Initialize email stuff
        self.server = smtplib.SMTP(EMAIL_HOST)
        self.server.starttls()
        self.server.ehlo()
        self.server.login(EMAIL_USERNAME, EMAIL_PASSWORD)

    def __del__(self):
        self.connection.close()
        self.server.close()


    def send_email(self, to_addr, subject, message):

        ''' Send an email

            NOTE: DO NOT FORGET: Let less secure apps access the email ID

        '''

        from_string = "From: %s" % FROM_EMAIL_ID
        to_string = "To: %s" % to_addr
        subject_string = "Subject: %s" % subject

        msg = '\r\n'.join([from_string, to_string, subject_string, "", message])

        self.server.sendmail(FROM_EMAIL_ID, to_addr, msg)


    def isBlacklisted(self, ip):

        if self.miscCollection.find_one({"_id":ip}):

            return True

        return False

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

    def getSecret(self, user_id):

        user = self.userCollection.find_one({"_id":user_id})

        if user:
            return user['secret']

        return None


    def authenticate_secret(self, user_id, secret):

        user = self.userCollection.find_one({"_id":user_id})

        if user:
            return secret==user['secret']

        return False


    def authenticate(self, uname, password, IPAddress):

        ''' Authenticate the user

            params: uname: Username as a string
                    password: password as a string
                    IPAddress: IP of the user

            Returns: user_id: A string of the user's ID id the login is valid
                     "DQ": The user is disqualified
                     None: Invalid Login
         '''

        check_password = hashlib.sha512(password + SALT).hexdigest()

        user = self.userCollection.find_one({"username":uname})

        if user and (check_password==user['password']):

            self.logLogin(uname, password, True, IPAddress) # Log the attempt

            if user['disqualified']: # User is disqualified

                return "DQ"

            return user['_id'] # Valid login

        self.logLogin(uname, password, False, IPAddress) # Log the attempt

        return None # Invalid login



    def isDQd(self, user_id):

        return (self.userCollection.find_one({"_id":user_id})['disqualified'])



    def logout(self, user_id, IP):

        uname = self.userCollection.find_one({"_id":user_id})['username']
        self.logLogout(uname, IP)




    def isLoggedIn(self, user_id):

        # TODO: REVIEW THIS

        return (self.userCollection.find_one({"_id":user_id})['loggedIn'])




    def incrementLevel(self, user_id, currentLevel):

        ''' Increase the user's level by 1 '''

        self.userCollection.update_one({"_id":user_id},
                                       {"$set" : {"currentLevel" : (currentLevel + 1)}})



    def setLastAnswerTime(self, user_id, time):

        ''' Set the time of the last answered question '''

        self.userCollection.find_one_and_update({"_id":user_id},
                                                {"$set" : {"lastLevelTime":time},
                                                "$push" :{"answerTimes":time}})



    def getLeaderBoard(self):

        tempList = []

        for user in self.userCollection.find({"disqualified":False}):

            tempList.append((user['currentLevel'], user['lastLevelTime'], user['NAME'], user['team']))

        tempList.sort(reverse=True, cmp=comp)

        return [[str(x[2]), x[0], rank+1, x[-1]] for rank,x in enumerate(tempList)]




    def getLevel(self, user_id):

        ''' Get current level of the user '''

        return self.userCollection.find_one({"_id":user_id})['currentLevel']




    def getQuestion(self, level):

        ''' Get question for given level '''

        maxLevel = self.miscCollection.find_one({"_id":"maxLevel"})['value']

        if level <= maxLevel:

            return self.questionCollection.find_one({"_id":level})['question']

        return None




    def getAnswer(self, level):

        ''' Get answer for given level '''

        return self.questionCollection.find_one_and_update({"_id":level}, {"$inc":{"attempts":1}})['answer']




    def setTeam(self, user_id, team):

        self.userCollection.update_one({"_id":user_id}, {"$set":{"team":team}})

    def getTeam(self, user_id):

        return self.userCollection.find_one({"_id":user_id})['team']

    def answerIsCorrect(self, ans, lvl, user_id, ip):

        if lvl > -1:

            ans_original = ans
            ans = ans.lower().replace(' ', '')
            check_ans = hashlib.sha512(ans + SALT).hexdigest()
            print check_ans, self.getAnswer(lvl)

            if check_ans == self.getAnswer(lvl):

                self.logAnswer(user_id=user_id,
                              levelNo=lvl,
                              ans=ans,
                              valid=True,
                              IP=ip) # Log the answer as correct

                self.incrementLevel(user_id, lvl)
                self.setLastAnswerTime(user_id, time.time())

                return True

            else:

                self.logAnswer(user_id=user_id,
                              levelNo=lvl,
                              ans=ans_original,
                              valid=False,
                              IP=ip) # Log the answer as incorrect

                return False



        else:
            self.setTeam(user_id, int(ans))
            self.incrementLevel(user_id, lvl)
            self.setLastAnswerTime(user_id, time.time())
            return True




    ##################################################################################################
    ##################################################################################################
    ##################################################################################################
    ##################################################################################################
    ##################################################################################################
    ##################################################################################################
    ##################################################################################################
    ##################################################################################################

    ##############################
    ###### Admin Stuff ###########
    ##############################

    def logAdminLogin(self, uname, password, valid, IP):

        self.adminLoginCollection.insert_one({"username":uname,
                                            "password":password,
                                            "time":time.time(),
                                            "valid":valid,
                                            "IPAddress":IP})

    def logAdminLogout(self, uname, IP):

        self.adminLogoutCollection.insert_one({"username":uname,
                                            "IPAddress":IP,
                                            "time":time.time()})

    def adminIsLoggedIn(self, adminID):

        return self.adminCollection.find_one({"_id":adminID})['isLoggedIn']

    def getAdminSecret(self, admin_name):

        return self.adminCollection.find_one({"username":admin_name})['secret']

    def authenticate_admin_secret(self, admin_id, secret):

        admin = self.adminCollection.find_one({"_id":admin_id})

        if admin:
            return secret==admin['secret']

        return False

    def loginAdmin(self, username, password, ip):

        check_password = hashlib.sha512(password + SALT).hexdigest()

        admin = self.adminCollection.find_one({"username":username})

        if admin and (check_password==admin['password']):

            self.logAdminLogin(username, password, True, ip)

            return admin['_id']

        self.logAdminLogin(username, password, False, ip)
        return None

    def logoutAdmin(self, admin_id, ip):
        name = self.adminCollection.find_one_and_update({"_id":admin_id}, {"$set":{"isLoggedIn":False}})['username']
        self.logAdminLogout(name, ip)

    def checkAdminLogin(self, admin_id, password):

        ''' Looks up admin by ID. Returns True if password matches the admin's password.'''

        check_password = hashlib.sha512(password + SALT).hexdigest()
        admin = self.adminCollection.find_one({"_id":admin_id})

        return (admin and check_password==admin['password'])


    def add_user(self, email, password, username, schoolName):

        # Generate random ID for the user. (length 32 string)
        # Hash the password and store it.
        # Add user with _id, username, password, email, currentLevel, lastLevelTime, NAME (schoolName), disqualified, answerTimes=[]

        _id = ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(32))
        hashed_password = hashlib.sha512(password + SALT).hexdigest()
        secret = hashlib.sha512(_id + SALT).hexdigest()

        self.userCollection.insert_one({'_id':_id,
                                        'username':username,
                                        'password':hashed_password,
                                        'email':email,
                                        'currentLevel':-1,
                                        'lastLevelTime':0.0,
                                        'NAME':schoolName,
                                        'disqualified': False,
                                        'secret': secret,
                                        'team': -1,
                                        'used_adv': False,
                                        'answerTimes':[]})

        email_message = REGISTRATION_MSG + '\r\n' + 'username: ' + username + '\r\n' + "password: " + password
        self.send_email(to_addr=email, subject=SUBJECT_MSG, message=email_message)

    def remove_user(self, username):

        ''' Deletes the user with the matching username '''

        self.userCollection.delete_one({"username":username})

    def dq_user(self, username):

        ''' Disqualifies the user with the matching username '''

        self.userCollection.update_one({"username":username}, {"$set":{"disqualified":True}})

    def rq_user(self, username):

        ''' Requalifies the user with the matching username '''

        self.userCollection.update_one({"username":username}, {"$set":{"disqualified":False}})

    def increment_level(self, username, increment):

        ''' Increments the level of the user by a given value '''

        user = self.userCollection.find_one({"username":username})

        if user and user['team'] == MYSTIC:

            self.userCollection.update_one({"username":username}, {"$inc":{"currentLevel":increment}})

    def set_start_time(self, newTime):

        self.miscCollection.update_one({"_id":"times"}, {"$set":{"startTime":newTime}})

    def set_end_time(self, newTime):

        self.miscCollection.update_one({"_id":"times"}, {"$set":{"endTime":newTime}})

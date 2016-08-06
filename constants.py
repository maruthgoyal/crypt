MONGO_DB = "cryptic_hunt"

USER_COLLECTION = "users"    # Contains the credentials of all the users
QUESTIONS_COLLECTION = "qa"  # Contains all the questions and answers
LOGIN_LOG_COLLECTION = "login_logs"       # Log all the logins
LOGOUT_LOG_COLLECTION = "logout_logs"
ANS_LOG_COLLECTION = "answer_logs"  # Log all the attempts
MISC_COLLECTION = "misc"

ADMIN_COLLECTION = "admins"
ADMIN_LOGIN_COLLECTION = "admin_logins"
ADMIN_LOGOUT_COLLECTION = "admin_logouts"

USER = "3JzDDTVnF1CG5TwN"
PASSWORD = "85yQgB6NXP1F2OJqAQFHiWCAASmNN4SPqQO6WyAHQLMPsfB9lpWjzamlbO4BZJ6g"


EMAIL_HOST = 'smtp.gmail.com:587'
FROM_EMAIL_ID = "espicev13@gmail.com"
EMAIL_USERNAME = "espicev13"
EMAIL_PASSWORD = "thisisnoida"

REGISTRATION_MSG = """Hello\nThank you for registering for eSpice v13. The following will be your login details for the online cryptic hunt to be held on August 13th 2016. We hope you enjoy the hunt.\n """
SUBJECT_MSG = 'Registration for eSpice v13'

SALT = "9808412005564c13bd85fa92356dd48d"

TIME_BONUS = (30 * 60) # 30 Minutes

VALOR = 0
MYSTIC = 1
INSTINCT = 2

MONGO_URI = "mongodb://%s:%s@ds147835-a0.mlab.com:47835/cryptic_hunt"

LVL_0_ANS = "QyVdoL1QUGbb9Ukd"

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

USER = ""
PASSWORD = ""


EMAIL_HOST = 'smtp.gmail.com:587'
FROM_EMAIL_ID = ""
EMAIL_USERNAME = ""
EMAIL_PASSWORD = ""

REGISTRATION_MSG = """Hello\nThank you for registering for eSpice v13. The following will be your login details for the online cryptic hunt to be held on August 13th 2016. We hope you enjoy the hunt.\n """
SUBJECT_MSG = 'Registration for eSpice v13'

SALT = ""

TIME_BONUS = (30 * 60) # 30 Minutes

VALOR = 0
MYSTIC = 1
INSTINCT = 2

MONGO_URI = ""

LVL_0_ANS = "QyVdoL1QUGbb9Ukd"

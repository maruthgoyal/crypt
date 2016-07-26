from flask import Flask, redirect, url_for, render_template,request, make_response, abort # Flask stuff

import time
from engine import Engine # Where all the magic happens

from flask_limiter import Limiter  # For Rate limiting
from flask_limiter.util import get_remote_address

from constants import VALOR, INSTINCT, MYSTIC, TIME_BONUS

app = Flask(__name__)
eng = Engine() # Initialize our engine

USER_COOKIE_NAME = "user"
ADMIN_COOKIE_NAME = "admin"

USER_SECRET_NAME = "user_secret"
ADMIN_SECRET_NAME = "admin_secret"

limiter = Limiter(
        app,
        key_func=get_remote_address,
        global_limits=['200/hour']

        ) # Initialize our rate limiter. Not more than 200 requests to the site/hour



EXPIRY_DELAY = 7200 # Expire the session login after 2 hours
ADMIN_EXPIRY_DELAY = 3600 # Expire admin session in 1 hour



@app.errorhandler(401)  # A robot is being used
def fourzeroone(e):

    return render_template("robot.html"), 401

@app.errorhandler(404) # Page not found
def fourzerofour(e):

    return render_template("notFound.html"), 404

@app.errorhandler(403) # If user trying to access restricted resource.
def fourzerothree(e):

    ''' Access Denied '''

    return render_template("backoff.html"), 403

@app.errorhandler(429) # Rate limited
def fourtwonine(e):

    ''' Too many requests to the site '''

    return render_template("rate_limited.html"), 429

@app.before_request  # Check if user is not a robot or blacklisted before every request
def before_request():

    ''' Checking is a robot '''

    user_agent = request.user_agent

    if any(x==None for x in (user_agent.platform, user_agent.browser, user_agent.version)):

        abort(401)

    if eng.isBlacklisted(request.remote_addr):

        abort(403)






@app.route('/', methods=['POST', 'GET'])
@limiter.limit("50/hour") # Not more than 50 visits to the main page per hour
def index():

    #print currentTime, start, end
    # print request.access_route, request.environ['REMOTE_ADDR']

    if request.method == 'GET':

        if USER_COOKIE_NAME in request.cookies and USER_SECRET_NAME in request.cookies:  # Check if user is already logged in

            return redirect(url_for('play')) # If so, go straight to the play page. Yay.

        return render_template('index.html', error=False) # Otherwise, go to Login.

    else:

        uname = request.form['username']
        password = request.form['password']
        ip = request.environ['REMOTE_ADDR'] # IP Address of the user. For logging and blacklist purposes

        if uname and password:

            id_of_user = eng.authenticate(uname, password, ip) # Log and verify the login attempt

            if id_of_user: # If the login was valid

                if id_of_user == 'DQ': # If the user is disqualified

                    return redirect(url_for('dead')) # Send them to the dead page

                resp = make_response(redirect(url_for('play'))) # Otherwise, send them to play
                resp.set_cookie(USER_COOKIE_NAME, id_of_user, expires=(time.time() + EXPIRY_DELAY)) # Set the cookie and expiry
                resp.set_cookie(USER_SECRET_NAME, eng.getSecret(id_of_user), expires=(time.time() + EXPIRY_DELAY)) # Set the secret and expiry

                return resp

        return render_template('index.html', error=True) # The login was invalid






@app.route('/play', methods=['POST', 'GET'])
def play():

    start, end = eng.getTimes()
    currentTime = time.time()

    if USER_COOKIE_NAME not in request.cookies or USER_SECRET_NAME not in request.cookies: # User is not logged in. Gavar.

        resp = make_response(redirect(url_for('index')))
        resp.set_cookie(USER_COOKIE_NAME, '', expires=0)
        resp.set_cookie(USER_SECRET_NAME, '', expires=0)

        return resp



    cookie = request.cookies[USER_COOKIE_NAME]
    secret = request.cookies[USER_SECRET_NAME]




    if not eng.authenticate_secret(cookie, secret):

        resp = make_response(redirect(url_for('index')))
        resp.set_cookie(USER_COOKIE_NAME, '', expires=0)
        resp.set_cookie(USER_SECRET_NAME, '', expires=0)

        return resp


    eligibleForTimeExtension = (eng.getTeam(cookie) == VALOR) and ((currentTime - end) < TIME_BONUS)

    if currentTime >= start and (currentTime < end or eligibleForTimeExtension):

        if eng.isDQd(cookie):

            return redirect(url_for('dead'))

        else:

            currentLevel = eng.getLevel(cookie) # Get the current level
            question = eng.getQuestion(currentLevel).replace('\\', '') # Get the question for that level

            if request.method == 'GET': # show the question

                return render_template('play.html', q=question, wrongAns=False)

            else: # User submitted an answer

                answer = str(request.form['ans']).lower().replace(' ', '') # Get the answer

                if eng.answerIsCorrect(answer, currentLevel, cookie): # If the answer is correct

                    eng.logAnswer(user_id=cookie,
                                  levelNo=currentLevel,
                                  ans=answer,
                                  valid=True,
                                  IP=request.environ['REMOTE_ADDR']) # Log the answer as correct

                    eng.incrementLevel(cookie, currentLevel) # Increase the user's current level
                    eng.setLastAnswerTime(cookie, time.time()) # Set the user's time for the last answer

                    return redirect(url_for('play')) # Reload the page

                eng.logAnswer(user_id=cookie,
                              levelNo=currentLevel,
                              ans=answer,
                              valid=False,
                              IP=request.environ['REMOTE_ADDR']) # Log the answer as incorrect

                return render_template('play.html', q=question, wrongAns=True) # Re-render the page, with wrong answer flag

    elif currentTime > end:

        return render_template("finished.html")

    else:

        return render_template("notstarted.html")





@app.route('/leaderboard')
def leaderboard():

    leaderList = eng.getLeaderBoard()

    return render_template("leaderboard.html", leaders=leaderList)





@app.route('/logout')
def logout():

    if USER_COOKIE_NAME in request.cookies:

        eng.logout(request.cookies[USER_COOKIE_NAME], request.environ['REMOTE_ADDR']) # Logout the user. Sending the IP for logging purposes

        resp = make_response(redirect(url_for('index'))) # Send to the index page.
        resp.set_cookie(USER_COOKIE_NAME, value='', expires=0) # Remove the cookie
        resp.set_cookie(USER_SECRET_NAME, value='', expires=0)

        return resp

    return redirect(url_for('index'))





@app.route('/dq')
def dead():

    return render_template("dead.html")


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

@app.route('/5/7/whoami/admin', methods=['POST', 'GET'])
def admin():

    if request.method == 'GET':

        if (ADMIN_COOKIE_NAME in request.cookies and ADMIN_SECRET_NAME in request.cookies) and (eng.adminIsLoggedIn(request.cookies[ADMIN_COOKIE_NAME])):

            return redirect(url_for('admin_dash'))

        return render_template("admin_login.html", error=False)

    else:

        adminUsername = request.form['username']
        adminPassword= request.form['password']
        admin_ip = request.environ['REMOTE_ADDR']

        if adminUsername and adminPassword:

            id_of_admin = eng.loginAdmin(adminUsername, adminPassword, admin_ip)

            if id_of_admin:

                response = make_response(redirect(url_for('admin_dash')))
                response.set_cookie(ADMIN_COOKIE_NAME, id_of_admin, expires=(time.time() + ADMIN_EXPIRY_DELAY))
                response.set_cookie(ADMIN_SECRET_NAME, eng.getAdminSecret(adminUsername), expires=(time.time() + ADMIN_EXPIRY_DELAY))

                return response

        return render_template("admin_login.html", error=True) # If either username or password is missing, or invalid login

@app.route('/5/7/whoami/admin/dash')
def admin_dash():

    if ADMIN_COOKIE_NAME not in request.cookies or ADMIN_SECRET_NAME not in request.cookies:

        return redirect(url_for("admin"))

    if not eng.authenticate_admin_secret(request.cookies[ADMIN_COOKIE_NAME], request.cookies[ADMIN_SECRET_NAME]):

        resp = make_response(redirect(url_for("admin")))
        resp.set_cookie(ADMIN_COOKIE_NAME, '', expires=0)
        resp.set_cookies(ADMIN_SECRET_NAME, '', expires=0)

        return resp

    return render_template("admin_dashboard.html")


@app.route('/5/7/whoami/admin/add', methods=['POST', 'GET'])
def add_user():

    if ADMIN_COOKIE_NAME not in request.cookies or ADMIN_SECRET_NAME not in request.cookies:

        return redirect(url_for('admin'))

    if request.method == 'GET':

        if not eng.authenticate_admin_secret(request.cookies[ADMIN_COOKIE_NAME], request.cookies[ADMIN_SECRET_NAME]):

            resp = make_response(redirect(url_for("admin")))
            resp.set_cookie(ADMIN_COOKIE_NAME, '', expires=0)
            resp.set_cookies(ADMIN_SECRET_NAME, '', expires=0)

            return resp

        return render_template('add_user.html', error=False)

    else:

        if not eng.authenticate_admin_secret(request.cookies[ADMIN_COOKIE_NAME], request.cookies[ADMIN_SECRET_NAME]):

            resp = make_response(redirect(url_for("admin")))
            resp.set_cookie(ADMIN_COOKIE_NAME, '', expires=0)
            resp.set_cookies(ADMIN_SECRET_NAME, '', expires=0)

            return resp

        email = request.form['emailID']
        schoolName = request.form['name']
        username = request.form['username']
        password = request.form['password']
        adminPass = request.form['adminPass']

        if eng.checkAdminLogin(request.cookies[ADMIN_COOKIE_NAME], adminPass):

            eng.add_user(email, password, username, schoolName)

        else:

            return render_template("add_user.html", error=True)

        return redirect(url_for('admin_dash'))

@app.route('/5/7/whoami/admin/remove', methods=['POST', 'GET'])
def remove_user():

    if ADMIN_COOKIE_NAME not in request.cookies or ADMIN_SECRET_NAME not in request.cookies:

        return redirect(url_for('admin'))


    if not eng.authenticate_admin_secret(request.cookies[ADMIN_COOKIE_NAME], request.cookies[ADMIN_SECRET_NAME]):

        resp = make_response(redirect(url_for("admin")))
        resp.set_cookie(ADMIN_COOKIE_NAME, '', expires=0)
        resp.set_cookies(ADMIN_SECRET_NAME, '', expires=0)

        return resp

    if request.method == 'GET':

        return render_template("remove_user.html", error=False)

    else:

        uname = request.form['username']
        adminPass = request.form['adminPass']

        if eng.checkAdminLogin(request.cookies[ADMIN_COOKIE_NAME], adminPass):

            eng.remove_user(uname)

        else:
            return render_template("remove_user.html", error=True)

        return redirect(url_for('admin_dash'))

@app.route('/5/7/whoami/admin/dq', methods=['POST', 'GET'])
def dq_user():

    if ADMIN_COOKIE_NAME not in request.cookies or ADMIN_SECRET_NAME not in request.cookies:
        return redirect(url_for('admin'))

    if not eng.authenticate_admin_secret(request.cookies[ADMIN_COOKIE_NAME], request.cookies[ADMIN_SECRET_NAME]):

        resp = make_response(redirect(url_for("admin")))
        resp.set_cookie(ADMIN_COOKIE_NAME, '', expires=0)
        resp.set_cookies(ADMIN_SECRET_NAME, '', expires=0)

        return resp

    if request.method == 'GET':

        return render_template("dq_user.html", error=False)

    else:

        uname = request.form['username']
        adminPass = request.form['adminPass']

        if eng.checkAdminLogin(request.cookies[ADMIN_COOKIE_NAME], adminPass):

            eng.dq_user(uname)

        else:
            return render_template("dq_user.html", error=True)

        return redirect(url_for('admin_dash'))

@app.route('/5/7/whoami/admin/rq', methods=['POST', 'GET'])
def rq_user():

    if ADMIN_COOKIE_NAME not in request.cookies or ADMIN_SECRET_NAME not in request.cookies:
        return redirect(url_for('admin'))

    if not eng.authenticate_admin_secret(request.cookies[ADMIN_COOKIE_NAME], request.cookies[ADMIN_SECRET_NAME]):

        resp = make_response(redirect(url_for("admin")))
        resp.set_cookie(ADMIN_COOKIE_NAME, '', expires=0)
        resp.set_cookies(ADMIN_SECRET_NAME, '', expires=0)

        return resp

    if request.method == 'GET':

        return render_template("rq_user.html", error=False)

    else:

        uname = request.form['username']
        adminPass = request.form['adminPass']

        if eng.checkAdminLogin(request.cookies[ADMIN_COOKIE_NAME], adminPass):

            eng.rq_user(uname)

        else:
            return render_template("rq_user.html", error=True)

        return redirect(url_for('admin_dash'))

@app.route('/5/7/whoami/admin/chlvl', methods=['POST', 'GET'])
def chlvl():

    if ADMIN_COOKIE_NAME not in request.cookies or ADMIN_SECRET_NAME not in request.cookies:
        return redirect(url_for('admin'))


    if not eng.authenticate_admin_secret(request.cookies[ADMIN_COOKIE_NAME], request.cookies[ADMIN_SECRET_NAME]):

        resp = make_response(redirect(url_for("admin")))
        resp.set_cookie(ADMIN_COOKIE_NAME, '', expires=0)
        resp.set_cookies(ADMIN_SECRET_NAME, '', expires=0)

        return resp

    if request.method == 'GET':

        return render_template("chlevel.html", error=False)

    else:

        uname = request.form['username']
        increment = request.form['increment']
        adminPass = request.form['adminPass']

        if eng.checkAdminLogin(request.cookies[ADMIN_COOKIE_NAME], adminPass):

            eng.increment_level(uname, increment)

        else:
            return render_template("chlevel.html", error=True)

        return redirect(url_for('admin_dash'))

@app.route('/5/7/whoami/admin/setStartTime', methods=['POST', 'GET'])
def ch_start_time():

    if ADMIN_COOKIE_NAME not in request.cookies or ADMIN_SECRET_NAME not in request.cookies:
        return redirect(url_for('admin'))


    if not eng.authenticate_admin_secret(request.cookies[ADMIN_COOKIE_NAME], request.cookies[ADMIN_SECRET_NAME]):

        resp = make_response(redirect(url_for("admin")))
        resp.set_cookie(ADMIN_COOKIE_NAME, '', expires=0)
        resp.set_cookies(ADMIN_SECRET_NAME, '', expires=0)

        return resp

    if request.method == 'GET':

        return render_template("chStartTime.html", error=False)

    else:

        new_time = request.form['time']
        adminPass = request.form['adminPass']

        if eng.checkAdminLogin(request.cookies[ADMIN_COOKIE_NAME], adminPass):

            eng.set_start_time(int(new_time))

        else:
            return render_template("chStartTime.html", error=True)

        return redirect(url_for('admin_dash'))


@app.route('/5/7/whoami/admin/setEndTime', methods=['POST', 'GET'])
def ch_end_time():

    if ADMIN_COOKIE_NAME not in request.cookies or ADMIN_SECRET_NAME not in request.cookies:
        return redirect(url_for('admin'))


    if not eng.authenticate_admin_secret(request.cookies[ADMIN_COOKIE_NAME], request.cookies[ADMIN_SECRET_NAME]):

        resp = make_response(redirect(url_for("admin")))
        resp.set_cookie(ADMIN_COOKIE_NAME, '', expires=0)
        resp.set_cookies(ADMIN_SECRET_NAME, '', expires=0)

        return resp

    if request.method == 'GET':

        return render_template("chEndTime.html", error=False)

    else:

        new_time = request.form['time']
        adminPass = request.form['adminPass']

        if eng.checkAdminLogin(request.cookies[ADMIN_COOKIE_NAME], adminPass):

            eng.set_end_time(int(new_time))

        else:
            return render_template("chEndTime.html", error=True)

        return redirect(url_for('admin_dash'))




@app.route('/5/7/whoami/admin/logout')
def adminLogout():

    if ADMIN_COOKIE_NAME in request.cookies:

        eng.logoutAdmin(request.cookies[ADMIN_COOKIE_NAME], request.environ['REMOTE_ADDR'])

        resp =make_response(redirect(url_for("admin")))
        resp.set_cookie(ADMIN_COOKIE_NAME, '0',expires=0)
        resp.set_cookie(ADMIN_SECRET_NAME, '0', expires=0)
        return resp

    return redirect(url_for("admin"))


if __name__ == '__main__':

    app.run(debug=True, host='0.0.0.0')

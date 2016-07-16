from flask import Flask, redirect, url_for, render_template,request, make_response, abort # Flask stuff

import time
from engine import Engine # Where all the magic happens

from flask_limiter import Limiter  # For Rate limiting
from flask_limiter.util import get_remote_address

app = Flask(__name__)
eng = Engine() # Initialize our engine



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
@app.route('/<string:message>', methods=['POST', 'GET'])
@limiter.limit("50/hour") # Not more than 50 visits to the main page per hour
def index(message=None):

    start, end = eng.getTimes()
    currentTime = time.time()

    print currentTime, start, end

    if currentTime >= start and currentTime < end:

        if request.method == 'GET':

            if "user" in request.cookies:  # Check if user is already logged in

                return redirect(url_for('play')) # If so, go straight to the play page. Yay.

            return render_template('index.html', error=False, mess=message) # Otherwise, go to Login.

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
                    resp.set_cookie('user', id_of_user, expires=(time.time() + EXPIRY_DELAY)) # Set the cookie and expiry

                    return resp

            return render_template('index.html', error=True, mess=message) # The login was invalid

    elif currentTime > end:

        return render_template("finished.html") # Event is over.

    else:

        return render_template("notstarted.html") # Event hasn't started.






@app.route('/play', methods=['POST', 'GET'])
def play():

    start, end = eng.getTimes()
    currentTime = time.time()

    if currentTime >= start and currentTime < end:

        if 'user' not in request.cookies: # User is not logged in. Gavar.

            return redirect(url_for('index'))

        elif eng.isDQd(request.cookies['user']):

            return redirect(url_for('dead'))

        else:

            currentLevel = eng.getLevel(request.cookies['user']) # Get the current level
            question = eng.getQuestion(currentLevel) # Get the question for that level

            if request.method == 'GET': # show the question

                return render_template('play.html', q=question, wrongAns=False)

            else: # User submitted an answer

                answer = request.form['ans'] # Get the answer

                if eng.answerIsCorrect(answer, currentLevel): # If the answer is correct

                    eng.logAnswer(user_id=request.cookies['user'],
                                  levelNo=currentLevel,
                                  ans=answer,
                                  valid=True,
                                  IP=request.environ['REMOTE_ADDR']) # Log the answer as correct

                    eng.incrementLevel(request.cookies['user']) # Increase the user's current level
                    eng.setLastAnswerTime(request.cookies['user'], time.time()) # Set the user's time for the last answer

                    return redirect(url_for('play')) # Reload the page

                eng.logAnswer(user_id=request.cookies['user'],
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

    leaderList = eng.getLeaderboard()

    return render_template("leaderboard.html", leaders=leaderList)





@app.route('/logout', methods=['POST'])
def logout():

    if 'user' in request.cookies:

        eng.logout(request.cookies['user'], request.environ['REMOTE_ADDR']) # Logout the user. Sending the IP for logging purposes

        resp = make_response(redirect(url_for('index', message="Either you have logged out, or your session has expired."))) # Send to the index page.
        resp.set_cookie('user', value='', expires=0) # Remove the cookie

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

@app.route('/5/7/69/whoami/admin', methods=['POST', 'GET'])
def admin():

    if request.method == 'GET':

        if ('admin' in request.cookies) and (eng.adminIsLoggedIn(request.cookies['admin'])):

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
                response.set_cookie("admin", id_of_admin, expires=(time.time() + ADMIN_EXPIRY_DELAY))

                return response

        return render_template("admin_login.html", error=True) # If either username or password is missing, or invalid login

@app.route('/5/7/whoami/admin/dash')
def admin_dash():

    if "admin" not in request.cookies:

        return redirect(url_for("admin"))

    return render_template("admin_dashboard.html")


@app.route('/5/7/whoami/admin/add', methods=['POST', 'GET'])
def add_user():

    if "admin" not in request.cookies:

        return redirect(url_for('admin'))

    if request.method == 'GET':

        return render_template('add_user.html', error=False)

    else:

        email = request.form['emailID']
        schoolName = request.form['name']
        username = request.form['username']
        password = request.form['password']
        adminPass = request.form['adminPass']

        if eng.checkAdminLogin(request.cookies['admin'], adminPass):

            eng.add_user(email, password, username, schoolName)

        else:
            return render_template("add_user.html", error=True)

        return redirect(url_for('admin_dash'))

@app.route('/5/7/whoami/admin/remove', methods=['POST', 'GET'])
def remove_user():

    if 'admin' not in request.cookies:
        return redirect(url_for('admin'))

    if request.method == 'GET':

        return render_template("remove_user.html", error=False)

    else:

        uname = request.form['username']
        adminPass = request.form['adminPass']

        if eng.checkAdminLogin(request.cookies['admin'], adminPass):

            eng.remove_user(uname)

        else:
            return render_template("remove_user.html", error=True)

        return redirect(url_for('admin_dash'))

@app.route('/5/7/whoami/admin/dq', methods=['POST', 'GET'])
def dq_user():

    if 'admin' not in request.cookies:
        return redirect(url_for('admin'))

    if request.method == 'GET':

        return render_template("dq_user.html", error=False)

    else:

        uname = request.form['username']
        adminPass = request.form['adminPass']

        if eng.checkAdminLogin(request.cookies['admin'], adminPass):

            eng.dq_user(uname)

        else:
            return render_template("dq_user.html", error=True)

        return redirect(url_for('admin_dash'))


@app.route('/5/7/whoami/admin/logout')
def adminLogout():

    if "admin" in request.cookies:

        self.adminLogout(request.cookies['admin'], request.environ['REMOTE_ADDR'])

        resp =make_response(redirect(url_for("admin")))
        resp.set_cookie("admin", 0,expires=0)
        return resp

    return redirect(url_for("admin"))


if __name__ == '__main__':

    app.run(debug=True)

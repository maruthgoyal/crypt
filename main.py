from flask import Flask, redirect, url_for, render_template,request, make_response, abort

import time
from engine import Engine

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
eng = Engine()

limiter = Limiter(
        app,
        key_func=get_remote_address,
        global_limits=['200/hour']

        )

EXPIRY_DELAY = 7200 # 2 Hours

@app.errorhandler(401)
def fourzeroone(e):

    return render_template("robot.html"), 401

@app.errorhandler(404)
def fourzerofour(e):

    return render_template("notFound.html"), 404

@app.errorhandler(403)
def fourzerothree(e):

    ''' Access Denied '''

    return render_template("backoff.html"), 403

@app.before_request
def before_request():

    ''' Checking is a robot '''

    user_agent = request.user_agent

    if any(x==None for x in (user_agent.platform, user_agent.browser, user_agent.version)):

        abort(401)

    if eng.isBlacklisted(request.remote_addr):

        abort(403)



@app.route('/', methods=['POST', 'GET'])
@app.route('/<string:message>', methods=['POST', 'GET'])
@limiter.limit("50/hour")
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

        return render_template("finished.html")

    else:

        return render_template("notstarted.html")


@app.route('/play', methods=['POST', 'GET'])
def play():

    start, end = eng.getTimes()
    currentTime = time.time()

    if currentTime >= start and currentTime < end:

        if 'user' not in request.cookies: # User is not logged in. Gavar.

            return redirect(url_for('index'))

        elif eng.isDQd(request.cookies['user']):

            return redirect(url_for('dead'))

        #elif not eng.isLoggedIn(request.cookies['user']):
    #
    #        return redirect(url_for('index'))


        else:

            currentLevel = eng.getLevel(request.cookies['user']) # Get the current level
            question = eng.getQuestion(currentLevel) # Get the question for that level

            print question

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

        resp = make_response(redirect(url_for('index', message="Either you have not logged in, or your session has expired. Please login."))) # Send to the index page.
        resp.set_cookie('user', value='', expires=0) # Remove the cookie

        return resp

    return redirect(url_for('index'))

@app.route('/dq')
def dead():

    return render_template("dead.html")


if __name__ == '__main__':

    app.run(debug=True)

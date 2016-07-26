from flask import Flask, render_template, request, redirect, url_for
from engine import Engine
import time

app = Flask(__name__)
eng = Engine()

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/signup', methods=['GET', 'POST'])
def signup():

    if request.method == 'GET':
        return render_template("signup.html", message=None)

    else:
        print request.form
        schName = request.form['schName']
        schMail = request.form['schMail']
        schPh = request.form['schPh']

        teachInchName = request.form['teachInchName']
        teachInchMail = request.form['teachInchMail']
        teachInchPh = request.form['teachInchPh']

        studInchName = request.form['studInchName']
        studInchMail = request.form['studInchMail']
        studInchPh = request.form['studInchPh']

        turtle1, turtle2 = request.form['turtle1'], request.form['turtle2']
        gaming = request.form['gaming']
        flash1, flash2 = request.form['flash1'], request.form['flash2']
        surprise = request.form['surprise']
        music1, music2 = request.form['music1'], request.form['music2']
        snap = request.form['snap']
        gd = request.form['gd']
        quiz1, quiz2 = request.form['quiz1'], request.form['quiz2']
        prog1, prog2  = request.form['prog1'], request.form['quiz2']
        design1, design2 = request.form['design1'], request.form['design2']
        av1, av2 = request.form['av1'], request.form['av2']

        data = {"School Name":schName,
                "School e-mail": schMail,
                "School Phone": schPh,
                "Teacher Incharge Name": teachInchName,
                "Teacher Incharge e-mail": teachInchMail,
                "Teacher Incharge Phone": teachInchPh,
                "Student Incharge Name": studInchName,
                "Student Incharge e-mail": studInchMail,
                "Student Incharge Phone": studInchPh,
                "turtle": [turtle1, turtle2],
                "gaming":[gaming],
                "flash": [flash1, flash2],
                "surprise":[surprise],
                "music":[music1, music2],
                "snap": [snap],
                "gd": [gd],
                "quiz": [quiz1, quiz2],
                "prog": [prog1, prog2],
                "design": [design1, design2],
                "av": [av1, av2],
                "time": time.time()}

        eng.register(data)

        return render_template("signup.html", message="Thanks for registering. See you there.")


if __name__ =='__main__':
    app.run(debug=True)

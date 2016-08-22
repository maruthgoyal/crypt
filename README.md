eSpice Cryptic Hunt
======

This is the cryptic hunt webapp used for eSpice v13. It uses the #Flask# framework for Python for the backend and #MongoDB# to as the database.

#This app is not deployment ready#

In order to deploy this app, you must fill out certain things. 

The #constants.py# file must be populated with the following:

• e-mail IDs for sending the registration emails
• URI of the MongoDB (see mLab)
• Username and Password of the MongoDB

A MongoDB database must be created containing all the collections listed in the constants.py file. I realize doing this entire setup process is very tedious. Hence, I will be releasing some scripts which will automate this entire process. 

#Deployment#
We used 1 professional Dyno on Heroku to deploy this app. It's as simple as "git push heroku_2 master" to deploy. I'll upload an entire document along with the scripts containing step-by-step instructions for deploying this app.

NOTE: This app is the version with the Pokemon teams. I'll be adding one without the teams as a more general version.

#!/usr/bin/env python
# File    : server.py ; a Flask app to monitor a garage door
# Author  : Joe McManus josephmc@alumni.cmu.edu
# Version : 0.1  04/09/2016
# Copyright (C) 2016 Joe McManus
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from flask import Flask, render_template, Markup, request
import sys 
import mraa
import time
import sqlite3
import hashlib
import logging 

logging.basicConfig(filename='/var/log/flask.log',level=logging.DEBUG)
logging.debug("Started App")


def getHash(passText):
	hashPass=hashlib.md5()
	hashPass.update(passText)
	return(hashPass.hexdigest())

def readDoor(pinNumber):
	pin=mraa.Gpio(pinNumber)
	pin.dir(mraa.DIR_IN)
	if pin.read() == 0:
		status="Closed"
	else:
		status="Open"

	return(status)

app = Flask(__name__)

@app.route('/')
def index():
	sideDoor=readDoor(7)
	eastDoor=readDoor(8)
	westDoor=readDoor(9)

	bodyText=Markup("<strong> Side Door </strong> : " + sideDoor + "<br>" )
	bodyText=bodyText + Markup("<strong> East  Door </strong> : " + eastDoor + "<br>" )
	bodyText=bodyText + Markup("<strong> West  Door </strong> : " + westDoor + "<br>" )
	return render_template('template.html', bodyText=bodyText)

@app.route('/tmp')
def tmp():
	try: 
		#Initialize the MRAA pin
		pin = mraa.Aio(1) 
		#Set it to a 12 bit value
		pin.setBit(12)
	except Exception,e:
		print("Error: {:s}". format(e))
		sys.exit()
	
	rawReading = pin.read()
			
	#Galileo voltage should be the raw reading divided by 819.0
	#The reading is from 0-4095 to cover 0-5 volts
	#Or 4095/5=819.0
	galVoltage=float(rawReading / 819.0)
	tempC= (galVoltage * 100 ) - 50 
	tempF= (tempC * 9.0 / 5.0) + 32.0
	bodyText="Current Temperature: " + str(round(tempF,2)) 
	return render_template('template.html', bodyText=bodyText) 
	
@app.route('/loginForm')
def loginForm():
	bodyText=Markup('''<form method=POST action=/login>
	Username: <input type=text name=postUser value=\"\"></input><br>
	Password: <input type=password name=postPass value=\"\"></input><br>
	<input type=submit name=submit value=\"submit\">
	</form>
	''')
	return render_template('template.html', bodyText=bodyText) 

@app.route('/login', methods=['GET', 'POST'])
def login():
	db = sqlite3.connect('server.sql3')
	db.row_factory = sqlite3.Row
	epass=getHash(request.form['postPass'])
	print(epass)
	query="select id, username, password from users where username=? and password=?"
	t=(request.form['postUser'], epass)
	cursor=db.cursor()
	cursor.execute(query, t)
	rows = cursor.fetchall()
	for row in rows:
		print(row[0])
	if len(rows) == 1:
		bodyText=request.form['postUser'] + " " + request.form['postPass']
		bodyText=bodyText + " Success!" 
	else:
		bodyText = "Incorect Login."

	return render_template('template.html', bodyText=bodyText)
	

if __name__ == '__main__':
	#app.debug = True
	logging.debug("Started Main")
	app.run(host='0.0.0.0', port=80)

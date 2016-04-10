#!/usr/bin/env python
# File    : door.py 
# Author  : Joe McManus josephmc@alumni.cmu.edu
# Version : 0.1  04/09/2016
# Copyright (C) 2015 Joe McManus
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


import mraa
import time
import argparse
import logging
import os
import sqlite3
import smtplib

from email.mime.text import MIMEText


logging.basicConfig(filename='/var/log/door.log',level=logging.DEBUG)
logging.debug("Started App")


parser = argparse.ArgumentParser(description='Analog Pin Value Reader for Galileo')
parser.add_argument('--delay', help="Number of seconds to wait between readings, default 59", default=59, type=int, action="store")
parser.add_argument('--pid', help="Create a pid file in /var/run/door.pid",  action="store_true")
parser.add_argument('--quiet', help="Quiet display, show only the voltage of the analog pin", action="store_true")
args=parser.parse_args()


if args.pid:
	fh=open("/var/run/door.pid", "w")
	fh.write(str(os.getpid()))
	fh.close()


mailServer="mx.example.com"
mailFrom="you@example.com"
mailTo="you@example.com"
msgSubject="Alert: Garage Door open!" 

db = sqlite3.connect('/data/flask/server.sql3')
db.row_factory = sqlite3.Row

def sendMessage(mailServer, mailFrom, mailTo, msgSubject): 
        msg= MIMEText("Alert: Garage Door Open!")
        msg['Subject'] = msgSubject
        msg['From'] = mailFrom
        msg['To'] = mailTo
	
	try:                                 
        	s = smtplib.SMTP(mailServer,timeout=25)
        	s.sendmail(mailFrom, mailTo, msg.as_string())
	except: 
		logging.debug("ERROR: Couldn't send email")

def insertRecord(db, door, status):
	query="insert into doorData (id, door, status, dateStamp) values(?,?,?,CURRENT_TIMESTAMP)" 
	t=(None, door, status) 
	cursor=db.cursor()
	cursor.execute(query, t)
	db.commit()
	

def queryRecords(db): 
	query="select count(status) from doorData where dateStamp > datetime('now', '-5 minutes') and status=1"
	cursor=db.cursor()
	cursor.execute(query)
	rows = cursor.fetchall()
	for row in rows:
		count=row[0]

	if count > 4:
		query="select distinct(door) from doorData where dateStamp > datetime('now', '-5 minutes') and status=1";
		cursor=db.cursor()                                                                                                         
	        cursor.execute(query)                                                                                                      
      		rows = cursor.fetchall()
		for row in rows:                              
               		if row[0] == "7": 
				door="Side Door"
			elif row[0] == "8":
				door="East Door"
			elif row[0] == "9":
				door="West Door"

			logging.debug("Alert: " + door + " open") 
			msgSubject="Alert: " + door + " open"
			sendMessage(mailServer, mailFrom, mailTo, msgSubject)
	


while 1:
	for x in range (7, 10):
		pin=mraa.Gpio(x)
		pin.dir(mraa.DIR_IN)
       		pinVal=pin.read()
		if args.pid:
			logging.debug(pinVal)
		else:
			print(pinVal)

		insertRecord(db, x, pinVal)
		queryRecords(db)

       	time.sleep(args.delay) 



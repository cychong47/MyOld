#!/usr/bin/env python

from __future__ import print_function
import os
import sys
import time
import sqlite3
import string
import struct
import fcntl
import termios
from operator import itemgetter
from collections import OrderedDict


"""	
	Perosnal day logger

	2010.04.27	Convert to class
				dipslay event in aligned format
	2011.09.29	Add "search"
	2013.09.03	Add summary option to display only tags and project count

	Todo
		- Update event - add tags or change the date
		- Delete event
		- Web I/F
"""

PROG_NAME = "j.py"

USAGE = """
	PROG_NAME add ..		Add what I did today
	PROG_NAME addp ..		Add what I did today w/o project
	PROG_NAME search ..		Find what I did
	PROG_NAME summary ..	List only summary
	PROG_NAME				List what I did
	PROG_NAME 2010			List what I did on 2010
	PROG_NAME 2010-12		List what I did on 2010-12
	PROG_NAME year			List what I did on 'year'
	PROG_NAME month			List what I did on 'month'
"""

"""
	DB struct
	timestamp
	event
"""

#JOURNAL_DATA_FILE=os.getenv("HOME")+"/work/hobby/journal/myold.db"
JOURNAL_DATA_FILE="myold.db"

class journal():
	def __init__(self):
		s = struct.pack("HHHH", 0, 0, 0, 0)
		self.lines, self.columns = struct.unpack("HHHH", fcntl.ioctl(sys.stdout.fileno(), termios.TIOCGWINSZ, s))[:2]

		self.columns -= 12
		self.cursor = False

		self.connectDB()

		self.tagList = {}
		self.prjList = {}

	def connectDB(self):
		# +---------+-------------+---------+
		# |  ID(*)  |  Timestamp  |  Entry  | 
		# +---------+-------------+---------+
		# ID is assigned automatically

		self.connection = sqlite3.connect(JOURNAL_DATA_FILE)

		if self.connection == None:
			print("Fail to open DB file %s\nExit..." %JOURNAL_DATA_FILE)
			sys.exit()

		if os.path.getsize(JOURNAL_DATA_FILE) == 0:
			print ("Create a new database")
			self.connection.execute('''CREATE TABLE journal 
				(id integer primary key AUTOINCREMENT, 
				timestamp DATETIME NOT NULL, 
				entry VARCHAR NOT NULL);''')
			self.connection.commit()

		self.cursor = self.connection.cursor()
		self.connection.text_factory = str		# enable Korean Input
#		else:
#			print ("Use existing database")

	def closeDB(self):
		self.cursor.close()
		self.connection.close()

	def add(self, date, event):
		self.cursor.execute('INSERT INTO journal VALUES (null, ?, ?)', (date, event))
		self.connection.commit()

	def printGroup(self, title, d):
		print("="*90)
		print("%s" %(title))
		print("="*90)

		count = 0
		for k, v in OrderedDict(sorted(d.items(), key=lambda d: d[0], reverse=False)).items():
			buf = "    %s (%u) " %(k, v)
			print("%-25s" %(buf), end="")
			count += 1
			if (count % 4 == 0):
				print("")
		print("\n")

	def printProject(self, d):
		self.printGroup("Projects", d)

	def printTag(self, d):
		self.printGroup("Tags", d)

	def printReverseTag(self, d):
		print("="*90)
		print("Tags sorted in count")
		print("="*90)

		rvsTagList = {}

		# first make a dictionary as count:tag
		for tag in d.keys():
			count = d[tag]
			if rvsTagList.has_key(count):
				rvsTagList[count].append(tag)
			else:
				rvsTagList[count] = [tag]
		
		# print tags based on the count in reverse(from the largest)
		countsList = rvsTagList.keys()
		for tagCount in sorted(countsList, reverse=True):
			count = 0
			print ("%4u : " %(tagCount), end="")
			for tag in rvsTagList[tagCount]:
				buf = "  %s " %(tag)
				print("%-20s" %(buf), end="")
				count += 1
				if (count % 5 == 0) and count != len(rvsTagList[tagCount]):
					print("\n       ", end="")
			print ("")
		print ("")
			

	def analyze(self, entry):
		line = entry.split()

		for word in line:
			if (word[0] == "+") is True:
				try:
					self.tagList[word[1:]] += 1
				except:
					self.tagList[word[1:]] = 1
			elif (word[0:2] == "p:") is True:
				try:
					self.prjList[word[2:]] += 1
				except:
					self.prjList[word[2:]] = 1

	def summary(self):
		count = 0

		# maybe it is better to add project as Db field
		self.cursor.execute('SELECT * FROM journal')

		for row in self.cursor:
			self.analyze(row[2])
			count += 1
		
		print("Total %u logs" %count)
		self.printTag(self.tagList)
		self.printReverseTag(self.tagList)
		self.printProject(self.prjList)

	def display(self, target_date, keyword = ""):
		count = 0
		startOffset = 0

		self.cursor.execute('SELECT * FROM journal')
		old_date = ""
		item_date = ""
		item_time = ""

		for row in self.cursor:
			item_date = row[1][0:10]
			item_time = row[1][11:19]

			# if date is specified
			if target_date:
				if target_date != item_date[0:len(target_date)]:
					continue

			# if 'search' case
			if keyword != "":
				if row[2].find(keyword) == -1:
					continue

			if old_date != item_date:
				print ("\n"+item_date)
				print ("-"*10)
				old_date = item_date

			#if text is too long, segment it
#			print (len(row[2]) + len(item_time), self.columns)
			if len(row[2]) + len(item_time) > self.columns:
				startOffset = 0

				for line_num in range(0, len(row[2])/self.columns + 1):
					length = self.columns
						
					if (startOffset +  length) <= len(row[2]):
						try:
							while row[2][startOffset + length -1] != ' ':
								length -= 1
						except:
							print (row[2], len(row[2]))
							print (startOffset, length)
							print (row[2][startOffset + length])
							sys.exit()
					
					if line_num > 0:
						print (" "*10, row[2][startOffset : startOffset + length])
					else:
						print ("*", item_time, row[2][startOffset : startOffset + length])

					startOffset += length
			else:
				print ("*", item_time, row[2])

			self.analyze(row[2])
			count += 1

		print ("")

if __name__ == "__main__":

	j = journal()

	if len(sys.argv) > 1:		# add
		if sys.argv[1] in ["add", "addp"]:
			date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
			event = " ".join(sys.argv[2:])

			if sys.argv[1] == "add":
				if event.find("p:") == -1:
					print("Error! Specify project with p:")
					sys.exit()

			print ("Add one entry @ %s" %date)

			j.add(date, event)

#		if sys.argv[1] == "update":

		elif sys.argv[1] in ["summary", "sum"]:
			j.summary()
		elif sys.argv[1] == "search":
			event = " ".join(sys.argv[2:])
			j.display("", event)
		elif sys.argv[1] in ["year", "y"]:
			j.display(time.strftime("%Y", time.localtime()))
		elif sys.argv[1] in ["month", "m"]:
			j.display(time.strftime("%Y-%m", time.localtime()))
		elif sys.argv[1] in ["day", "d", "today", "t"]:
			j.display(time.strftime("%Y-%m-%d", time.localtime()))
			j.display(time.strftime("%Y-%m", time.localtime()))
			j.display(time.strftime("%Y", time.localtime()))
		elif sys.argv[1] in ["help", "-h", "--help"]:
			print (USAGE.replace("PROG_NAME", PROG_NAME))
		else:
			if sys.argv[1][0] == '2':
				if eval(sys.argv[1]) >= 2000 and eval(sys.argv[1]) < 2030:
					j.display(sys.argv[1])
	else:
		j.display(time.strftime("%Y", time.localtime()), "")
	
	j.closeDB()

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
	convert DB schema to new one
"""

PROG_NAME = "convert.py"

USAGE = """
	PROG_NAME oldFile newFile
"""


if len(sys.argv) != 3:
	print(USAGE.replace("PROG_NAME", PROG_NAME))
	sys.exit()

srcFile = sys.argv[1]
tgtFile = sys.argv[2]

# +---------+-------------+---------+
# |  ID(*)  |  Timestamp  |  Entry  | 
# +---------+-------------+---------+
# ID is assigned automatically

# open source file 
srcConnection = sqlite3.connect(srcFile)
if os.path.isfile(srcFile) is False:
	print("File %s is not exist\nExit..." %(srcFile))
	sys.exit()

# open target file 
tgtConnection = sqlite3.connect(tgtFile)
if os.path.isfile(tgtFile) is True and os.path.getsize(tgtFile) != 0:
	print("Target file is already exist.\nExit...")
	srcConnection.close()
	sys.exit()

tgtConnection.execute('''CREATE TABLE journal 
	(id integer primary key AUTOINCREMENT, 
	timestamp DATETIME NOT NULL, 
	project VARCHAR, 
	entry VARCHAR NOT NULL);''')
tgtConnection.commit()

# read all entries from source file
srcCursor = srcConnection.cursor()
srcConnection.text_factory = str		# enable Korean Input

srcCursor.execute('SELECT * FROM journal')
tgtCursor = tgtConnection.cursor()
tgtConnection.text_factory = str		# enable Korean Input

# write to target file with a explicit project field
for row in srcCursor:
	idx = row[0]
	date = row[1]
	entry = row[2]
	line = row[2].split()

	project = ""
	# FIXME if more than two projects are specified???
	print row[2].count("p:")
#	if row[2].count("p:") == 1:
#		for word in line:
#			if row[2].count("p:") == 1:
#				if (word[0:2] == "p:") is True:
#			project = word[2:]
#		else:

	print("%s %s %-10s %s" %(idx, date, project, entry))

srcCursor.close()
srcConnection.close()
tgtCursor.close()
tgtConnection.close()

#	tgtCursor.execute('INSERT INTO journal VALUES (null, ?, ?)', (date, project, event))


#!/usr/bin/env python

import subprocess, shlex
import argparse
import tempfile #could maybe also use os.tmpfile()

import time

import os,os.path,sys

try: input = raw_input;
except: pass; #2.x and 3.x compatibility

HELPTEXT = \
"""
journal.py attemps to be a simple-as-possible-but-not-simpler personal diary program using gpg for encryption. To that end, the entire program is contained in a single file, and the only dependencies are this file, python 2.7 or greater, and gpg.

"""
EPILOG = \
"""
Copyright Harry Stern 2012 
Released under the MIT License <http://opensource.org/licenses/MIT>
"""

####--------####
#   config     #
####--------####
JOURNALDIR = "."
TEMPDIR = None #uses tempfile.mkstemp()'s default directory when None
JOURNALEXT = ".jrn"

EDITORCMD = "nano %(file)s"

####--------####
#   journal    #
####--------####

def del_tempfile(temp_file):

	#first, try using shred if on Linux
	#shred is not a panacea; in particular, on some journaled filesystems it is kind of useless
	#unless you can guarantee the journal is also overwritten
	if os.uname()[0] == 'Linux':
		try:
			subprocess.call(['shred', temp_file])
		except OSError as err:
			if err.errno == 2:
				pass
			else:
				raise err
	#XXX find out what to do on windows
	try:
		os.unlink(temp_file)
	except OSError: #only on Windows, according to python docs, so I haven't tested
		pass

def encrypt(temp_file, entry_file):
	#--no-use-agent is because gpg complains when gpg-agent isn't running
	#XXX should add option for other ciphers, though really you should configure that in .gnugp/gpg.conf
	subprocess.call(["gpg", "--no-use-agent", "--output", entry_file, "--symmetric", temp_file])

def _get_entry_file():
	#file name is year month day hour minute in such a way that when sorted alphanumerically, oldest comes first
	fname = time.strftime("%Y%m%d%H%M") + JOURNALEXT
	return os.path.join(os.path.abspath(JOURNALDIR), fname) 

def new_entry(args):

	#create temp file, but we're just passing the file name to another program
	fd, tempf = tempfile.mkstemp()
	os.close(fd)

	outfile = None

	#check options, probably could do this elsewhere after restructuring
	if args.dir is not None:
		global JOURNALDIR
		JOURNALDIR = args.dir

	if args.output is not None:
		outfile = args.output

	#spawn editor program
	try:
		command = shlex.split(EDITORCMD %{"file":tempf}) #file name is not always the last argument, shlex.split should be fine even for windows
		subprocess.call(command)
	except OSError as err:
		if err.errno == 2: #"No such file or directory", program doesn't exist.
			print "editor command failed: file not found. exiting."
			sys.exit()
		else:
			raise err
	#some programs like gedit return 0 even though it hasn't actually closed
	#in addition, this lets you do whatever you want with the temp file before it's encrypted
	input("Press Enter when done editing.")	

	if outfile is None:
		outfile = _get_entry_file()

	encrypt(tempf, outfile)
	
	del_tempfile(tempf)
	

def view_entry():
	pass

def edit_entry():
	pass


####--------####
#   parser     #
####--------####
parser = argparse.ArgumentParser(description=HELPTEXT, epilog=EPILOG)
subparsers = parser.add_subparsers()
#the problem with subparsers is that they are mandatory and you can't just output help if none are used
#XXX fix somehow? maybe just try/except: pass; 

##journal.py add [args]
add_entry_parser = subparsers.add_parser("add", help="create a journal entry")

add_entry_parser.set_defaults(action=new_entry)

#output options. 
add_entry_parser.add_argument("-d", "--dir", help="Directory in which the journal files should go.")
add_entry_parser.add_argument("-o", "--output", help="Output the journal file directly to a specific file.")

##journal.py view [args]
view_entry_parser = subparsers.add_parser("view", help="view a journal entry")

view_entry_parser.set_defaults(action=view_entry)

##journal.py edit [args]
edit_entry_parser = subparsers.add_parser("edit", help="edit a journal entry")

edit_entry_parser.set_defaults(action=edit_entry)

#parse command line args and execute proper function
args = parser.parse_args()
args.action(args)

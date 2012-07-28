#!/usr/bin/env python

import subprocess
import argparse
import tempfile

import sys

HELPTEXT = \
"""
journal.py attemps to be a simple-as-possible-but-not-simpler personal diary program using gpg for encryption. To that end, the only dependencies are this file, python 2.7 or greater, and gpg.

"""

####--------####
#   config     #
####--------####
JOURNALDIR = "."
TEMPDIR = "/tmp"

EDITORCMD = "nano"

####--------####
#   journal    #
####--------####

def new_entry():
	pass

def view_entry():
	pass

def edit_entry():
	pass

#subprocess.call("gpg --no-use-agent -c test.txt", shell=True)


####--------####
#   parser     #
####--------####
parser = argparse.ArgumentParser(description="A secure text file journal written as simply as possible.")

parser.parse_args()


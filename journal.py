#!/usr/bin/env python

import subprocess, shlex
import argparse
import tempfile

import time

import os, os.path
import sys
import stat

try: input = raw_input;  # 2.x and 3.x compatibility hack
except: pass;

HELPTEXT = """
journal.py attemps to be a simple-as-possible-but-not-simpler personal diary program using gpg for encryption. \
To that end, the entire program is contained in a single file, and the only dependencies are this file, python 2.7 or greater, and gpg.\
An effort has been made to allow almost any text editing program to be used in conjunction with journal.py.
"""

EPILOG = """
(c) 2012 Harry Stern and released under the MIT License <http://opensource.org/licenses/MIT>
"""

#    config    #
JOURNALDIR = "."
TEMPDIR = None  # uses tempfile.mkstemp()'s default directory when None

JOURNALFMT = "%Y%m%d%H%M"
JOURNALEXT = ".jrn"

EDITORCMD = "nano %(file)s"


#    journal    #
def create_tempfile():
    #create temp file, but we're just passing the file name to another program
    #mostly it's for the os-independent file creation
    #XXX there is probably a better way to do this
    fd, tempf = tempfile.mkstemp(text=True)
    os.close(fd)

    return tempf


def del_tempfile(temp_file):
    #shred is not a panacea; in particular, on some journaled filesystems it is kind of useless
    #unless you can guarantee the fs journal is also overwritten
    try:
        subprocess.call(['shred', temp_file])  # i am probably missing some important option or something here
    except OSError as err:
        if type(err) == FileNotFoundError:
            pass # XXX maybe we should warn about not having shred
        else:
            raise err
    #XXX find out shred's equivalent on windows

    try:
        os.unlink(temp_file)
    except OSError:
        pass

#---


def encrypt(temp_file, entry_file):
    #--no-use-agent is because we don't need gpg-agent
    #--no-mdc-warning is because MDC integrity protection is irrelevant in our case
    #--quiet suppresses messages telling you what algorithm the file is encrypted with
    #XXX should add option for other ciphers, though really you should configure that in .gnupg/gpg.conf
    subprocess.call(["gpg", "--no-use-agent", "--output", entry_file, "--symmetric", temp_file])


def decrypt(entry_file, temp_file):
    #--yes is because gpg asks "do you want to overwrite"
    #the empty temp file we just created
    subprocess.call(["gpg", "--no-use-agent", "--no-mdc-warning", "--yes", "--quiet", "--output", temp_file, "--decrypt", entry_file])

#---


def spawn_editor(temp_file):
    try:
        command = shlex.split(EDITORCMD % {"file": temp_file})
        subprocess.call(command)
    except OSError as err:
        if err.errno == 2:  # "No such file or directory", program doesn't exist.
            print("Editor command failed: File not found. exiting.")
            sys.exit()
        else:
            raise err

    #this lets you do whatever you want with the temp file before it's encrypted/deleted
    input("Press Enter when done.")

#---


def _get_entry_file(journal_dir):
    fname = time.strftime(JOURNALFMT) + JOURNALEXT
    return os.path.join(os.path.abspath(journal_dir), fname)


def new_entry(args):
    temp_file = create_tempfile()

    #check options, probably could do this elsewhere after restructuring
    journal_dir = args.dir
    entry_file = args.output

    spawn_editor(temp_file)

    #currently do this here so that it is created at the right time, and not when args are parsed
    #may be better the other way though, since the fs keeps track of date created
    if entry_file is None:
        entry_file = _get_entry_file(journal_dir)

    encrypt(temp_file, entry_file)

    del_tempfile(temp_file)

#---


def _get_latest_entry(journal_dir):
    #get all files in journal directory whose extension is the right one
    files = (f for f in os.listdir(journal_dir) if os.path.splitext(f)[1] == JOURNALEXT)

    #return a sorted list of the last modified times of the files, largest (i.e. most recent) first
    times = sorted(((f, os.path.getmtime(f)) for f in files), key=lambda l: l[1], reverse=True)

    if times:
        return times[0][0]
    else:
        print("No journal entries found. Exiting.")
        sys.exit()


def view_entry(args):
    temp_file = create_tempfile()

    journal_dir = args.dir
    entry_file = args.entry

    if entry_file is None:
        entry_file = _get_latest_entry(journal_dir)

    decrypt(entry_file, temp_file)
    os.chmod(entry_file, stat.S_IREAD)  # ro so that you don't get any funny ideas, does work on windows

    spawn_editor(temp_file)

    del_tempfile(temp_file)

#---


def edit_entry():
    pass


#    parser    #
parser = argparse.ArgumentParser(description=HELPTEXT, epilog=EPILOG)
subparsers = parser.add_subparsers()

#the problem with subparsers is that you can't just output help if none are used
#XXX fix somehow? maybe just try/except: pass;
#also they're kind of convoluted and stupid

##journal.py add [args]
add_entry_parser = subparsers.add_parser("add", help="Create a journal entry.")
add_entry_parser.set_defaults(cmd=new_entry)

#options
add_entry_parser.add_argument("-d", "--dir", default=JOURNALDIR,
        help="Directory in which the journal files are stored. Default is current directory.")

add_entry_parser.add_argument("-o", "--output",
        help="Journal entry file output name. Default is YYYYMMDDHHMM.jrn.")

##journal.py view [args]
view_entry_parser = subparsers.add_parser("view", help="View a journal entry.")
view_entry_parser.set_defaults(cmd=view_entry)

#options
view_entry_parser.add_argument("-d", "--dir", default=JOURNALDIR,
        help="Directory in which the journal files are stored. Default is current directory.")

view_entry_parser.add_argument("entry",
        help="Journal entry id to view. Default is latest.")

##journal.py edit [args]
edit_entry_parser = subparsers.add_parser("edit", help="Edit a journal entry".)
edit_entry_parser.set_defaults(cmd=edit_entry)


if __name__ == '__main__':
    args = parser.parse_args()
    args.cmd(args)

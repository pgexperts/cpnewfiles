#!/usr/bin/python
#
#    cpnewfiles.py is licensed under the PostgreSQL License:
#
#    Copyright (c) 2012, PostgreSQL, Experts, Inc.
#
#    Permission to use, copy, modify, and distribute this software and its
#    documentation for any purpose, without fee, and without a written
#    agreement is hereby granted, provided that the above copyright notice and
#    this paragraph and the following two paragraphs appear in all copies.
#
#    IN NO EVENT SHALL POSTGRESQL EXPERTS, INC. BE LIABLE TO ANY PARTY FOR
#    DIRECT, INDIRECT, SPECIAL, INCIDENTAL, OR CONSEQUENTIAL DAMAGES, INCLUDING
#    LOST PROFITS, ARISING OUT OF THE USE OF THIS SOFTWARE AND ITS
#    DOCUMENTATION, EVEN IF POSTGRESQL EXPERTS, INC. HAS BEEN ADVISED OF THE
#    POSSIBILITY OF SUCH DAMAGE.
#
#    POSTGRESQL EXPERTS, INC. SPECIFICALLY DISCLAIMS ANY WARRANTIES, INCLUDING,
#    BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
#    FOR A PARTICULAR PURPOSE. THE SOFTWARE PROVIDED HEREUNDER IS ON AN "AS IS"
#    BASIS, AND POSTGRESQL EXPERTS, INC. HAS NO OBLIGATIONS TO PROVIDE
#    MAINTENANCE, SUPPORT, UPDATES, ENHANCEMENTS, OR MODIFICATIONS.


import os
import re
import shutil
import sys
import shelve
import signal
import atexit
from datetime import datetime, timedelta
from optparse import OptionParser

LOCKFILE = '.cpnewfiles_lockfile'

def sigint(signal, frame):
    sys.stderr.write("Exited with SIGINT.\n")
    
    sys.exit(1)

signal.signal(signal.SIGINT, sigint)


parser = OptionParser()

parser.add_option('-H', "--hours", action="store", type="int", dest="hours",
                  default=1)
parser.add_option('-m', "--minutes", action="store", type="int", dest="minutes",
                  default=0)
parser.add_option('', "--debug", action="store_const", const=1,
                  dest="debug", default=0)

(options, args) = parser.parse_args()


sourcedir = args[0]
destdir = args[1]

LOCKFILE_PATH = os.path.join(sourcedir, LOCKFILE)

@atexit.register
def remove_lockfile():
    try:
        os.remove(LOCKFILE_PATH)
    except OSError:
        pass

def create_lockfile():
    try:
        os.fdopen(open(LOCKFILE_PATH, os.O_EXCL | os.O_CREAT))
    except OSError:
        sys.stderr.write("Could not create lockfile %s" % LOCKFILE_PATH)
        sys.exit(1)


create_lockfile()

keeptime = datetime.now() - timedelta(hours=options.hours, minutes=options.minutes)

shelf = shelve.open(os.path.join(sourcedir, ".cpnewfiles"), writeback=True)
try:
  lastfilets = shelf["lastfilets"]
except:
  lastfilets = datetime.min

if options.debug:
  print "Sourcedir: " + sourcedir
  print "Destdir: " + destdir

  print "Keep time: " + str(keeptime)
  print "Last file ts: " + str(lastfilets)

# handy function for getting a directory listing in mtime order
# from here: http://stackoverflow.com/questions/168409/how-do-you-get-a-directory-listing-sorted-by-creation-date-in-python
def getfiles(dirpath):
  a = [s for s in os.listdir(dirpath)
    if os.path.isfile(os.path.join(dirpath, s))]
  a.sort(key=lambda s: os.path.getmtime(os.path.join(dirpath, s)))
  return a

# iterate over the files in the source directory
for file in getfiles(sourcedir):
  # We don't want to operate on dotfiles
  if not re.match('^\.', file):
    fullpath = os.path.join(sourcedir, file)
    ts = datetime.fromtimestamp(os.stat(os.path.join(sourcedir, file)).st_mtime)
    if options.debug:
      print "File: " + fullpath
      print "Timestamp: " + str(ts) + " lastfilets: " + str(lastfilets)
    if ts > lastfilets:
      try:
          shutil.copy(fullpath, destdir)
          shelf["lastfilets"] = ts
          if ts < keeptime:
            try:
              if options.debug: 
                print "deleting " + fullpath
              os.remove(fullpath)
            except:
              print "Error deleting " + fullpath
              # we don't exit here because this should just get taken
              # care of on the next run
      except:
        print "Error copying " + fullpath + \
          " to " + destdir
        shelf.close()
        sys.exit(1)
    else:
      if options.debug:
        print "Not copying due to age"

shelf.close()

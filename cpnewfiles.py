#!/usr/bin/python

import os
import re
import shutil
import sys
import shelve
from datetime import datetime, timedelta
from optparse import OptionParser


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
      except:
        print "Error copying " + fullpath + \
          " to " + destdir
        shelf.close()
        sys.exit(1)
    else:
      if options.debug:
        print "Not copying due to age"

shelf.close()

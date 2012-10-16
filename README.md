cpnewfiles
==========

Copy files from a source directory to a destination directory and keep track of the last copied file's timestamp. Next run, only copy new files.

Delete copied files but keep around an hour by default.  This is configurable
via the --hours and --minutes command line options.

Example usage:

cpnewfiles.py --hours=2 --minutes=30 /some/source/dir /some/dest/dir

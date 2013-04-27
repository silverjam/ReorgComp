# File: utils.py

####

import os
import sys

from nose.tools import nottest

####


@nottest
def delete_test_file(filen):
	if os.path.exists(filen) and os.path.isfile(filen):
		os.remove(filen)
	elif not os.path.isfile(filen):
		sys.stderr.write("warning: not a file: '%s'" % (filen,))

@nottest
def delete_later(filen):
	def func():
		return delete_test_file(filen)
	return func

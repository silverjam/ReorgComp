# File: test_basics.py

####

from os import path

import tempfile

from nose.tools import with_setup

from utils import delete_later

from reorgcomp.rename import save_output
from reorgcomp.rename import read_input
from reorgcomp.rename import detect_moves

####

def T(filename):
	return path.join(tempfile.gettempdir(), filename)


test_saveload_file = T("test_saveload_file")

@with_setup(teardown=delete_later(test_saveload_file))
def test_saveload():
	testdata = [1,2,3,4,5]
	save_output(test_saveload_file, testdata)
	loaded_data = read_input(test_saveload_file)
	assert loaded_data == testdata


test_detectmoves_file = T("test_detectmoves_file")

@with_setup(teardown=delete_later(test_detectmoves_file))
def test_detectmoves():

	# detect_moves(basenew = None, baseold = None, outfile = None):

	actual = detect_moves("tests/data/B", "tests/data/A", test_detectmoves_file)
	expected = [
		('tests/data/A/foo/bar/baz/Greeting.txt',
  			[('tests/data/B/baz/bar/foo/Greeting.txt', 1.0)])
		]

	assert actual == expected

	loaded = read_input(test_detectmoves_file)
	assert loaded == expected

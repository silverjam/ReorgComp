# File: test_basics.py

####

from os import path

import tempfile

from nose.tools import with_setup

from utils import delete_later

import reorgcomp.rename

from reorgcomp.rename import save_output
from reorgcomp.rename import read_input
from reorgcomp.rename import detect_moves
from reorgcomp.rename import rename_dirs
from reorgcomp.rename import parse_arguments

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
  			[('tests/data/B/baz/bar/foo/Greeting.txt', 1.0),
  			 ('tests/data/B/baz/Greeting.txt', 0.36363636363636365)])
		]

	assert expected == actual, (expected, actual)

	loaded = read_input(test_detectmoves_file)
	assert expected == loaded, (expected, loaded)


def test_rename_dirs():

	def _walk(d):
		assert d == '.'
		yield ("", ["bazfoo"], "foofoo")

	def _rename(from_, to):
		assert from_ == "bazfoo"
		assert to == "bazbar"

	parse_arguments(["--addrename", "foo", "bar"])
	rename_dirs(os_walk=_walk, os_rename=_rename)
	

def test_rename_target():

	rename_target = "rename_target"
	parse_arguments(["--rename", rename_target])

	def _walk(d):
		assert d == rename_target
		yield ("", ["bazfoo"], "foofoo")

	def _rename(from_, to):
		pass

	rename_dirs(os_walk=_walk, os_rename=_rename)
	

def unpretend(val):
	def func():
		reorgcomp.rename.PRETEND_OPS = val


@with_setup(teardown=unpretend(False))
def test_pretend():

	parse_arguments(["--pretend", "--rename", "bacon"])

	def _walk(d):
		yield ("", ["bazfoo"], "foofoo")

	notcalled = [True]

	def _rename(from_, to):
		notcalled[0] = False

	rename_dirs(_walk, _rename)

	assert notcalled[0]

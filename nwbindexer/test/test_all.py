# pytest for nwbindexer installation
# tests to make sure sample data files are available, then
# tests commands: build_index, query_index and search_nwb (four tests total)

import os
import pytest
import sys
import subprocess
import shutil
import importlib

test_data_dir = os.path.dirname(__file__)  # should be ".../nwbindexer/test"
file1_path = os.path.join(test_data_dir, "ecephys_example.nwb")
file2_path = os.path.join(test_data_dir, "ophys_example.nwb")
index_file = "nwb_index.db"

def test_parsimonious_installed():
	parsimonious_spec = importlib.util.find_spec("parsimonious")
	parsimonious_installed = parsimonious_spec is not None
	assert parsimonious_installed is True


# create temporary directory to use for storing test index file.  Based on:
# https://stackoverflow.com/questions/25525202/py-test-temporary-folder-for-the-session-scope
# https://stackoverflow.com/questions/51593595/pytest-auto-delete-temporary-directory-created-with-tmpdir-factory
@pytest.fixture(scope='module')
def tmpdir_module(tmpdir_factory):
	"""A tmpdir fixture for the module scope. Persists throughout the module."""
	my_tmpdir = tmpdir_factory.mktemp("tmpdir")
	yield my_tmpdir 
	shutil.rmtree(str(my_tmpdir))

def test_check_sample_files():
	# make sure can access sample files
	global test_data_dir, file1_path, file2_path
	assert os.path.isdir(test_data_dir)
	assert os.path.isfile(file1_path)
	assert os.path.isfile(file2_path)

def run_command(cmd):
	print("> %s" % cmd)
	p = subprocess.run(cmd, shell=True, capture_output=True)
	output = p.stdout.decode("utf-8").replace("\r", "")  # strip ^M characters (line return) from windows output
	error = p.stderr.decode("utf-8").replace("\r", "")
	return output + error

def test_build_index(tmpdir_module):
	global test_data_dir, index_file, file1_path, file2_path
	index_file_path = os.path.join(tmpdir_module, index_file)
	# index file should not exist
	assert not os.path.isfile(index_file_path)
	cmd = "python -m nwbindexer.build_index %s %s" % (test_data_dir, index_file_path)
	expected_output = """Creating database '%s'
scanning directory %s
Scanning file 1: %s
Scanning file 2: %s
""" % (index_file_path, test_data_dir, file1_path, file2_path)
	output = run_command(cmd)
	assert output == expected_output

query1 = '"general/optophysiology/*: excitation_lambda == 600.0"'
query2 = '"general/extracellular_ephys/tetrode1: location LIKE \'%hippocampus\'"'


def test_query_index(tmpdir_module):
	global query1, query2, index_file, file1_path, file2_path
	index_file_path = os.path.join(tmpdir_module, index_file)
	cmd = "python -m nwbindexer.query_index %s %s" % (index_file_path, query1)
	expected_output = """Opening '%s'
Found 1 matching files:
[   {   'file': '%s',
        'subqueries': [   [   {   'node': '/general/optophysiology/my_imgpln',
                                  'vind': {'excitation_lambda': 600.0},
                                  'vtbl': {}}]]}]
""" % (index_file_path, file2_path)
	output = run_command(cmd)
	assert output == expected_output
	cmd = "python -m nwbindexer.query_index %s %s" % (index_file_path, query2)
	expected_output = """Opening '%s'
Found 1 matching files:
[   {   'file': '%s',
        'subqueries': [   [   {   'node': '/general/extracellular_ephys/tetrode1',
                                  'vind': {   'location': 'somewhere in the '
                                                          'hippocampus'},
                                  'vtbl': {}}]]}]
""" % (index_file_path, file1_path)
	output = run_command(cmd)
	assert output == expected_output

def test_search_nwb(tmpdir_module):
	# index_file_path = os.path.join(tmpdir_module, index_file)
	global query1, query2, test_data_dir, file1_path, file2_path
	cmd = "python -m nwbindexer.search_nwb %s %s" % (test_data_dir, query1)
	expected_output = """Found 1 matching files:
[   {   'file': '%s',
        'subqueries': [   [   {   'node': '/general/optophysiology/my_imgpln',
                                  'vind': {'excitation_lambda': 600.0},
                                  'vtbl': {}}]]}]
""" % file2_path
	output = run_command(cmd)
	assert output == expected_output
	cmd = "python -m nwbindexer.search_nwb %s %s" % (test_data_dir, query2)
	expected_output = """Found 1 matching files:
[   {   'file': '%s',
        'subqueries': [   [   {   'node': '/general/extracellular_ephys/tetrode1',
                                  'vind': {   'location': 'somewhere in the '
                                                          'hippocampus'},
                                  'vtbl': {}}]]}]
""" % file1_path
	output = run_command(cmd)
	assert output == expected_output

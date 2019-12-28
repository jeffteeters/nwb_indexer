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
basic_path = os.path.join(test_data_dir, "example_file_path.nwb") # was originally "basic_example.nwb"
ecephys_path = os.path.join(test_data_dir, "ecephys_example.nwb")
ophys_path = os.path.join(test_data_dir, "ophys_example.nwb")
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
	global test_data_dir, basic_path, ecephys_path, ophys_path
	assert os.path.isdir(test_data_dir)
	assert os.path.isfile(basic_path)
	assert os.path.isfile(ecephys_path)
	assert os.path.isfile(ophys_path)

def run_command(cmd):
	print("> %s" % cmd)
	p = subprocess.run(cmd, shell=True, capture_output=True)
	output = p.stdout.decode("utf-8").replace("\r", "")  # strip ^M characters (line return) from windows output
	error = p.stderr.decode("utf-8").replace("\r", "")
	return output + error

def test_build_index(tmpdir_module):
	global test_data_dir, index_file, basic_path, ecephys_path, ophys_path
	index_file_path = os.path.join(tmpdir_module, index_file)
	# index file should not exist
	assert not os.path.isfile(index_file_path)
	cmd = "python -m nwbindexer.build_index %s %s" % (test_data_dir, index_file_path)
	expected_output = """Creating database '%s'
scanning directory %s
Scanning file 1: %s
Scanning file 2: %s
Scanning file 3: %s
""" % (index_file_path, test_data_dir, ecephys_path, basic_path, ophys_path)
	output = run_command(cmd)
	assert output == expected_output

query1 = '"general/optophysiology/*: excitation_lambda == 600.0"'
query2 = '"general/extracellular_ephys/tetrode1: location LIKE \'%hippocampus\'"'
query3 = "units: id, location == 'CA3' & quality > 0.8"


def test_query_index(tmpdir_module):
	global query1, query2, query3, index_file, ecephys_path, ophys_path
	index_file_path = os.path.join(tmpdir_module, index_file)
	cmd = "python -m nwbindexer.query_index %s %s" % (index_file_path, query1)
	expected_output = """Opening '%s'
Found 1 matching files:
[   {   'file': '%s',
        'subqueries': [   [   {   'node': '/general/optophysiology/my_imgpln',
                                  'vind': {'excitation_lambda': 600.0},
                                  'vtbl': {}}]]}]
""" % (index_file_path, ophys_path)
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
""" % (index_file_path, ecephys_path)
	output = run_command(cmd)
	assert output == expected_output
	cmd = "python -m nwbindexer.query_index %s \"%s\"" % (index_file_path, query3)
	expected_output = """Opening '%s'
Found 1 matching files:
[   {   'file': '%s',
        'subqueries': [   [   {   'node': '/units',
                                  'vind': {},
                                  'vtbl': {   'child_names': [   'id',
                                                                 'location',
                                                                 'quality'],
                                              'combined': [   {   'id': 2,
                                                                  'location': 'CA3',
                                                                  'quality': 0.85}],
                                              'row_values': [   (   2,
                                                                    'CA3',
                                                                    0.85)]}}]]}]
""" % (index_file_path, basic_path)
	output = run_command(cmd)
	assert output == expected_output

def test_search_nwb(tmpdir_module):
	# index_file_path = os.path.join(tmpdir_module, index_file)
	global query1, query2, query3, test_data_dir, basic_path, ecephys_path, ophys_path
	cmd = "python -m nwbindexer.search_nwb %s %s" % (test_data_dir, query1)
	expected_output = """Found 1 matching files:
[   {   'file': '%s',
        'subqueries': [   [   {   'node': '/general/optophysiology/my_imgpln',
                                  'vind': {'excitation_lambda': 600.0},
                                  'vtbl': {}}]]}]
""" % ophys_path
	output = run_command(cmd)
	assert output == expected_output
	cmd = "python -m nwbindexer.search_nwb %s %s" % (test_data_dir, query2)
	expected_output = """Found 1 matching files:
[   {   'file': '%s',
        'subqueries': [   [   {   'node': '/general/extracellular_ephys/tetrode1',
                                  'vind': {   'location': 'somewhere in the '
                                                          'hippocampus'},
                                  'vtbl': {}}]]}]
""" % ecephys_path
	output = run_command(cmd)
	assert output == expected_output
	cmd = "python -m nwbindexer.search_nwb %s \"%s\"" % (test_data_dir, query3)
	expected_output = """Found 1 matching files:
[   {   'file': '%s',
        'subqueries': [   [   {   'node': '/units',
                                  'vind': {},
                                  'vtbl': {   'child_names': [   'id',
                                                                 'location',
                                                                 'quality'],
                                              'combined': [   {   'id': 2,
                                                                  'location': 'CA3',
                                                                  'quality': 0.85}],
                                              'row_values': [   (   2,
                                                                    'CA3',
                                                                    0.85)]}}]]}]
""" % basic_path
	output = run_command(cmd)
	assert output == expected_output
import os
import sys
import subprocess

test_data_dir = "test_data"
index_file = "nwb_index.db"
cwd = os.getcwd()

def restore_directory():
	global cwd
	remove_index_file()
	os.chdir(cwd)

def remove_index_file():
	global index_file
	if os.path.isfile(index_file):
		os.remove(index_file)

def abort(error_message = None):
	global cwd
	if error_message:
		print(error_message)
	restore_directory()
	sys.exit("Aborting.")

def check_sample_files():
	global test_data_dir
	if not os.path.isdir(test_data_dir):
		abort("Directory '%s' not found." % test_data_dir)
	test_files = ["EC9_B15.nwb", "GP31_B65.nwb"]
	for file in test_files:
		path = os.path.join(test_data_dir, file)
		if not os.path.isfile(path):
			abort("Test file '%s' not found." % path)


def run_command(cmd, expected_output):
	print("> %s" % cmd)
	p = subprocess.run(cmd, shell=True, capture_output=True)
	output = p.stdout.decode("utf-8").replace("\r", "")  # strip ^M characters (line return) from windows output
	if output != expected_output:
		print("Following command failed:\n%s" % cmd)
		print("Expected:\n%s" % expected_output)
		print("Found:\n%s" % output)
		abort()

def check_build_index():
	global test_data_dir, index_file
	os.chdir(test_data_dir)
	if os.path.isfile(index_file):
		remove_index_file()
		print("previous '%s' removed." % index_file)
	# cmd = "python " + os.path.join("..", "build_index.py") + " " + os.path.join("..", "test_data")
	cmd = "python " + os.path.join("..", "build_index.py") + " ./"
	expected_output = """Creating database 'nwb_index.db'
scanning directory ./
Scanning file 1: ./EC9_B15.nwb
Warning: not indexing string array because too large (packed size = 12287, limit = 10000), at '/general/extracellular_ephys/electrodes/group'
Scanning file 2: ./GP31_B65.nwb
Warning: not indexing string array because too large (packed size = 12543, limit = 10000), at '/general/extracellular_ephys/electrodes/group'
"""
	run_command(cmd, expected_output)

query1 = '"general/subject: subject_id == \'EC9\'"'
query2 = '"general/subject: subject_id LIKE \'GP31%\'"'

def check_query_index():
	global query1, query2
	cmd = "python " + os.path.join("..", "query_index.py") + ' - ' + query1
	expected_output = """Opening 'nwb_index.db'
Found 1 matching files:
[   {   'file': './EC9_B15.nwb',
        'subqueries': [   [   {   'node': '/general/subject',
                                  'vind': {'subject_id': 'EC9'},
                                  'vtbl': {}}]]}]
"""
	run_command(cmd, expected_output)
	cmd = "python " + os.path.join("..", "query_index.py") + ' - ' + query2
	expected_output = """Opening 'nwb_index.db'
Found 1 matching files:
[   {   'file': './GP31_B65.nwb',
        'subqueries': [   [   {   'node': '/general/subject',
                                  'vind': {'subject_id': 'GP31'},
                                  'vtbl': {}}]]}]
"""
	run_command(cmd, expected_output)

def check_search_nwb():
	global query1, query2
	# cmd = "python " + os.path.join("..", "search_nwb.py") + " " + os.path.join("..", "test_data") + " " + query1
	cmd = "python " + os.path.join("..", "search_nwb.py") + " ./ " + query1
	expected_output = """Found 1 matching files:
[   {   'file': './EC9_B15.nwb',
        'subqueries': [   [   {   'node': '/general/subject',
                                  'vind': {'subject_id': 'EC9'},
                                  'vtbl': {}}]]}]
"""
	run_command(cmd, expected_output)
	# cmd = "python " + os.path.join("..", "search_nwb.py") + " " + os.path.join("..", "test_data") + " " + query2
	cmd = "python " + os.path.join("..", "search_nwb.py") + " ./ " + query2
	expected_output = """Found 1 matching files:
[   {   'file': './GP31_B65.nwb',
        'subqueries': [   [   {   'node': '/general/subject',
                                  'vind': {'subject_id': 'GP31'},
                                  'vtbl': {}}]]}]
"""
	run_command(cmd, expected_output)



def main():
	check_sample_files()
	check_build_index()
	check_query_index()
	check_search_nwb()
	restore_directory()
	print("All tests passed.")

main()

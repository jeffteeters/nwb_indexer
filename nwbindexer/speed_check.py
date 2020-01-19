
# script to test speed of queries

import os
import sys
import subprocess
# import re
import readline
import resource

import pprint
pp = pprint.PrettyPrinter(indent=4)

# python_tools_dir = os.getcwd()  # assumes this is running in same directory contaiing this file (speed_check.py)


# default values for command-line arguments
default_java_tool_dir = "/Users/jt/crcns/projects/petr_nwbqe_paper/NwbQueryEngine4"
# directory containg nwb files and also the index file (nwb_index.db) built by build_index.py
default_data_dir = "../sample_data"

# constants
java_cmd_prefix=("java -Djava.library.path=src/main/resources/" 
		" -jar target/nwbqueryengine-1.0-SNAPSHOT-jar-with-dependencies.jar ")
index_file_name = "nwb_index.db"
cwd = os.getcwd()  # current working directory


# Queries currently in paper:
# A) epochs:(start_time>200  &  stop_time<400  |  stop_time>1600)
# B) */data:  (unit  ==  "unknown")
# C)/general/subject: (subject_id == "anm00210863") & */epochs/*: (start_time > 500 & start_time < 550 &tags LIKE "%LickEarly%")
# D)units: (id > -1 & location == "CA3" & quality > 0.8)
# E)/general:(virusLIKE "%infectionLocation: M2%")

default_queries = """
# A
epochs*:(start_time>200 & stop_time<400 | stop_time>1600)
# B
*/data: (unit == "unknown")
# C
general/subject: (subject_id == "anm00210863") & epochs/*: (start_time > 500 & start_time < 550 & tags LIKE "%LickEarly%")
# D
units: (id > -1 & location == "CA3" & quality > 0.8)
# E
general:(virus LIKE "%infectionLocation: M2%")
# F
general/optophysiology/*: (excitation_lambda)
"""

default_queries = """
# A
general/subject: (subject_id == "anm00210863") & epochs/*: (start_time > 500 & start_time < 550 & tags LIKE "%LickEarly%")
# B
units: (id > -1 & location == "CA3" & quality > 0.8)
# C
general:(virus LIKE "%infectionLocation: M2%")
# D
general/optophysiology/*: (excitation_lambda)
"""

# G
# Don't include this because there are so many groups found in the Churchland dataset
# *:(neurodata_type == "RoiResponseSeries")

tools_cmd = None
tools = None
def make_tools_cmd(data_dir, index_file_path, java_tool_dir, java_cmd):
	# creates list of tools and info about tools (command line and directory for running the tool)
	global java_cmd_prefix, tools_cmd, tools
	tools_cmd = []
#	tools_cmd.append({"name": "search_nwb", "cmd": "python -m nwbindexer.search_nwb " + data_dir})
	if java_tool_dir is not None:
		tools_cmd.append({"name": "java", "cmd": java_cmd_prefix + data_dir, "dir": java_tool_dir})
#	tools_cmd.append({"name": "query_index", "cmd": "python -m nwbindexer.query_index " + index_file_path })
	tools_cmd.append({"name": "search_nwb", "cmd": "python -m nwbindexer.search_nwb " + data_dir})
	tools_cmd.append({"name": "query_index", "cmd": "python -m nwbindexer.query_index " + index_file_path })
    # tools has list of tool names
	tools = [tools_cmd[i]["name"] for i in range(len(tools_cmd))]


def run_query(query, run_number, order):
	# run query on all three tools, returns times as a triple (one for each tool)
	# order is a string of digits indicating the order to run the queries
	global tools_cmd, cwd
	# list to store execution times
	times = [None, None, None]
	# convert order to list of ints
	order = list(map(int, list(order)))
	for tool_num in order:
		tool_info = tools_cmd[tool_num]
		tool = tool_info["name"]
		cmd = tool_info["cmd"] + " '" + query + "'"
		if "dir" in tool_info and tool_info["dir"] is not None:
			os.chdir(tool_info["dir"])
		print("** Starting run %s, %s with: %s" % (run_number, tool, query,) )
		print("dir:%s" % os.getcwd())
		print("cmd:%s" % cmd)
		who= resource.RUSAGE_CHILDREN
		resource_before = resource.getrusage(who)
		p = subprocess.run(cmd, shell=True, capture_output=True)
		resource_after = resource.getrusage(who)
		time_user = resource_after[0] - resource_before[0]
		time_sys = resource_after[1] - resource_before[1]
		time_total = time_user + time_sys
		# stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		output_lines = p.stdout.decode("utf-8").split(sep='\n')
		print("\n".join(output_lines))  # ls output
		error_output = p.stderr # .decode("utf-8")
		if len(error_output) > 0:
			print ("Found error:")
			print(error_output)
			sys.exit("aborting.")
		print("Time, user={:.4f}, sys={:.4f}, total={:.4f}".format(time_user, time_sys, time_total))
		times[tool_num] = time_total
	# change back to original directory in case directory changed
	os.chdir(cwd)
	return times

alpha = "ABCDEFGHIJKLMNOP"

def run_default_queries(run_number, order):
	# run default queries once, in the order specified.  Order is a string of digits.
	global default_queries, tools, query_display, alpha
	results = []
	results.append(tools)  # heading of output table
	queries = []  # for storing actual queries (without blank lines or comments)
	for line in default_queries.split("\n"):
		if line == "" or line[0] == "#":
			# skip blanks lines or comments
			print(line)
			continue
		query_code = alpha[len(queries)]
		print("\n------- query %s -------\n%s" % (query_code, line))
		query = line
		queries.append(query)
		times = run_query(query, run_number, order)
		results.append(times)
	# display final timing results
	return [results, queries]

def run_default_queries_repetitions(num_runs):
	# run the default queries num_runs times, average the results
	global alpha
	rep_results = []
	# order specifies the order each query is executed, done to have different orders in case that matters
	# for the timeing due to caches
	orders = ["012", "021", "102", "120", "201", "210"]
	for run_number in range(num_runs):
		order = orders[ run_number % len(orders) ]
		results, queries = run_default_queries(run_number, order)
		rep_results.append(results)
	# display results
	print("Queries in test:")
	for i in range(len(queries)):
		print("%s. %s" % (alpha[i], queries[i]))
	print("timing results are:")
	pp.pprint(rep_results)

# def display_
# 	print("\t".join(["qid",] + results[0]))
# 	for i in range(1,len(results)):
# 		print("{}\t{:.4f}\t{:.4f}\t{:.4f}".format(alpha[i-1], results[i][0], results[i][1], results[i][2]))



def run_single_query(query):
	global tools
	times = run_query(query)
	print("\t".join(tools) + "\n" + "\t".join( [ "{:.4g}".format(x) for x in times]))

def do_interactive_queries():
	print("Enter query, control-d to quit")
	while True:
		try:
			query=input("> ")
		except EOFError:
			break;
		run_single_query(query)
	print("\nDone running all queries")


def display_instructions():
	global default_java_tool_dir, default_data_dir, index_file_name
	print("Usage: %s ( i | <ndq> | <query> ) [ <data_dir> [ <java_tool_dir> ] ]" % sys.argv[0])
	print(" First parameter required, either:")
	print("    'i' - interactive mode (user enters queries interactively).")
	print("    <ndq> - an integer, number of times to run default queries.  Times for runs are averaged.")
	print("    <query> - a single query to execute; must be quoted.")
	print(" After the first parameter, optionally specify:")
	print("    <data_dir> - directory containing NWB files AND index file ('%s' built by build_index.py)" % index_file_name)
	print("    <java_tool_dir> - directory containing NWB Query Engine (Java tool)")
	print("    If <data_dir> not specified, uses: %s" % default_data_dir)
	print("    If <java_tool_dir> not specified, uses: %s" % default_java_tool_dir)
	sys.exit("")


def main():
	global default_java_tool_dir, default_data_dir, index_file_name
	arglen = len(sys.argv)
	if arglen < 2 or arglen > 4:
		display_instructions()
	java_tool_dir = os.path.abspath( argv[3] if arglen == 4 else default_java_tool_dir )
	data_dir = os.path.abspath( sys.argv[2] if arglen > 2 else default_data_dir )
	if not os.path.isdir(data_dir):
		print("ERROR: Data directory not found: '%s'" % data_dir)
		sys.exit("Aborting.")
	index_file_path = os.path.join(data_dir, index_file_name)
	if not os.path.isfile(index_file_path):
		print("ERROR: Index file not found: '%s'; perhaps need to build it using build_index.py." % index_file_path)
		sys.exit("Aborting.")
	if not os.path.isdir(java_tool_dir):
		print("WARNING: Could not find java_tool_directory: %s" % java_tool_directory)
		print("Not running Java tool queries")
		java_cmd = None
	else:
		java_cmd = java_cmd_prefix + data_dir
	make_tools_cmd(data_dir, index_file_path, java_tool_dir, java_cmd)
	if sys.argv[1] == "i":
		do_interactive_queries()
	elif sys.argv[1].isdigit():
		num_runs = int(sys.argv[1])
		run_default_queries_repetitions(num_runs)
	elif sys.argv[1][0] not in ('"', "'"):
		display_instructions()
	else:
		query = sys.argv[1]
		run_single_query(query)


if __name__ == "__main__":
	main()

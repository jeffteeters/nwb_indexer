
# script to test speed of queries

import os
import sys
import subprocess
# import re
import readline
import resource

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
# G
# Don't include this because there are so many groups found in the Churchland dataset
# *:(neurodata_type == "RoiResponseSeries")
"""

# tools = ["java", "search_nwb", "query_index"]
# tool_info = {"java": {"cmd": java_cmd, "dir": java_tool_dir},
# 	"search_nwb": {"cmd": "python -m nwbindexer.search_nwb " + data_dir, "dir": python_tools_dir},
# 	"query_index": {"cmd": "python -m nwbindexer.query_index -", "dir": python_tools_dir}
# }

tools_cmd = None
tools = None
def make_tools_cmd(data_dir, index_file_path, java_tool_dir, java_cmd):
	# creates list of tools and info about tools (command line and directory for running the tool)
	global java_cmd_prefix, tools_cmd, tools
	tools_cmd = []
	if java_tool_dir is not None:
		tools_cmd.append({"name": "java", "cmd": java_cmd_prefix + data_dir, "dir": java_tool_dir})
	tools_cmd.append({"name": "search_nwb", "cmd": "python -m nwbindexer.search_nwb " + data_dir})
	tools_cmd.append({"name": "query_index", "cmd": "python -m nwbindexer.query_index " + index_file_path })
    # tools has list of tool names
	tools = [tools_cmd[i]["name"] for i in range(len(tools_cmd))]


def run_query(query):
	# run query on all three tools, returns times as a triple (one for each tool)
	global tools_cmd, cwd
	times = []
	for tool_info in tools_cmd:
		tool = tool_info["name"]
		cmd = tool_info["cmd"] + " '" + query + "'"
		if "dir" in tool_info and tool_info["dir"] is not None:
			os.chdir(tool_info["dir"])
		print("Starting: ** %s ** with: %s" % (tool, query,) )
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
		times.append(time_total)
	# change back to original directory in case directory changed
	os.chdir(cwd)
	return times

def run_default_queries():
	global default_queries, tools
	results = []
	results.append(tools)  # heading of output table
	queries = []  # for storing actual queries (without blank lines or comments)
	alpha = "ABCDEFGHIJKLMNOP"
	for line in default_queries.split("\n"):
		if line == "" or line[0] == "#":
			# skip blanks lines or comments
			print(line)
			continue
		query_code = alpha[len(queries)]
		print("\n------- query %s -------\n%s" % (query_code, line))
		query = line
		queries.append(query)
		times = run_query(query)
		results.append(times)
	# display final timing results
	print("Queries in test:")
	for i in range(len(queries)):
		print("%s. %s" % (alpha[i], queries[i]))
	print("timing results are:")
	print("\t".join(["qid",] + results[0]))
	for i in range(1,len(results)):
		print("{}\t{:.4f}\t{:.4f}\t{:.4f}".format(alpha[i-1], results[i][0], results[i][1], results[i][2]))

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
	print("Usage: %s ( i | - | <query> ) [ <data_dir> [ <java_tool_dir> ] ]" % sys.argv[0])
	print(" First parameter required:")
	print("    Either one characer: 'i' - interactive mode, '-' use stored default queries")
	print("    *OR* a single query to execute; must be quoted.")
	print(" After the first parameter, optionally specify:")
	print("    <data_dir> - directory containing nwb files AND index file ('%s' built by build_index.py)" % index_file_name)
	print("    <java_tool_dir> - directory containing NWB Query Engine (java tool)")
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
	elif sys.argv[1] == "-":
		run_default_queries()
	elif sys.argv[1][0] not in ('"', "'"):
		display_instructions()
	else:
		query = sys.argv[1]
		run_single_query(query)


if __name__ == "__main__":
	main()

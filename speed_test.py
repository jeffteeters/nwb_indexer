
# script to test speed of queries

import os
import sys
import subprocess
# import re
import readline
import resource


java_tool_dir = "/Users/jt/crcns/projects/petr_nwbqe_paper/NwbQueryEngine4"
python_tools_dir = os.getcwd()
data_dir = "../sample_data"
java_cmd=("java -Djava.library.path=src/main/resources/" 
		" -jar target/nwbqueryengine-1.0-SNAPSHOT-jar-with-dependencies.jar " + data_dir)


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

tools = ["java", "search_nwb", "query_index"]
tool_info = {"java": {"cmd": java_cmd, "dir": java_tool_dir},
	"search_nwb": {"cmd": "python search_nwb.py " + data_dir, "dir": python_tools_dir},
	"query_index": {"cmd": "python query_index.py -", "dir": python_tools_dir}
}

def run_query(query):
	# run query on all three tools, returns times as a triple (one for each tool)
	global tools, tool_info
	times = []
	for tool in tools:
		cmd = tool_info[tool]["cmd"] + " '" + query + "'"
		tdir = tool_info[tool]["dir"]
		os.chdir(tdir)
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
	return times

def run_default_queries():
	global default_queries
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
	print("Usage: %s ( i | - | <query> )" % sys.argv[0])
	print(" Either one characer: 'i' - interactive mode, '-' use stored default queries")
	print(" *OR* a single query to execute; must be quoted.")
	sys.exit("")


def main():
	arglen = len(sys.argv)
	if arglen != 2:
		display_instructions()
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

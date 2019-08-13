
# script to test speed of queries

import os
import sys
import subprocess
import re
import readline

java_tool_dir = "/Users/jt/crcns/projects/petr_nwbqe_paper/NwbQueryEngine2"
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
/*data: (unit == "unknown")
# C
# following does not work in NWB Query Engine, the '*' in /epochs causes a problem
#/general/subject: (subject_id == "anm00210863") & /epochs/*: (start_time > 500 & start_time < 550 & tags LIKE "%LickEarly%")
# simplified version of the above to work in NWB Query engine
/general/subject: (subject_id == "anm00210863") & epochs*: (start_time > 500 & start_time < 550 & tags LIKE "%LickEarly%")
# Will this be the same, with slash before /epochs*
/general/subject: (subject_id == "anm00210863") & /epochs*: (start_time > 500 & start_time < 550 & tags LIKE "%LickEarly%")
# D
/general:(virus LIKE "%infectionLocation: M2%")
# E
*:(neurodata_type == "RoiResponseSeries")
"""

tools = ["java", "search_nwb", "query_index"]
tool_info = {"java": {"cmd": java_cmd, "dir": java_tool_dir},
	"search_nwb": {"cmd": "python search_nwb.py " + data_dir, "dir": python_tools_dir},
	"query_index": {"cmd": "python query_index.py -", "dir": python_tools_dir}
}

def run_query(query):
	# run query on all three tools, returns times as a triple (one for each tool)
	global tools, tool_info
	time_pattern = b"\nreal\t(\d+)m(\d+\.\d+)s\nuser\t(\d+)m(\d+\.\d+)s\nsys\t(\d+)m(\d+\.\d+)s\n"
	times = []
	for tool in tools:
		cmd = tool_info[tool]["cmd"] + " '" + query + "'"
		tdir = tool_info[tool]["dir"]
		os.chdir(tdir)
		print("Starting: ** %s ** with: %s" % (tool, query,) )
		print("dir:%s" % os.getcwd())
		print("cmd:%s" % cmd)
		p = subprocess.run("time " + cmd, shell=True, capture_output=True)
		# stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		output_lines = p.stdout.decode("utf-8").split(sep='\n')
		print("\n".join(output_lines))  # ls output
		time_output = p.stderr # .decode("utf-8")
		m = re.fullmatch(time_pattern, time_output)
		if not m:
			print("time_output did not match pattern:")
			print(time_output)
			print(time_pattern)
			sys.exit("quitting")
		time_user = int(m.group(3)) * 60.0 + float(m.group(4))
		time_sys = int(m.group(5)) * 60.0 + float(m.group(6))
		total_time = time_user + time_sys
		print (time_output)
		print("total time is: %gs" % total_time)
		times.append(total_time)
	return times

def run_default_queries():
	global query_lines
	results = []
	results.append(tools)  # heading of output table
	queries = []  # for storing actual queries (without blank lines or comments)
	alpha = "ABCDEFGHIJKLMNOP"
	for line in query_lines.split("\n"):
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
		print("%s\t%g\t%g\t%g" % (alpha[i-1], results[i][0], results[i][1], results[i][2]))


# def test_speed_old():
# 	global tools, tool_info, query_lines
# 	results = []
# 	results.append(tools)  # heading of output table
# 	time_pattern = b"\nreal\t(\d+)m(\d+\.\d+)s\nuser\t(\d+)m(\d+\.\d+)s\nsys\t(\d+)m(\d+\.\d+)s\n"
# 	queries = []  # for storing actual queries (without blank lines or comments)
# 	alpha = "ABCDEFGHIJKLMNOP"
# 	for line in query_lines.split("\n"):
# 		if line == "" or line[0] == "#":
# 			# skip blanks lines or comments
# 			print(line)
# 			continue
# 		query_code = alpha[len(queries)]
# 		print("\n------- query %s -------\n%s" % (alpha[len(queries)], line))
# 		query = line
# 		queries.append(query)
# 		times = []
# 		for tool in tools:
# 			cmd = tool_info[tool]["cmd"] + " '" + query + "'"
# 			tdir = tool_info[tool]["dir"]
# 			os.chdir(tdir)
# 			print("Starting: ** %s ** with %s) %s" % (tool, query,) )
# 			print("dir:%s" % os.getcwd())
# 			print("cmd:%s" % cmd)
# 			p = subprocess.run("time " + cmd, shell=True, capture_output=True)
# 			# stdout=subprocess.PIPE, stderr=subprocess.PIPE)
# 			output_lines = p.stdout.decode("utf-8").split(sep='\n')
# 			print("\n".join(output_lines))  # ls output
# 			time_output = p.stderr # .decode("utf-8")
# 			m = re.fullmatch(time_pattern, time_output)
# 			if not m:
# 				print("time_output did not match pattern:")
# 				print(time_output)
# 				print(time_pattern)
# 				sys.exit("quitting")
# 			time_user = int(m.group(3)) * 60.0 + float(m.group(4))
# 			time_sys = int(m.group(5)) * 60.0 + float(m.group(6))
# 			total_time = time_user + time_sys
# 			print (time_output)
# 			print("total time is: %gs" % total_time)
# 			times.append(total_time)
# 		results.append(times)
# 	# display final timing results
# 	print("Queries in test:")
# 	for i in range(len(queries)):
# 		print("%s. %s" % (alpha[i], queries[i]))
# 	print("timing results are:")
# 	print("\t".join(["qid",] + results[0]))
# 	for i in range(1,len(results)):
# 		print("%s\t%g\t%g\t%g" % (alpha[i-1], results[i][0], results[i][1], results[i][2]))


			# print(time_output)


# time $java_cmd "/general:(virus LIKE \"%infectionLocation: M2%\")" > /dev/null


#while read -r line; do
#    echo "Running: $line"
#    result=`time $java_cmd $line`
#    echo $result
#done <<< "$queries"

def run_single_query(query):
	global tools
	times = run_query(query)
	print("\t".join(tools) + "\n" + "\t".join(map(str, times)))

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
	elif sys.argv[1] == "=":
		run_default_queries()
	elif sys.argv[1][0] not in ('"', "'"):
		display_instructions()
	query = sys.argv[1]
	run_single_query(query)


if __name__ == "__main__":
	main()

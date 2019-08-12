
# script to test speed of queries

import os
import sys
import subprocess
import re

java_tool_dir = "/Users/jt/crcns/projects/petr_nwbqe_paper/NwbQueryEngine2"
python_tools_dir = os.getcwd()
data_dir = "../sample_data"
java_cmd=("java -Djava.library.path=src/main/resources/" 
		" -jar target/nwbqueryengine-1.0-SNAPSHOT-jar-with-dependencies.jar " + data_dir)

query_lines = """
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

def test_speed():
	global tools, tool_info, query_lines
	results = []
	results.append(tools)  # heading of output table
	time_pattern = b"\nreal\t(\d+)m(\d+\.\d+)s\nuser\t(\d+)m(\d+\.\d+)s\nsys\t(\d+)m(\d+\.\d+)s\n"
	queries = []  # for storing actual queries (without blank lines or comments)
	alpha = "ABCDEFGHIJKLMNOP"
	for line in query_lines.split("\n"):
		if line == "" or line[0] == "#":
			# skip blanks lines or comments
			print(line)
			continue
		print("\n------- query %s -------\n%s" % (alpha[len(queries)], line))
		query = line
		queries.append(query)
		times = []
		for tool in tools:
			cmd = tool_info[tool]["cmd"] + " '" + query + "'"
			tdir = tool_info[tool]["dir"]
			os.chdir(tdir)
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
		results.append(times)
	# display final timing results
	print("Queries in test:")
	for i in range(len(queries)):
		print("%s. %s" % (alpha[i], queries[i]))
	print("timing results are:")
	print("\t".join(["qid",] + results[0]))
	for i in range(1,len(results)):
		print("%s\t%g\t%g\t%g" % (alpha[i-1], results[i][0], results[i][1], results[i][2]))


			# print(time_output)


# time $java_cmd "/general:(virus LIKE \"%infectionLocation: M2%\")" > /dev/null


#while read -r line; do
#    echo "Running: $line"
#    result=`time $java_cmd $line`
#    echo $result
#done <<< "$queries"


def main():
	test_speed()

if __name__ == "__main__":
	main()

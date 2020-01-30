
# script to test speed of queries

import os
import sys
import subprocess
# import re
import readline
import resource
import copy

# for generating plot of timing results
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

import pprint
pp = pprint.PrettyPrinter(indent=4)

# python_tools_dir = os.getcwd()  # assumes this is running in same directory contaiing this file (speed_check.py)


# default values for command-line arguments
default_java_tool_dir = "/Users/jt/crcns/projects/petr_nwbqe_paper/NwbQueryEngine5"
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

default_queries = """
# A
epochs*:(start_time>200 & stop_time<250 | stop_time>4850)
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
		tools_cmd.append({"name": "NWB Query Engine", "cmd": java_cmd_prefix + data_dir, "dir": java_tool_dir})
#	tools_cmd.append({"name": "query_index", "cmd": "python -m nwbindexer.query_index " + index_file_path })
	tools_cmd.append({"name": "search_nwb", "cmd": "python -m nwbindexer.search_nwb " + data_dir})
	tools_cmd.append({"name": "query_index", "cmd": "python -m nwbindexer.query_index " + index_file_path })
	# tools has list of tool names
	tools = [tools_cmd[i]["name"] for i in range(len(tools_cmd))]


def run_query(query, run_number=1, order="012"):
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
		print("\n** Starting run %s, %s with: %s" % (run_number, tool, query,) )
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
	graph_rep_results(rep_results)

def graph_rep_results(rep_results):
	# calculate average results, also save min and max
	num_runs = len(rep_results)
	num_queries = len(rep_results[0]) - 1  # minus 1 for tool names
	tool_names = rep_results[0][0]
	num_tools = len(tool_names)
	assert num_tools == 3
	# build structure like:
	# [ { "tool_name": <tool_name>, "query_times" <query_times> } ]
	# where:
	# <tool_name> - string, name of the tool,
	# <query_times> = [  (Q1_ave, Q1_min, Q1_max), (Q2_ave, Q2_min, Q2_max), ... ]
	tool_times = []
	for tool_index in range(num_tools):
		tool_name = tool_names[tool_index]
		query_times = []
		for query_index in range(num_queries):
			time_sum = rep_results[0][query_index + 1][tool_index]
			time_min = time_sum
			time_max = time_sum
			for run_index in range(1, num_runs):
				val = rep_results[run_index][query_index + 1][tool_index]
				time_sum += val
				if val < time_min:
					time_min = val
				if val > time_max:
					time_max = val
			avg_min_max = ( time_sum / float(num_runs), time_min, time_max)
			query_times.append(avg_min_max)
		tool_times.append({ "tool_name": tool_name, "query_times": query_times})
	plot_tool_times(tool_times)
	return
	# old plotting code below


	ave_results = copy.deepcopy(rep_results[0])
	num_queries = len(ave_results)


	for run_index in range(1, num_reps):
		for query_index in range(1, num_queries):
			for tool_index in range(num_tools):
				ave_results[query_index][tool_index] += rep_results[run_index][query_index][tool_index]
	# divide by number of runs to get average
	for query_index in range(1, num_queries):
			for tool_index in range(num_tools):
				ave_results[query_index][tool_index] /= num_reps
	print("average results are:")
	pp.pprint(ave_results)
	make_plot(ave_results)
	# compute average time per tool
	## plan to remove following code
	# total_time_per_tool = [0.0, 0.0, 0.0]
	# for tool_index in range(num_tools):
	# 	for query_index in range(1, num_queries):
	# 		total_time_per_tool[tool_index] += ave_results[query_index][tool_index]
	# ave_time_per_tool = [total_time_per_tool[i] / float(num_queries) for i in range(num_tools)]
	# tool_names = ave_results[0]
	# print("average time per tool:")
	# pp.pprint(tool_names)
	# pp.pprint(ave_time_per_tool)
	# plot_ave_time_per_tool(tool_names, ave_time_per_tool)


def plot_tool_times(tool_times):
	# tool_times is a structure like:
	# [ { "tool_name": <tool_name>, "query_times" <query_times> } ]
	# where:
	# <tool_name> - string, name of the tool,
	# <query_times> = [  (Q1_ave, Q1_min, Q1_max), (Q2_ave, Q2_min, Q2_max), ... ]
	num_queries = len(tool_times[0]["query_times"])
	tool_names = [x["tool_name"] for x in tool_times]
	num_tools = len(tool_names)
	query_names = ["Q%s" % (i + 1) for i in range(num_queries)]

	x = np.arange(len(query_names))*1.25  # the label locations
	width = 0.35  # the width of the bars
	all_bars_width = width * float(num_tools)
	fig, ax = plt.subplots()
	# rects = []
	for tool_index in range(num_tools):
		query_times = tool_times[tool_index]["query_times"]
		offset = (width * tool_index) - (all_bars_width / 2.0) + (width / 2.0)
		time_ave = [query_times[i][0] for i in range(len(query_times))]
		time_min = [query_times[i][1] for i in range(len(query_times))]
		time_max = [query_times[i][2] for i in range(len(query_times))]
		down_error = [time_ave[i] - time_min[i] for i in range(len(time_ave))]
		up_error = [time_max[i] - time_ave[i] for i in range(len(time_ave))]
		print("tool: %s" % tool_names[tool_index])
		print("time_ave: %s" % time_ave)
		print("time_min: %s" % time_min)
		print("time_max: %s" % time_max)
		# print("tool_index=%s, offset=%s, all_bars_width=%s" % (tool_index, offset, all_bars_width))
		rects = ax.bar(x + offset, time_ave, width, label=tool_names[tool_index], yerr=[down_error, up_error])
		autolabel2(rects, ax, time_max)

	# Add some text for labels, title and custom x-axis tick labels, etc.
	ax.set_ylabel('Query times (sec)')
	ax.set_title('Times by query and tool')
	ax.set_xticks(x)
	ax.set_xticklabels(query_names)
	ax.legend()
	plt.yscale("log")
	# from matplotlib.ticker import ScalarFormatter
	from matplotlib.ticker import FormatStrFormatter
	# ax.yaxis.set_major_formatter(ScalarFormatter())
	# from https://stackoverflow.com/questions/13511612/format-truncated-python-float-as-int-in-string
	plt.tick_params(axis='y', which='minor')
	ax.set_yticks([0.5, 1, 2.5, 5, 10, 20, 40, 80])
	ax.yaxis.set_major_formatter(FormatStrFormatter("%01g"))
	# ax.yaxis.set_minor_formatter(FormatStrFormatter("%01d"))
	# plt.ticklabel_format(style='plain', axis='y')
	# ax.ticklabel_format(useOffset=False, style='plain')
	# ax.ticklabel_format(style='plain')
	# import matplotlib.ticker as mticker
	# ax.yaxis.set_major_formatter(mticker.ScalarFormatter())
	# ax.yaxis.get_major_formatter().set_scientific(False)
	# ax.yaxis.get_major_formatter().set_useOffset(False)


	fig.tight_layout()
	plt.savefig('time_per_query_and_tool_test.pdf')
	plt.show()




# def plot_ave_time_per_tool(tool_names, ave_time_per_tool):
# 	# generate plot of average query time per tool
# 	num_tools = len(tool_names)
# 	x = np.arange(num_tools)  # the label locations
# 	width = 0.75  # the width of the bars
# 	fig, ax = plt.subplots()
# 	rects = ax.bar(x - width/2, ave_time_per_tool, width, label=tool_names)
# 	autolabel(rects, ax)

# 	# Add some text for labels, title and custom x-axis tick labels, etc.
# 	ax.set_ylabel('Average query time (sec)')
# 	ax.set_title('Average time per tool')
# 	ax.set_xticks(x)
# 	ax.set_xticklabels(tool_names)
# 	ax.legend()
# 	plt.yscale("log")

# 	fig.tight_layout()
# 	plt.savefig('average_time_per_tool.pdf')
# 	plt.show()

# def test_plot_ave_time_per_tool():
# 	tool_names = ["NWB Query Engine", "search_nwb", "query_index"]
# 	ave_time_per_tool = [14.376904666666668, 22.825276666666664, 0.5911126666666675]
# 	plot_ave_time_per_tool(tool_names, ave_time_per_tool)

def test_plotting():
	test_results = [   ['NWB Query Engine', 'search_nwb', 'query_index'],
	[14.376904666666668, 22.825276666666664, 0.5911126666666675],
	[2.0265133333333387, 0.43731499999999723, 0.4694036666666636],
	[1.6206033333333316, 0.4567080000000023, 0.41073933333333706],
	[1.5515750000000024, 0.5179549999999987, 0.44407033333332874]]
	variance = [
	[ 2.0, 4.0, .1],
	[.2, .04, .05],
	[.1,.06, .04],
	[.1, .05, .04]
	]
	print("test results are:")
	pp.pprint(test_results)
	make_plot(test_results, variance)

def test_plotting2():
	rep_results = [   [   ['NWB Query Engine', 'search_nwb', 'query_index'],
		[17.121465, 25.931048000000004, 0.8929710000000002],
		[53.274452999999994, 81.793924, 1.1305179999999986],
		[19.372635000000002, 30.672892999999988, 0.6211500000000179],
		[2.5219609999999903, 0.5723900000000022, 0.5536539999999874],
		[2.13974300000001, 0.8018010000000011, 0.5394149999999911],
	[2.0108150000000116, 0.9465439999999958, 0.6255980000000108]],
	[   ['NWB Query Engine', 'search_nwb', 'query_index'],
	[16.60134299999999, 25.143021000000008, 0.9168309999999842],
		[54.142889, 78.28330000000005, 1.1646689999999822],
		[16.813823999999954, 29.68915600000002, 0.6607349999999883],
		[2.43924599999999, 0.6162909999999826, 0.5709880000000425],
		[2.109916999999996, 0.628770999999972, 0.5487640000000127],
		[2.019654000000024, 0.7447540000000146, 0.612367999999968]],
	[   ['NWB Query Engine', 'search_nwb', 'query_index'],
		[16.385359999999977, 25.34464100000003, 0.7689310000000233],
		[56.70292999999991, 80.53669400000004, 1.217979000000014],
		[17.646947000000026, 28.355358000000024, 0.5822899999999294],
		[2.383011000000039, 0.534860000000009, 0.530239000000023],
		[2.0600289999999717, 0.5480499999999608, 0.519582000000014],
		[1.7707240000000013, 0.6844410000000778, 0.5066459999999324]]]
	graph_rep_results(rep_results)


def make_plot(ave_results, variance=None):
	# generate plot of average results
	num_queries = len(ave_results) - 1
	tool_names = ave_results[0]
	num_tools = len(tool_names)
	query_names = ["Q%s" % (i + 1) for i in range(num_queries)]
	# convert from structure with each row containing times for one query, across all tools, e.g.:
	# [   ['java', 'search_nwb', 'query_index'],
	# [14.376904666666668, 22.825276666666664, 0.5911126666666675],
	# [2.0265133333333387, 0.43731499999999723, 0.4694036666666636],
	# [1.6206033333333316, 0.4567080000000023, 0.41073933333333706],
	# [1.5515750000000024, 0.5179549999999987, 0.44407033333332874]]
	# to structure with each row containing times for one tool, across all queries.  (what were columns in above)
	tool_times = []
	for tool_index in range(num_tools):
		t_times = []
		for query_index in range(num_queries):
			t_times.append(ave_results[query_index+1][tool_index])
		tool_times.append(t_times)
	# print("after reshaping:")
	# pp.pprint(tool_times)
	x = np.arange(len(query_names))*1.25  # the label locations
	width = 0.35  # the width of the bars
	all_bars_width = width * float(num_tools)
	fig, ax = plt.subplots()
	# rects = []
	variance = [2.0, 0.2, 0.1, 0.11]
	for tool_index in range(num_tools):
		offset = (width * tool_index) - (all_bars_width / 2.0) + (width / 2.0)
		# print("tool_index=%s, offset=%s, all_bars_width=%s" % (tool_index, offset, all_bars_width))
		rects = ax.bar(x + offset, tool_times[tool_index], width, label=tool_names[tool_index], yerr=variance)
		autolabel(rects, ax)

	# Add some text for labels, title and custom x-axis tick labels, etc.
	ax.set_ylabel('Query times (sec)')
	ax.set_title('Times by query and tool')
	ax.set_xticks(x)
	ax.set_xticklabels(query_names)
	ax.legend()
	plt.yscale("log")
	# from matplotlib.ticker import ScalarFormatter
	from matplotlib.ticker import FormatStrFormatter
	# ax.yaxis.set_major_formatter(ScalarFormatter())
	# from https://stackoverflow.com/questions/13511612/format-truncated-python-float-as-int-in-string
	plt.tick_params(axis='y', which='minor')
	ax.set_yticks([0.5, 1, 2.5, 5, 10, 20, 40, 80])
	ax.yaxis.set_major_formatter(FormatStrFormatter("%01g"))
	# ax.yaxis.set_minor_formatter(FormatStrFormatter("%01d"))
	# plt.ticklabel_format(style='plain', axis='y')
	# ax.ticklabel_format(useOffset=False, style='plain')
	# ax.ticklabel_format(style='plain')
	# import matplotlib.ticker as mticker
	# ax.yaxis.set_major_formatter(mticker.ScalarFormatter())
	# ax.yaxis.get_major_formatter().set_scientific(False)
	# ax.yaxis.get_major_formatter().set_useOffset(False)


	fig.tight_layout()
	plt.savefig('time_per_query_and_tool_test.pdf')
	plt.show()


def autolabel2(rects, ax, time_max):
	"""Attach a text label above each bar in *rects*, displaying its height.
	Get height from time_max so text is above error bar"""
	for rect_index in range(len(rects)):
		rect = rects[rect_index]
		height = time_max[rect_index]
		sigdig = 1 if height > 10 else 2
		ax.annotate('{}'.format(round(height,sigdig)),
					xy=(rect.get_x() + rect.get_width() / 2, height),
					xytext=(0, 3),  # 3 points vertical offset
					textcoords="offset points",
					ha='center', va='bottom')

def autolabel(rects, ax):
	"""Attach a text label above each bar in *rects*, displaying its height."""
	for rect in rects:
		height = rect.get_height()
		sigdig = 1 if height > 10 else 2
		ax.annotate('{}'.format(round(height,sigdig)),
					xy=(rect.get_x() + rect.get_width() / 2, height),
					xytext=(0, 3),  # 3 points vertical offset
					textcoords="offset points",
					ha='center', va='bottom')

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
	test_plotting2()
	# test_plot_ave_time_per_tool()
	# main()

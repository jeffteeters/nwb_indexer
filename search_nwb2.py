import sys
import os
import h5py
import numpy as np
import parse2
import pprint
import readline

pp = pprint.PrettyPrinter(indent=4)

sample_file = "../pynwb_examples/tutorials_python/general/basic_example.nwb"


def make_equery(ti, made_by_index):
	# Create query string that will be run by "eval"
	# replace each cloc by "x[i]" where i = 0, 1, 2, ...
	# but don't include those that appear before a comma
	# made_by_index contains list of cloc names, which has values made by an index
	# These must be searched using the "in" operator.  This is done by patching the expression.
	equery = []
	cloc_count = 0
	cloc_index_locations = []	# list of indices, both in ti['tokens'] and in equery of clocs that are made using 
								# an index.  Used to patch query later
	index_last_comma = 0		# index in equery of last comma, values before that are not included in expression
	i = 0	# for following loop, similar to:  for i in range(len(ti['tokens'])):
	while i < len(ti['tokens']):
		ttype = ti['ttypes'][i]
		token = ti['tokens'][i]
		if ttype == "CLOC":
			ttmp = "x[%i]" % cloc_count
			# check for cloc that has an index.  If found save location for later patching
			if token in made_by_index:
				if i + 3 < len(ti['tokens']) and ti['tokens'][i+1] == "[":
					# found specified subscript, make sure right format
					if ti["ttypes"][i+2] != "NC" or ti['tokens'][i+3] != "]":
						sys.exit("found %s and opening '[', but not constant followed by closing ']'" % token)
					# ttmp ="(" + ttmp + ")[%s]" % ti['tokens'][i+2]  # add in constant specifier
					ttmp +="[%s]" % ti['tokens'][i+2]
					i += 3  # skip next three tokens, e.g. '[' NC ']'
				else:
					# save location and patch later
					cloc_index_locations.append((i, len(equery), token))
			cloc_count += 1
		elif ttype == "COMMA":
			index_last_comma = len(equery)  # save location of comma so can not include prefix in imploded equery
			i += 1
			continue # if comma, don't append anything
		elif ttype == "AOR" and token == "AND":
			ttmp = "and"
		elif ttype == "AOR" and token == "OR":
			ttmp = "or"
		elif ttype == "ROP" and token == "LIKE":
			# replace "LIKE" with "==""
			ttmp = "=="
		else:
			ttmp = ti["tokens"][i]
		equery.append(ttmp)
		i += 1
		# print("token=%s, index_last_comma=%i, equery=%s" % (token, index_last_comma, equery))
	# if any clocs using index found, change query to use 'in' operator.
	# For example, original query: tags LIKE "example"
	# convert to "example in tags"
	for iec in cloc_index_locations:
		i, equery_i, cloc = iec
		if equery_i < index_last_comma:
			# this not used in expression, ignore
			continue
		# safety check
		op = ti["tokens"][i+1]
		if op != "LIKE" and op != "==":
			sys.exit("Found index (%s), with operator not 'LIKE' or '==' (%s), i=%s, index_last_comma=%s." % (
				cloc, op, i, index_last_comma) )
		const_type = ti['ttypes'][i+2]
		if const_type != "SC" and const_type != "NC":
			sys.exit("Found index (%s), with non-constant (%s) as third component." % (cloc, equery[i+2]) )
		# swap order and replace operator with "in"
		tmp = equery[equery_i];
		equery[equery_i] = equery[equery_i+2]
		equery[equery_i+2] = tmp
		equery[equery_i+1] = "in"
	# now implode, but ignore part before comma
	equery = " ".join(equery[index_last_comma:])
	# if equery == "":		# not sure if this is needed
	# 	equery = "True"
	return equery


def make_indexed_lists(tags, tags_index):
	# build tags_lists - list of tags in array by ids
	# tags - list of values, for example, "tags"
	# tags_index - index array, indicates boundary of groupings for tags
	tags_lists = []
	cur_from = 0
	for cur_to in tags_index:
		if cur_to > cur_from:
			tags_lists.append(tags[cur_from:cur_to])
		else:
			tags_lists.append([])
		cur_from = cur_to
	return tags_lists

# from: https://stackoverflow.com/questions/39502461/truly-recursive-tolist-for-numpy-structured-arrays
def array_to_list(array):
    if isinstance(array, np.ndarray):
        return array_to_list(array.tolist())
    elif isinstance(array, list):
        return [array_to_list(item) for item in array]
    elif isinstance(array, tuple):
        return tuple(array_to_list(item) for item in array)
    else:
        return array


def query_nwb2(node, ti, cloc_indices):
	# perform subquery on group that contains nwb2 interval information, that it, has array elements that
	# line up element-wise; e.g. id, start_time, stop_time, tags, tags_index, timeseries, timeseries_index
	# load values from dataset
	# todo: check for datasets that need to be stored as arrays of arrays (has index value)
	cvals = []
	cnames = []
	header = []
	made_by_index = []  # list of clocs made by _index.  Has an array in cvals.
	for cli in cloc_indices:
		cloc = ti["tokens"][cli]
		header.append(cloc)
		cloc_vals = node[cloc].value
		print("cloc=%s, original vals=%s" % (cloc, cloc_vals))
		if isinstance(cloc_vals, np.ndarray):
			cloc_vals = array_to_list(cloc_vals) # convert numpy ndarray to list
		else:
			cloc_vals = [cloc_vals, ]  # convert scalar to list with one element
		# check for _index dataset
		cloc_index = cloc + "_index"
		if cloc_index in node:
			if not isinstance(node[cloc_index], h5py.Dataset):
				sys.exit("Node %s is not a Dataset, should be since has '_index' suffix" % cloc_index);
			index_vals = node[cloc_index].value;
			cloc_vals = make_indexed_lists(cloc_vals, index_vals)
			print("cloc=%s, after indexed vals=%s" % (cloc, cloc_vals))
			made_by_index.append(cloc)  # flag these values made by the index
		cvals.append(cloc_vals)
		cnames.append(cloc)
	equery = make_equery(ti, made_by_index)
	print("Doing nwb2 query, cnames are: %s, values are:" % cnames)
	pp.pprint(cvals)
	print("equery is: %s" % equery)
	zipl = list(zip(*(cvals)))
	print("zipl = %s" % zipl)
	str_filt = "filter( (lambda x: %s), zipl)" % equery
	result = list(eval(str_filt))
	result = { 'header': header, 'result': result}
	return result


def query_normal_group(node, ti, cloc_indices):
	# return ("query_normal_group")
	# see if this works
	return query_nwb2(node, ti, cloc_indices)



def run_subquery(ti, pn):
	global fp
	# pn is ploc number (index to ploc in ti['plocs']).  ploc is 'parent location'
	ploc_info = ti['plocs'][pn]
	ploc = ploc_info[0]
	cloc_indices = ploc_info[1:]
	if not ploc in fp:
		sys.exit("Did not find '%s' in nwb file" % ploc)
	node = fp[ploc]
	if not isinstance(node,h5py.Group):
		sys.exit("Node '%s' is not a group" % ploc)
	# verify all children are in group and they are datasets
	for cli in cloc_indices:
		cloc = ti["tokens"][cli]
		if cloc not in node:
			sys.exit("Did not find '%s' in %s" % (cloc, ploc))
		if not isinstance(node[cloc], h5py.Dataset):
			sys.exit("Node '%s/%s' is not a dataset" % (ploc, cloc))			
	if "neurodata_type" in node.attrs and node.attrs["neurodata_type"] == "TimeIntervals":
		# found nwb2.0 intervals
		sqr = query_nwb2(node, ti, cloc_indices)
	else:
		# found normal group
		sqr = query_normal_group(node, ti, cloc_indices)
	return sqr  # subquery result


	# global pp
	# pp.pprint(ti)

def run_query(ti):
	sq_results = []  # subquery results
	for pn in range(len(ti['plocs'])):
		# sqr = run_subquery(ti, pn)
		sq_results.append(run_subquery(ti, pn))
	print("subquery results are: %s" % sq_results)


def get_and_run_queries():
	print("Enter query, control-d to quit")
	while True:
		try:
			query=input("> ")
		except EOFError:
			break;
		ti = parse.parse(query)
		run_query(ti)
	print("\nDone running all queries")

def main_old():
	global sample_file, fp
	if len(sys.argv) > 2:
		sys.exit('Usage: %s [ <nwb_file> ]' % sys.argv[0])
	if len(sys.argv) == 1:
		nwb_file = sample_file
		print("<nwb_file> not specified; using '%s'" % nwb_file)
	else:
		nwb_file=sys.argv[1]
	if not os.path.isfile(nwb_file):
		sys.exit("ERROR: file '%s' was not found!" % nwb_file)
	fp = h5py.File(nwb_file, "r")
	if not fp:
		sys.exit("Unable to open %s" % path)
	get_and_run_queries()
	# print ("scanning directory %s" % dir)
	# scan_directory(dir)
	con.close()

def make_subquery_call_string(qi):
	# build expression that calls runsubquery for each subquery
	cs_tokens = []
	cpi = 0  # current ploc index
	i = 0
	while i < len(qi['tokens']):
		if cpi >= len(qi['plocs']) or i != qi['plocs'][cpi]["range"][0]:
			# either past the last ploc, or not yet to the start of range of the current ploc
			cs_tokens.append(qi["tokens"][i])
			i += 1
		else:
			# this token is start of expression for subquery, replace by call
			cs_tokens.append("runsubquery(%i,fp,qi,qr)" % cpi)
			i = qi['plocs'][cpi]["range"][1]  # advance to end (skiping all tokens in subquery)
			cpi += 1
	return " ".join(cs_tokens)

def get_search_criteria(cpi, qi):
	# get sc (search_criteria) for finding hdf5 group or dataset to perform search
	# sc = {
	#  start_path - path to starting element to search.  This is specified by parent in query
	#  match_path - regular expression for path that must match parent to do search.  Also
	#               specified by parent in query.  May be different than start_path if 
	#               wildcards are in parent.
	#  search_all - True if searching all children of start_path.  False if searching just within
	#               start_path
	#  children   - list of children (attributes or datasets) that must be present to find a match
	# }
	ploc = qi["plocs"][cpi]["path"]
	idx_first_star = ploc.find("*")
	if idx_first_star > -1:
		# at least one star (wild card)
		start_path = ploc[0:idx_first_star]
		if not start_path:
			start_path = "/"
		search_all = ploc[-1] == "*"   # search all if parent ends with wildcard
		match_path = ploc.replace("*", "*.")  # replace * with *. for RE match later
	else:
		start_path = ploc
		match_path = ploc
		search_all = False
	# make list of children
	children = qi["plocs"][cpi]["display_clocs"].copy()
	for i in qi["plocs"][cpi]["cloc_index"]:
		children.append(qi["tokens"][i])
	sc = {"start_path": start_path, "match_path": match_path,
		"search_all": search_all, "children": children}
	return sc


def runsubquery(cpi, fp, qi, qr):
	# run subquery with current ploc_index cpi, h5py pointer fp, and query information (qi)
	# return results in qr

	def search_node(name, node):
		# search one node, may be group or dataset
		# name is ignored
		# cpi - current ploc index, fp - h5py file pointer
		# qi - query information, qr - container for query results
		# sc search criteria
		# must always return None to allow search (visititems) to continue
		nonlocal sc, cpi, fp, qi, qr
		isGroup = isinstance(node,h5py.Group)
		for child in sc["children"]:
			found_child = child in node.attrs or (
				isGroup and child in node and isinstance(node[child], h5py.Dataset))
			if not found_child:
				return None
		# found all the children, return true and save location in query results (qr)
		qr[cpi].append(node.name)
		return None

	sc = get_search_criteria(cpi, qi)
	print("sc = %s" % sc)
	if sc['start_path'] not in fp:
		# did not even find starting path in hdf5 file, cannot do search
		return False
	start_node = fp[sc['start_path']]
	search_node(None, start_node)
	if sc['search_all'] and isinstance(start_node,h5py.Group):
		start_node.visititems(search_node)
	# qr[cpi] = "cpi=%i, ploc=%s, sc=%s" % (cpi, qi["plocs"][cpi]["path"], sc)
	found = len(qr[cpi]) > 0  # will have content if result found
	return found


def display_result(path, qr):
	print("file %s:" % path)
	pp.pprint(qr)

def query_file(path, qi):
	fp = h5py.File(path, "r")
	if not fp:
		sys.exit("Unable to open %s" % path)
	# for storing query results
	qr = [[] for i in range(len(qi["plocs"]))]
	subquery_call_string = make_subquery_call_string(qi)
	print("%s" % subquery_call_string)
	result = eval(subquery_call_string)
	if result:
	 	display_result(path, qr)

def query_directory(dir, qi):
	# must find files to query.  dir must be a directory
	assert os.path.isdir(dir)
	for root, dirs, files in os.walk(dir):
		for file in files:
			if file.endswith("nwb"):
				path = os.path.join(root, file)
				query_file(path, qi)

def query_file_or_directory(path, qi):
	# run a query on path, query specified in qi (query information, made in parse2.parse)
	if os.path.isfile(path):
		query_file(path, qi)
	else:
		query_directory(path, qi)

def do_interactive_queries(path):
	print("Enter query, control-d to quit")
	while True:
		try:
			query=input("> ")
		except EOFError:
			break;
		qi = parse2.parse(query)
		query_file_or_directory(path, qi)
	print("\nDone running all queries")

def process_command_line(path, query):
	# path is either a directory (search for NWB files) or a NWB file
	# query is None (for interactive input), or a query to process
	if query is None:
		do_interactive_queries(path)
	else:
		qi = parse2.parse(query)
		query_file_or_directory(path, qi)

def main():
	global sample_file
	arglen = len(sys.argv)
	if arglen < 2 or arglen > 3:
		print("Usage: %s <path> [ <query> ]" % sys.argv[0])
		print(" <path> = path to NWB file or directory or '-' for default path")
		print(" <query> = query to execute (optional).  If present, must be quoted.")
		sys.exit("")
	path = sys.argv[1]
	if path == "-":
		path = sample_file
		print("Using default path: '%s'" % path)
	if not os.path.exists(path):
		sys.exit("ERROR: path '%s' was not found!" % path)
	query = sys.argv[2] if arglen == 3 else None
	process_command_line(path, query)

if __name__ == "__main__":
    main()
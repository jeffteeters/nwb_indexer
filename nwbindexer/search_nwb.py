import sys
import os
import h5py
import numpy as np
import pprint
import readline
import re
import nwbindexer.lib.parse as parse
import nwbindexer.lib.results as results

# Tool or searching NWB files, both version 1 and 2.
#
# If reading this code to figure out how it works
# READ FROM THE BOTTOM TO THE TOP, starting with function main.
# The code uses the parser in file parse.py


pp = pprint.PrettyPrinter(indent=4)

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
	elif isinstance(array, bytes):
		# replace bytes by utf string
		return array.decode("utf-8")
	else:
		return array

def convert_to_list(cloc_vals):
	if isinstance(cloc_vals, np.ndarray):
		list_vals = array_to_list(cloc_vals) # convert numpy ndarray to list
	else:
		if isinstance(cloc_vals, bytes):
			# convert bytes to string
			cloc_vals = cloc_vals.decode("utf-8")
		list_vals = [cloc_vals, ]  # convert scalar to list with one element
	return list_vals

def make_subquery_call_string(qi):
	# build expression that calls runsubquery for each subquery
	# Calls are inserted in place of expression in tokens for each parent location
	# If there is no expression, calls are inserted where the expression would be if there was one
	cs_tokens = []   # cs == call string, (e.g. call string tokens)
	ila = 0	# index last added tokan
	for cpi in range(len(qi['plocs'])):
		# add any tokens before the ones in this expression
		while ila < qi['plocs'][cpi]["range"][0]:
			cs_tokens.append(qi["tokens"][ila])
			ila += 1
		# add in call
		cs_tokens.append("runsubquery(%i,fp,qi,qr)" % cpi)
		# skip to end of tokens for this subquery
		ila = qi['plocs'][cpi]["range"][1]
	# add any tokens needed at end of last parent expression
	while ila < len(qi["tokens"]):
		cs_tokens.append(qi["tokens"][ila])
		ila += 1
	return " ".join(cs_tokens)

def get_search_criteria(cpi, qi):
	# get sc (search_criteria) for finding hdf5 group or dataset to perform search
	# sc = {
	#  start_path - path to starting element to search.  This is specified by parent in query
	#  match_path - regular expression for path that must match parent to do search.  Also
	#               specified by parent in query.  May be different than start_path if 
	#               wildcards are in parent.  Is None if search_all is False
	#  search_all - True if searching all children of start_path.  False if searching just within
	#               start_path
	#  children   - list of children (attributes or datasets) that must be present to find a match
	#  editoken   - tokens making up subquery, which will be "edited" to perform query.
	#               Initially is copy of tokens
	# }
	ploc = qi["plocs"][cpi]["path"]
	idx_first_star = ploc.find("*")
	if idx_first_star > -1:
		# at least one star (wild card)
		start_path = ploc[0:idx_first_star]
		if not start_path:
			start_path = "/"
		search_all = True   # search all if wildcard character in parent location
		# force match path to start with slash for matching names of node paths in h5py
		match_path = ploc if ploc[0] == "/" else "/" + ploc
		match_path = match_path.replace("*", ".*")  # replace * with *. for RE match later
	else:
		start_path = ploc
		match_path = None
		search_all = False
	# make list of children
	children = qi["plocs"][cpi]["display_clocs"].copy()
	for i in qi["plocs"][cpi]["cloc_index"]:
		children.append(qi["tokens"][i])
	sc = {"start_path": start_path, "match_path": match_path,
		"search_all": search_all, "children": children}
	return sc

def initialize_editoken(sc, qi):
	# editoken needs to be refreshed for every new node searching
	sc["editoken"] = qi["tokens"].copy()

def make_like_pattern(sql_pattern):
	# convert SQL like pattern (with "%" as wildcard) to regular expression pattern (with ".*" wildcard)
	re_pattern = sql_pattern.replace("%", ".*")
	# re_pattern = re_pattern.strip("\"'")
	return re_pattern

def like(pattern, text):
	# implements LIKE operator.  pattern must be a regular expression, with "%" replaced by .*
	if isinstance(text, bytes):
		text = text.decode("utf-8")
	match = re.fullmatch(pattern, text, flags=re.DOTALL)
	found_match = match is not None
	return found_match

def runsubquery(cpi, fp, qi, qr):
	# run subquery with current ploc_index cpi, h5py pointer fp, and query information (qi)
	# store search results in qr, which is a results.File_result object (see file results.py).
	# return True if search results found, False otherwise

	def search_node(name, node):
		# search one node, may be group or dataset
		# name is ignored
		# cpi - current ploc index, fp - h5py file pointer
		# qi - query information, qr - container for query results
		# sc search criteria
		# must always return None to allow search (visititems) to continue
		nonlocal sc, cpi, fp, qi, qr
		if sc["match_path"] and not re.fullmatch(sc["match_path"], node.name):
			# path does not pattern specified in query
			return None
		ctypes = []  # types of found children
		for child in sc["children"]:
			ctype = get_child_type(node, child)
			if ctype is None:
				# child not found, skip this node
				return None
			ctypes.append(ctype)
		# found all the children, do search for values, store in query results (qre)
		# qre = {"vind": [], "vrow": []}
		initialize_editoken(sc, qi)
		vi_res = results.Vind_result()
		get_individual_values(node, ctypes, vi_res)	# fills vi_res, edits sc["editoken"]
		vtbl_res = results.Vtbl_result()
		found = get_row_values(node, ctypes, vtbl_res)
		if found:
			# found some results, save them
			node_result = results.Node_result(node.name, vi_res, vtbl_res)
			qr.add_node_result(node_result, cpi)
			# qre["node"] = node.name
			# qr[cpi].append(qre)
		return None

	def get_child_type(node, child):
		# return type of child inside of node.
		# Is one of following:
		# None - not present
		# Dictionary, with keys:
		#    type - "attribute" - attribute, or "dataset" - dataset
		#    If type attribute, has key drow == False (since not part of table with rows)
		#    If type dataset, then also has keys:
		#        drow - True if in table with rows (aligned columns), False otherwise
		#        sstype - subscript type.  Either:
		#           None (no subscript),
		#           "compound" (column in compound dataset).
		#           "2d" (column in 2-d dataset.  Index will be an integer, e.g. [1])
		nonlocal sc, cpi, fp, qi, qr
		if child in node.attrs:
			return {"type": "attribute", "drow": False}
		if not isinstance(node,h5py.Group):
			# can't be dataset because parent is not a group
			return None
		if child in node and isinstance(node[child], h5py.Dataset):
			# child is dataset inside a group; check for part of a table (drow = True)
			drow = "colnames" in node.attrs and (child == "id" or 
				child in [s.decode("utf-8").strip() for s in node.attrs["colnames"]])
			sstype = False	# not subscript since full child name found
			return {"type": "dataset", "sstype": None, "drow": drow}
		if child not in qi["plocs"][cpi]["cloc_parts"]:
			# no subscript, child not found
			return None
		# have subscript
		(main, subscript) = qi["plocs"][cpi]["cloc_parts"][child]
		if main in node and isinstance(node[main], h5py.Dataset):
			if len(node[main].shape) == 2:
				# found 2d table
				if subscript.isdigit() and int(subscript) < node[main].shape[1]:
					# found 2d table and index is valid (integer less than number of columns)
					sstype = "2d"
				else:
					# found 2 table, but index is invalid (not integer or greater than number of cols)
					return None
			elif len(node[main].shape) ==1 and subscript in node[main].dtype.names:
				# subscript is a name in a compound type.  e.g.:
				# >>> ts.dtype.names
				# ('idx_start', 'count', 'timeseries')
				sstype = "compound"
			else:
				# subscript not part of this dataset
				return None
			# if made it here, have valid subscript.  Now determine if main is part of table (drow = True)
			drow = "colnames" in node.attrs and (main == "id" or 
				main in [s.decode("utf-8").strip() for s in node.attrs["colnames"]])
			return {"type": "dataset", "sstype": sstype, "drow": drow}

	def get_individual_values(node, ctypes, vi_res):
		# fills vi_res (a results.Vind_result object) with individual results, edits sc["editoken"]
		# finds values of individual variables (not part of table) satisifying search criteria
		# to do that, for each individual variable, evals the binary expression, saving values that
		# result in True.  Edit sc["editoken"] replacing: var op const with True or False in
		# perperation for eval done in get_row_values.
		nonlocal sc, cpi, fp, qi
		for i in range(len(sc["children"])):
			ctype = ctypes[i]
			if ctype["drow"]:
				# skip values part of a table with rows
				continue
			child = sc["children"][i]
			value = load_value(node, child, ctype)
			if i < len(qi["plocs"][cpi]["display_clocs"]): 
				# just displaying these values, not part of expression.  Save it.  (display_clocs are first in children)
				vi_res.add_vind_value(child, value)
			else:
				# child is part of expression.  Need to make string for eval to find values
				# matching criteria, save matching values, and edit sc["editoken"]
				tindx = qi["plocs"][cpi]["cloc_index"][i - len(qi["plocs"][cpi]["display_clocs"])]  # token index
				assert qi["ttypes"][tindx] == "CLOC", ("%s/%s, expected token CLOC, found token: %s value: %s"
					" i=%i, tindx=%i, ttypes=%s, editoken=%s") % (node.name, child, qi["ttypes"][tindx],
					sc["editoken"][tindx], i, tindx, qi["ttypes"], sc["editoken"])
				if qi["tokens"][tindx+1] == "LIKE":
					str_filt = "filter( (lambda x: like(%s, x)), value)" % make_like_pattern(qi["tokens"][tindx+2])
				else:
					str_filt = "filter( (lambda x: x %s %s), value)" % (qi["tokens"][tindx+1], qi["tokens"][tindx+2])
				matching_values = list(eval(str_filt))
				found_match = len(matching_values) > 0
				if found_match:
					# found values matching result, same them
					vi_res.add_vind_value(child, matching_values)
				# edit editoken for future eval.  Replace "cloc rop const" with "True" or "False"
				sc["editoken"][tindx] = ""
				sc["editoken"][tindx+1] = "%s" % found_match
				sc["editoken"][tindx+2] = ""

	def load_value(node, child, ctype):
		# load value from hdf5 node.  child-name of child, ctype- type of child
		nonlocal cpi, qi, fp
		if ctype["type"] == "attribute":
			value = node.attrs[child]
		elif ctype["sstype"] is not None:
			# value indicated by subscript (either 2d array column or compound datatype)
			(main, subscript) = qi["plocs"][cpi]['cloc_parts' ][child]
			if ctype["sstype"] == "2d":
				# value is column in 2d table, extract column by h5py slice
				value = node[main][:,int(subscript)]
			else:
				assert ctype["sstype"] == "compound", "unknown sstype found %s" % ctype["sstype"]
				value = node[main][subscript]
		else:
			# no subscript, load value directly
			value = node[child][()]  # was dataset.value; depreciated, use dataset[()] instead
		# assert len(value) > 0, "Empty value found: %s, %s" % (node.name, child) 
		value = convert_to_list(value)
		if len(value) > 0 and isinstance(value[0], h5py.h5r.Reference):
			# assume array of object references.  Convert to strings (names of objects)
			value = [fp[n].name for n in value]
		return value

	def get_row_values(node, ctypes, vtbl_res):
		# evals sc["editoken"], stores results in vtbl_res (a results.Vtbl_result object)
		# does search for rows within a table stored as datasets with aligned columns, some of which
		# might have an associated index array.
		# Does this by getting all values from the columns, using zip to create aligned tuples
		# and making expression that can be run using eval, with filter function.
		# Store found values in vtbl_res and return True if expression evaluates as True, otherwise
		# False.
		nonlocal sc, cpi, fp, qi
		cvals = []   # for storing all the column values
		cnames = []  # variable names associed with corresponding cval entry
		made_by_index = []  # list of clocs with associated _index.  Has an array in cvals.
		for i in range(len(sc["children"])):
			ctype = ctypes[i]
			if not ctype["drow"]:
				# skip values not part of a table with rows
				continue
			child = sc["children"][i]
			# check to see if this child was referenced before
			if child in cnames:
				# child was referenced before, use previous index
				val_idx = cnames.index(child)
			else:
				val_idx = len(cnames)
				cnames.append(child)
				value = load_value(node, child, ctype)
				# check for _index dataset.  main is either child name, or part without subscript
				main = child if ctype["sstype"] is None else qi["plocs"][cpi]['cloc_parts' ][child][0]
				child_index = main + "_index"
				if child_index in node:
					if not isinstance(node[child_index], h5py.Dataset):
						sys.exit("Node %s is not a Dataset, should be since has '_index' suffix" % child_index);
					index_vals = node[child_index][()]  # was dataset.value; depreciated, use dataset[()] instead
					value = make_indexed_lists(value, index_vals)
					# print("child=%s, after indexed vals=%s" % (child, value))
					made_by_index.append(child)
				cvals.append(value)
			# now have value and val_index associated with child. Edit expression if this child is in expression
			if i >= len(qi["plocs"][cpi]["display_clocs"]):
				# this appearence of child corresponds to an expression (display_clocs are first in children)
				# need to edit tokens
				cloc_idx = qi["plocs"][cpi]["cloc_index"][i - len(qi["plocs"][cpi]["display_clocs"])]
				assert qi["ttypes"][cloc_idx] == "CLOC", "%s/%s token CLOC should be at location with cloc_idx" %(
					node.name, child)
				assert qi["ttypes"][cloc_idx+2] in ("SC", "NC"), ("%s/%s child should be compared to string or number,"
					" found type '%i', value: '%s'" )% ( node.name, child, 
					qi["ttypes"][cloc_idx+2], sc["editoken"][cloc_idx+2])
				op = sc["editoken"][cloc_idx+1]
				const = sc["editoken"][cloc_idx+2]
				if child in made_by_index:
					# values are arrays with number in each element indicated by _index arrays
					# need to convert "child op const" to "in" or any(map( lambda y: y op const, x[i]))". Like this:
					# str_filt3="filter( (   lambda x: any(map( lambda y: y == 6, x[2]))   ), zipl)"
					if op == "LIKE":
						opstr = "any(map(lambda y: like(%s, y), x[%i]))" % (make_like_pattern(const), val_idx)
					elif op == "==":
						opstr = "%s in x[%i]" % (const, val_idx)
					else:
						opstr = "any(map(lambda y: y %s %s, x[%i]))" % (op, const, val_idx)
				else:
					# not made by an index.  Generate comparisions with scalar values
					if op == "LIKE":
						opstr = "like(%s, x[%i])" % (make_like_pattern(const), val_idx)
					else:
						opstr = "x[%i] %s %s" % (val_idx, op, const)
				# now opstr contains entire expression, save it, replacing original
				sc["editoken"][cloc_idx] = ""
				sc["editoken"][cloc_idx+1] = opstr
				sc["editoken"][cloc_idx+2] = ""				
		# Done with loop creating expression to evaluate
		# perform evaluation
		# replace "&" and "|" with and
		sqr = qi["plocs"][cpi]["range"]  # subquery range
		equery = [ "and" if x == "&" else "or" if x == "|" else x for x in sc["editoken"][sqr[0]:sqr[1]]]
		equery = " ".join(equery)  # make it a single string
		if equery == "":
			# there is no expression (only child being displayed).  Set to True so will display any values found
			equery = "True"
		# print("equery is: %s" % equery)
		if len(cvals) == 0:
			# no column values in this expression
			result = eval(equery)
		else:
			zipl = list(zip(*(cvals)))
			# print("zipl = %s" % zipl)
			# str_filt = "filter( (lambda x: %s), zipl)" % equery
			efs = "filter( (lambda x: %s), zipl)" % equery  # expression filter string
			# print("str_filt=%s" % str_filt)
			# result = list(eval(str_filt))
			result = list(eval(efs))
			if len(result) > 0:
				vtbl_res.set_tbl_result(cnames, result)
				result = True
			else:
				result = False
		return result

	# start of main body of runsubqeury
	sc = get_search_criteria(cpi, qi)
	# print("sc = %s" % sc)
	if sc['start_path'] not in fp:
		# import pdb; pdb.set_trace()
		# did not even find starting path in hdf5 file, cannot do search
		return False
	start_node = fp[sc['start_path']]
	search_node(None, start_node)
	if sc['search_all'] and isinstance(start_node,h5py.Group):
		start_node.visititems(search_node)
	# qr[cpi] = "cpi=%i, ploc=%s, sc=%s" % (cpi, qi["plocs"][cpi]["path"], sc)
	found = qr.get_subquery_length(cpi) > 0	# will have length > 1 if result found
	return found

# def display_result(path, qr):
# 	print("file %s:" % path)
# 	pp.pprint(qr)

def query_file(path, qi):
	global compiled_query_results
	fp = h5py.File(path, "r")
	if not fp:
		sys.exit("Unable to open %s" % path)
	# for storing query results
	# qr = [[] for i in range(len(qi["plocs"]))]
	# initialize File_result object for storing subquery results
	qr = results.File_result(path, len(qi["plocs"]))
	subquery_call_string = make_subquery_call_string(qi)
	# will be like: runsubquery(0,fp,qi,qr) & runsubquery(1,fp,qi,qr)
	# print("subquery_call_string is: %s" % subquery_call_string)
	result = eval(subquery_call_string)
	if result:
		compiled_query_results.add_file_result(qr)
		# display_result(path, qr)

def query_directory(dir, qi):
	# must find files to query.  dir must be a directory
	assert os.path.isdir(dir)
	for root, dirs, files in os.walk(dir, followlinks=True):
		for file in sorted(files):
			if file.endswith("nwb"):
				path = os.path.join(root, file)
				query_file(path, qi)

def query_file_or_directory(path, qi):
	# run a query on path, query specified in qi (query information, made in parse.parse)
	global compiled_query_results
	# initialize results for storing result of query
	compiled_query_results = results.Results()
	if os.path.isfile(path):
		query_file(path, qi)
	else:
		query_directory(path, qi)
	num_files_matching = compiled_query_results.get_num_files()
	print("Found %i matching files:" % num_files_matching)
	if num_files_matching > 0:
		pp.pprint( compiled_query_results.get_value() )

def do_interactive_queries(path):
	print("Enter query, control-d to quit")
	while True:
		try:
			query=input("> ")
		except EOFError:
			break;
		qi = parse.parse(query)
		query_file_or_directory(path, qi)
	print("\nDone running all queries")

def process_command_line(path, query):
	# path is either a directory (search for NWB files) or a NWB file
	# query is None (for interactive input), or a query to process
	if query is None:
		do_interactive_queries(path)
	else:
		qi = parse.parse(query)
		query_file_or_directory(path, qi)

def main():
	arglen = len(sys.argv)
	if arglen < 2 or arglen > 3:
		print("Usage: %s <path> [ <query> ]" % sys.argv[0])
		print(" <path> = path to an NWB file or to a directory containing nwb files")
		print(" <query> = query to execute (optional).  If present, must be quoted.")
		sys.exit("")
	path = sys.argv[1]
	if not os.path.exists(path):
		sys.exit("ERROR: path '%s' was not found!" % path)
	query = sys.argv[2] if arglen == 3 else None
	process_command_line(path, query)

if __name__ == "__main__":
	main()

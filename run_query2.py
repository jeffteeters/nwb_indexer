import sys
import os
import sqlite3
import re
import readline
import parse2
import make_sql
import pprint
readline.parse_and_bind('tab: complete')
pp = pprint.PrettyPrinter(indent=4)

# global variables
default_dbname="nwb_idx2.db"
con = None     # database connection
cur = None       # cursor


def open_database(db_path):
	global con, cur
	# this for development so don't have to manually delete database between every run
	print("Opening '%s'" % db_path)
	con = sqlite3.connect(db_path)
	cur = con.cursor()

# def show_vals(*args):
#     for val in args:
#         print(val)
#     return 1

# def add_function():
# 	global con
# 	con.create_function("check_nwb2_table", 3, show_vals)


def show_available_files():
	global con, cur
	result=cur.execute("select id, location from file order by id")
	rows=result.fetchall()
	num_rows = len(rows)
	print("Searching %i files:" % num_rows)
	n = 0
	for row in rows:
		n += 1
		print("%i. %s" % (row))

# def run_query(sql):
# 	global con, cur
# 	result=cur.execute(sql)
# 	rows=result.fetchall()
# 	num_rows = len(rows)
# 	print("Found %i:" % num_rows)
# 	n = 0
# 	for row in rows:
# 		n += 1
# 		print("%i. %s" % (n, row))

# def get_and_run_queries():
# 	print("Enter query, control-d to quit")
# 	while True:
# 		try:
# 			query=input("> ")
# 		except EOFError:
# 			break;
# 		qi = parse2.parse(query)
# 		if qi:
# 			sql = make_sql.make_sql(qi)
# 			print ("sql=\n%s" % sql)
# 			run_query(sql)
# 	print("\nDone processing all queries")


# def main_old():
# 	global con, dbname
# 	if len(sys.argv) > 2:
# 		sys.exit('Usage: %s [ <db.sqlite3> ]' % sys.argv[0])
# 	if len(sys.argv) == 1:
# 		print("Database not specified; using '%s'" % dbname)
# 	else:
# 		dbname=sys.argv[1]
# 	if not os.path.isfile(dbname):
# 		sys.exit("ERROR: database '%s' was not found!" % dbname)
# 	open_database()
# 	add_function()
# 	show_available_files()
# 	get_and_run_queries()
# 	# print ("scanning directory %s" % dir)
# 	# scan_directory(dir)
# 	con.close()


def do_query(sql, results, result_type):
	# execute query, saving in dict results using key 'result_type'
	global cur
	assert result_type in ("vind", "vrow")
	result=cur.execute(sql)
	rows=result.fetchall()
	for row in rows:
		file = row[0]
		node_path = row[1]
		if file not in results:
			results[file] = {node_path: {result_type: row[2:]}}
		elif node_path not in results[file]:
			results[file][node_path] = {result_type: row[2:]}
		elif result_type not in results[file][node_path]:
			results[file][node_path][result_type] = row[2:]
		else:
			sys.exit("multiple results found for %s, %s, %s" % (file, node_path, result_type))

def runsubquery(cpi, qi, qr):
	# run subquery with current ploc_index cpi and query information (qi)
	# store search results in qr[cpi] (qr is a list, cpi is the index to each element)/
	# qr[cpi] is also a list.  Each element is a dictionary with the following format:
	# {"node": "/path/to/parent/node",
	#  "vind": [
	#            [cname1, val11, val12, val13, ...], [cname2, val21, val22, val23, ...] # cname - child name
	#          ]
	#  "vrow": [   # for values stored in tables, need to return rows
	#			 [col1Name,  col2name,  col3name, ...]  # the headers
	#			 [col1val1,  col2val1,  col3val1, ...]  # a tuple for each set of values found
	#			 [col1val2,  col2val2,  col3val2, ...]
	#          ]
	# }
	# return True if search results found, False otherwise
	results = {}
	sql_maker = make_sql.SQL_maker(qi)
	# do normal query
	sql = sql_maker.make_normal_sql(cpi)
	do_query(sql, results, "vind")
	sql = sql_maker.make_table_sql()
	do_query(sql, results, "vrow")
	if results:
		qr[cpi] = results
		return True
	else:
		return False


# def runsubquery_old(cpi, fp, qi, qr):
# 	# run subquery with current ploc_index cpi and query information (qi)
# 	# store search results in qr[cpi] (qr is a list, cpi is the index to each element)/
# 	# qr[cpi] is also a list.  Each element is a dictionary with the following format:
# 	# {"node": "/path/to/parent/node",
# 	#  "vind": [
# 	#            [cname1, val11, val12, val13, ...], [cname2, val21, val22, val23, ...] # cname - child name
# 	#          ]
# 	#  "vrow": [   # for values stored in tables, need to return rows
# 	#			 [col1Name,  col2name,  col3name, ...]  # the headers
# 	#			 [col1val1,  col2val1,  col3val1, ...]  # a tuple for each set of values found
# 	#			 [col1val2,  col2val2,  col3val2, ...]
# 	#          ]
# 	# }
# 	# return True if search results found, False otherwise

# 	def search_node(name, node):
# 		# search one node, may be group or dataset
# 		# name is ignored
# 		# cpi - current ploc index, fp - h5py file pointer
# 		# qi - query information, qr - container for query results
# 		# sc search criteria
# 		# must always return None to allow search (visititems) to continue
# 		nonlocal sc, cpi, fp, qi, qr
# 		if sc["match_path"] and not re.fullmatch(sc["match_path"], node.name):
# 			# path does not pattern specified in query
# 			return None
# 		ctypes = []  # types of found children
# 		for child in sc["children"]:
# 			ctype = get_child_type(node, child)
# 			if ctype is None:
# 				# child not found, skip this node
# 				return None
# 			ctypes.append(ctype)
# 		# found all the children, do search for values, store in query results (qre)
# 		qre = {"vind": [], "vrow": []}
# 		initialize_editoken(sc, qi)
# 		get_individual_values(node, ctypes, qre)	# fills qre["vind"], edits sc["editoken"]
# 		found = get_row_values(node, ctypes, qre)	# evals sc["editoken"], fills qre["vrow"]
# 		if found:
# 			# found some results, save them
# 			qre["node"] = node.name
# 			qr[cpi].append(qre)
# 		return None

# 	def get_child_type(node, child):
# 		# return type of child inside of node.
# 		# Is one of following:
# 		# None - not present
# 		# Dictionary, with keys:
# 		#    type - "attribute" - attribute, or "dataset" - dataset
# 		#    If type attribute, has key drow == False (since not part of table with rows)
# 		#    If type dataset, then also has keys:
# 		#        drow - True if in table with rows (aligned columns), False otherwise
# 		#        sstype - subscript type.  Either:
# 		#           None (no subscript),
# 		#           "compound" (column in compound dataset).
# 		#           "2d" (column in 2-d dataset.  Index will be an integer, e.g. [1])
# 		nonlocal sc, cpi, fp, qi, qr
# 		if child in node.attrs:
# 			return {"type": "attribute", "drow": False}
# 		if not isinstance(node,h5py.Group):
# 			# can't be dataset because parent is not a group
# 			return None
# 		if child in node and isinstance(node[child], h5py.Dataset):
# 			# child is dataset inside a group; check for part of a table (drow = True)
# 			drow = "colnames" in node.attrs and (child == "id" or 
# 				child in [s.decode("utf-8").strip() for s in node.attrs["colnames"]])
# 			sstype = False	# not subscript since full child name found
# 			return {"type": "dataset", "sstype": None, "drow": drow}
# 		if child not in qi["plocs"][cpi]["cloc_parts"]:
# 			# no subscript, child not found
# 			return None
# 		# have subscript
# 		(main, subscript) = qi["plocs"][cpi]["cloc_parts"][child]
# 		if main in node and isinstance(node[main], h5py.Dataset):
# 			if len(node[main].shape) == 2:
# 				# found 2d table
# 				if subscript.isdigit() and int(subscript) < node[main].shape[1]:
# 					# found 2d table and index is valid (integer less than number of columns)
# 					sstype = "2d"
# 				else:
# 					# found 2 table, but index is invalid (not integer or greater than number of cols)
# 					return None
# 			elif len(node[main].shape) ==1 and subscript in node[main].dtype.names:
# 				# subscript is a name in a compound type.  e.g.:
# 				# >>> ts.dtype.names
# 				# ('idx_start', 'count', 'timeseries')
# 				sstype = "compound"
# 			else:
# 				# subscript not part of this dataset
# 				return None
# 			# if made it here, have valid subscript.  Now determine if main is part of table (drow = True)
# 			drow = "colnames" in node.attrs and (main == "id" or 
# 				main in [s.decode("utf-8").strip() for s in node.attrs["colnames"]])
# 			return {"type": "dataset", "sstype": sstype, "drow": drow}

# 	def get_individual_values(node, ctypes, qre):
# 		# fills qre["vind"], edits sc["editoken"]
# 		# finds values of individual variables (not part of table) satisifying search criteria
# 		# to do that, for each individual variable, evals the binary expression, saving values that
# 		# result in True.  Edit sc["editoken"] replacing: var op const with True or False in
# 		# perperation for eval done in get_row_values.
# 		nonlocal sc, cpi, fp, qi
# 		for i in range(len(sc["children"])):
# 			ctype = ctypes[i]
# 			if ctype["drow"]:
# 				# skip values part of a table with rows
# 				continue
# 			child = sc["children"][i]
# 			value = load_value(node, child, ctype)
# 			if i < len(qi["plocs"][cpi]["display_clocs"]): 
# 				# just displaying these values, not part of expression.  Save it.  (display_clocs are first in children)
# 				qre["vind"].append([child, ] + value)
# 			else:
# 				# child is part of expression.  Need to make string for eval to find values
# 				# matching criteria, save matching values, and edit sc["editoken"]
# 				tindx = qi["plocs"][cpi]["cloc_index"][i - len(qi["plocs"][cpi]["display_clocs"])]  # token index
# 				assert qi["ttypes"][tindx] == "CLOC", ("%s/%s, expected token CLOC, found token: %s value: %s"
# 					" i=%i, tindx=%i, ttypes=%s, editoken=%s") % (node.name, child, qi["ttypes"][tindx],
# 					sc["editoken"][tindx], i, tindx, qi["ttypes"], sc["editoken"])
# 				if qi["tokens"][tindx+1] == "LIKE":
# 					str_filt = "filter( (lambda x: like(%s, x)), value)" % make_like_pattern(qi["tokens"][tindx+2])
# 				else:
# 					str_filt = "filter( (lambda x: x %s %s), value)" % (qi["tokens"][tindx+1], qi["tokens"][tindx+2])
# 				matching_values = list(eval(str_filt))
# 				found_match = len(matching_values) > 0
# 				if found_match:
# 					# found values matching result, same them
# 					qre["vind"].append([child, ] + matching_values)
# 				# edit editoken for future eval.  Replace "cloc rop const" with "True" or "False"
# 				sc["editoken"][tindx] = ""
# 				sc["editoken"][tindx+1] = "%s" % found_match
# 				sc["editoken"][tindx+2] = ""

# 	def load_value(node, child, ctype):
# 		# load value from hdf5 node.  child-name of child, ctype- type of child
# 		nonlocal cpi, qi, fp
# 		if ctype["type"] == "attribute":
# 			value = node.attrs[child]
# 		elif ctype["sstype"] is not None:
# 			# value indicated by subscript (either 2d array column or compound datatype)
# 			(main, subscript) = qi["plocs"][cpi]['cloc_parts' ][child]
# 			if ctype["sstype"] == "2d":
# 				# value is column in 2d table, extract column by h5py slice
# 				value = node[main][:,int(subscript)]
# 			else:
# 				assert ctype["sstype"] == "compound", "unknown sstype found %s" % ctype["sstype"]
# 				value = node[main][subscript]
# 		else:
# 			# no subscript, load value directly
# 			value = node[child].value
# 		# assert len(value) > 0, "Empty value found: %s, %s" % (node.name, child) 
# 		value = convert_to_list(value)
# 		if len(value) > 0 and isinstance(value[0], h5py.h5r.Reference):
# 			# assume array of object references.  Convert to strings (names of objects)
# 			value = [fp[n].name for n in value]
# 		return value

# 	def get_row_values(node, ctypes, qre):
# 		# evals sc["editoken"], fills qre["vrow"]
# 		# does search for rows within a table stored as datasets with aligned columns, some of which
# 		# might have an associated index array.
# 		# Does this by getting all values from the columns, using zip to create aligned tuples
# 		# and making expression that can be run using eval, with filter function.
# 		# Store found values in qre["vrow"] and return True if expression evaluates as True, otherwise
# 		# False.
# 		nonlocal sc, cpi, fp, qi
# 		cvals = []   # for storing all the column values
# 		cnames = []  # variable names associed with corresponding cval entry
# 		made_by_index = []  # list of clocs with associated _index.  Has an array in cvals.
# 		for i in range(len(sc["children"])):
# 			ctype = ctypes[i]
# 			if not ctype["drow"]:
# 				# skip values not part of a table with rows
# 				continue
# 			child = sc["children"][i]
# 			# check to see if this child was referenced before
# 			if child in cnames:
# 				# child was referenced before, use previous index
# 				val_idx = cnames.index(child)
# 			else:
# 				val_idx = len(cnames)
# 				cnames.append(child)
# 				value = load_value(node, child, ctype)
# 				# check for _index dataset.  main is either child name, or part without subscript
# 				main = child if ctype["sstype"] is None else qi["plocs"][cpi]['cloc_parts' ][child][0]
# 				child_index = main + "_index"
# 				if child_index in node:
# 					if not isinstance(node[child_index], h5py.Dataset):
# 						sys.exit("Node %s is not a Dataset, should be since has '_index' suffix" % child_index);
# 					index_vals = node[child_index].value;
# 					value = make_indexed_lists(value, index_vals)
# 					# print("child=%s, after indexed vals=%s" % (child, value))
# 					made_by_index.append(child)
# 				cvals.append(value)
# 			# now have value and val_index associated with child. Edit expression if this child is in expression
# 			if i >= len(qi["plocs"][cpi]["display_clocs"]):
# 				# this appearence of child corresponds to an expression (display_clocs are first in children)
# 				# need to edit tokens
# 				cloc_idx = qi["plocs"][cpi]["cloc_index"][i - len(qi["plocs"][cpi]["display_clocs"])]
# 				assert qi["ttypes"][cloc_idx] == "CLOC", "%s/%s token CLOC should be at location with cloc_idx" %(
# 					node.name, child)
# 				assert qi["ttypes"][cloc_idx+2] in ("SC", "NC"), ("%s/%s child should be compared to string or number,"
# 					" found type '%i', value: '%s'" )% ( node.name, child, 
# 					qi["ttypes"][cloc_idx+2], sc["editoken"][cloc_idx+2])
# 				op = sc["editoken"][cloc_idx+1]
# 				const = sc["editoken"][cloc_idx+2]
# 				if child in made_by_index:
# 					# values are arrays with number in each element indicated by _index arrays
# 					# need to convert "child op const" to "in" or any(map( lambda y: y op const, x[i]))". Like this:
# 					# str_filt3="filter( (   lambda x: any(map( lambda y: y == 6, x[2]))   ), zipl)"
# 					if op == "LIKE":
# 						opstr = "any(map(lambda y: like(%s, y), x[%i]))" % (make_like_pattern(const), val_idx)
# 					elif op == "==":
# 						opstr = "%s in x[%i]" % (const, val_idx)
# 					else:
# 						opstr = "any(map(lambda y: y %s %s, x[%i]))" % (op, const, val_idx)
# 				else:
# 					# not made by an index.  Generate comparisions with scalar values
# 					if op == "LIKE":
# 						opstr = "like(%s, x[%i])" % (make_like_pattern(const), val_idx)
# 					else:
# 						opstr = "x[%i] %s %s" % (val_idx, op, const)
# 				# now opstr contains entire expression, save it, replacing original
# 				sc["editoken"][cloc_idx] = ""
# 				sc["editoken"][cloc_idx+1] = opstr
# 				sc["editoken"][cloc_idx+2] = ""				
# 		# Done with loop creating expression to evaluate
# 		# perform evaluation
# 		# replace "&" and "|" with and
# 		sqr = qi["plocs"][cpi]["range"]  # subquery range
# 		equery = [ "and" if x == "&" else "or" if x == "|" else x for x in sc["editoken"][sqr[0]:sqr[1]]]
# 		equery = " ".join(equery)  # make it a single string
# 		# print("equery is: %s" % equery)
# 		if len(cvals) == 0:
# 			# are no column values in this expression.  Just evaluate it
# 			result = eval(equery)
# 		else:
# 			zipl = list(zip(*(cvals)))
# 			# print("zipl = %s" % zipl)
# 			str_filt = "filter( (lambda x: %s), zipl)" % equery
# 			# print("str_filt=%s" % str_filt)
# 			result = list(eval(str_filt))
# 			if len(result) > 0:
# 				qre["vrow"].append([cnames, ] + result)
# 				result = True
# 			else:
# 				result = False
# 		return result

# 	# start of main body of runsubqeury
# 	sc = get_search_criteria(cpi, qi)
# 	# print("sc = %s" % sc)
# 	if sc['start_path'] not in fp:
# 		# did not even find starting path in hdf5 file, cannot do search
# 		return False
# 	start_node = fp[sc['start_path']]
# 	search_node(None, start_node)
# 	if sc['search_all'] and isinstance(start_node,h5py.Group):
# 		start_node.visititems(search_node)
# 	# qr[cpi] = "cpi=%i, ploc=%s, sc=%s" % (cpi, qi["plocs"][cpi]["path"], sc)
# 	found = len(qr[cpi]) > 0  # will have content if result found
# 	return found


# def get_search_criteria(cpi, qi):
# 	# get sc (search_criteria) for finding hdf5 group or dataset to perform search
# 	# sc = {
# 	#  start_path - path to starting element to search.  This is specified by parent in query
# 	#  match_path - regular expression for path that must match parent to do search.  Also
# 	#               specified by parent in query.  May be different than start_path if 
# 	#               wildcards are in parent.  Is None if search_all is False
# 	#  search_all - True if searching all children of start_path.  False if searching just within
# 	#               start_path
# 	#  children   - list of children (attributes or datasets) that must be present to find a match
# 	#  editoken   - tokens making up subquery, which will be "edited" to perform query.
# 	#               Initially is copy of tokens
# 	# }
# 	ploc = qi["plocs"][cpi]["path"]
# 	idx_first_star = ploc.find("*")
# 	if idx_first_star > -1:
# 		# at least one star (wild card)
# 		start_path = ploc[0:idx_first_star]
# 		if not start_path:
# 			start_path = "/"
# 		search_all = True   # search all if wildcard character in parent location
# 		match_path = ploc.replace("*", ".*")  # replace * with *. for RE match later
# 	else:
# 		start_path = ploc
# 		match_path = None
# 		search_all = False
# 	# make list of children
# 	children = qi["plocs"][cpi]["display_clocs"].copy()
# 	for i in qi["plocs"][cpi]["cloc_index"]:
# 		children.append(qi["tokens"][i])
# 	sc = {"start_path": start_path, "match_path": match_path,
# 		"search_all": search_all, "children": children}
# 	return sc











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
			cs_tokens.append("runsubquery(%i,qi,qr)" % cpi)
			i = qi['plocs'][cpi]["range"][1]  # advance to end (skiping all tokens in subquery)
			cpi += 1
	return " ".join(cs_tokens)

def display_result(qr):
	print("results are:")
	# print("file %s:" % path)
	pp.pprint(qr)

def eval_subqueries(qi):
	# start of evaluation of subqueries
	# for storing query results
	qr = [[] for i in range(len(qi["plocs"]))]
	subquery_call_string = make_subquery_call_string(qi)
	# print("%s" % subquery_call_string)
	# will be like: runsubquery(0,fp,qi,qr) & runsubquery(1,fp,qi,qr)
	result = eval(subquery_call_string)
	if result:
	 	display_result(qr)

def do_interactive_queries():
	show_available_files()
	print("Enter query, control-d to quit")
	while True:
		try:
			query=input("> ")
		except EOFError:
			break;
		qi = parse2.parse(query)
		eval_subqueries(qi)
	print("\nDone running all queries")

def process_command_line(query):
	# query is None (for interactive input), or a query to process from the command line
	if query is None:
		do_interactive_queries()
	else:
		qi = parse2.parse(query)
		eval_subqueries(qi)

def main():
	global default_dbname, con
	arglen = len(sys.argv)
	if arglen < 2 or arglen > 3:
		print("Usage: %s <db_path> [ <query> ]" % sys.argv[0])
		print(" <path> = path to sqlite3 database file or '-' for default database (%s)" % default_dbname)
		print(" <query> = query to execute (optional).  If present, must be quoted.")
		sys.exit("")
	db_path = sys.argv[1]
	query = sys.argv[2] if arglen == 3 else None
	if db_path == "-":
		db_path = default_dbname
		if not query:
			# only display message if query not specified in command line
			print("Using default path: '%s'" % db_path)
	if not os.path.exists(db_path):
		sys.exit("ERROR: database '%s' was not found!" % db_path)
	open_database(db_path)
	process_command_line(query)
	con.close()

if __name__ == "__main__":
    main()
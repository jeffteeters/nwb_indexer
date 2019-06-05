import sys
import os
import sqlite3
import re
import readline
import parse2
import make_sql
import pprint
import results

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

class Cloc_info_manager:
	# manages information about child locations within each parent location
	# Is used by the following call sequence:
	# 1. Cloc_info_manager(qi)  - Initialize for all subsequent calls
	# 2. set_file_id(file_id)  - Specify file_id for query result
	# 3. set_ploc_index(pi)   - Specify which ploc (parent location, e.g. subquery) for query result
	# 4. get_number_of_nodes() - returns number of nodes found for specified file_id, and pi
	#			Used so calling routine knows how many nodes were returned and can can call set_node_index
	# 5. set_node_index(node_index) - Specifies node index (index of group or dataset) for obtaining results
	# 6. get_child_info - returns dictionary "query_child_info" which has value of each child to use in query

	# for finding values (in sqlite3 database) associated with child locations (cloc's) in query
	def __init__(self, qi):
		# qi is query information, output of parse2.
		self.qi = qi
		self.compute_sql_query_results()

	def get_file_ids(self):
		# return list of file_ids that are in sql_query_results (self.sqr)
		return sorted(self.sqr)

	def set_file_id(self, file_id):
		# file_id in first subscript in self.sqr (made by get_sql_query_results)
		self.file_id = file_id
		self.ploc_index = None 	# make sure set_ploc_index called after this

	def get_file_name(self):
		# return name of current file being processed
		return self.sqr[self.file_id]["file_name"]

	def set_ploc_index(self, pi):
		# pi is index to current ploc (parent location).  It is the second component of the self.sqr
		assert pi >= 0 and pi < len(self.sqr[self.file_id]["sq"])
		self.pi = pi
		self.compute_query_children()
		self.node_index = None 	# make sure set_node_index always called after this

	def get_number_of_nodes(self):
		# return number of nodes in query result for current file and ploc location
		return len(self.sqr[self.file_id]["sq"][self.pi])

	def set_node_index(self, node_index):
		# set node index used in get_sql_child_info and get_query_child_info
		assert node_index >= 0 and node_index < self.get_number_of_nodes()
		self.node_index = node_index
		self.compute_children_info()

	def get_node_name(self):
		return self.sqr[self.file_id]["sq"][self.pi][self.node_index]["node"]

	def get_query_children(self):
		return self.query_children

	def get_children_info(self):
		return self.query_children_info


	# methods below are not meant to be called only internally (e.g. are private)

	def compute_sql_query_results(self):
		# gets results of sql query for ALL plocs (parent locations).  Saves in self.sqr
		def do_sql_query(sql, sqr, pi, result_type, num_plocs):
				# execute query sql, saving in dict results using key 'result_type'.
				# pi is the parent (ploc) index
				global cur
				assert result_type in ("vind", "vrow")
				result=cur.execute(sql)
				rows=result.fetchall()
				# print("sql query result for %s" % result_type)
				# pp.pprint(rows)
				for row in rows:
					file_id = row[0]
					file_name = row[1]
					node_path = row[2]
					node_type = row[3]
					if file_id not in sqr:
						sq = [ [] for i in range(num_plocs) ] 
						sqr[file_id] = { "file_name": file_name, "sq": sq }
					sqr[file_id]["sq"][pi].append ( {"node": node_path,
							"node_type": node_type, result_type: row[4:] } )
		# start of main body of get_sql_query_results
		qi = self.qi
		# sql_maker = make_sql.SQL_maker(qi)
		# sqr - for storing sub query results.  Format is:
		# { file_id: { "file_name": <file_name>, "sq": [ <sq0_results>, <sq1_results>, ... ]}
		# where <sqN_results> is [ <node1>, <node2>, <node3> ...  ]
		# and <nodeN> is { "node": <node_name>, "vind": <vind_results>, "vrow": <vrow_results> }
		sqr = {}
		num_plocs = len(qi["plocs"])
		for pi in range(num_plocs):
			sql = make_sql.make_sql(qi, pi, "normal")
			# print("normal sql is: %s" % sql)
			do_sql_query(sql, sqr, pi, "vind", num_plocs)
			sql = make_sql.make_sql(qi, pi, "table")
			# print("table sql is: %s" % sql)
			do_sql_query(sql, sqr, pi, "vrow", num_plocs)
		# save it in object
		self.sqr = sqr
		# print("sqr = ")
		# pp.pprint(self.sqr)

	def compute_query_children(self):
		# get list of children (attributes or datasets) specified in query
		qi = self.qi
		pi = self.pi
		query_children = qi["plocs"][pi]["display_clocs"].copy()
		for i in qi["plocs"][pi]["cloc_index"]:
			query_children.append(qi["tokens"][i])
		self.query_children = query_children

	def compute_children_info(self):
		self.compute_sql_children_info()
		self.compute_query_children_info()

	def compute_sql_children_info(self):
		# create sql_children_info dictionary, which contains info about children returned by sql queries
		# (that is, for each child stored in sqr for the current parent). Has form:
		# { child_name: { "node_type": <node_type>, "value_type": <value_type>, "value": <value> }}
		node_qr = self.sqr[self.file_id]["sq"][self.pi][self.node_index]
		children_info = {}
		# each node query result should have either key "vind" or "vrow"
		assert "vind" in node_qr or "vrow" in node_qr
		qtype = "vind" if "vind" in node_qr else "vrow"
		for i in range(0, len(node_qr[qtype]), 4):
			child_name = node_qr[qtype][i]
			node_type = node_qr[qtype][i+1]  # type of child node, not parent node
			value_type = node_qr[qtype][i+2]
			value = node_qr[qtype][i+3]
			# safety check
			assert value_type in ('i', 'f', 's', 'I', 'F', 'S', 'c', 'M')
			assert node_type in ('g', 'd', 'a', 'G')
			# assert child_name in children
			children_info[child_name] = { "node_type": node_type, "value_type": value_type, "value": value }
		self.sql_children_info = children_info
		# print("sql_children_info = ")
		# pp.pprint(self.sql_children_info)

	def compute_query_children_info(self):
		# create query_children_info dictionary, which for each child specified in query, has form:
		# { query_child_name: { "node_type": <attribute | dataset>,
		#		"drow": True | False, "decoded_value": <value>, "using_index": True | False} }
		# return None if not all children are found (which might happen if a subscript is not present
		# in the found sql value. In other words, the child_name in the query may have a subscript,
		# but the child name in the sql results will never have a subscript.  If the subscript
		# spqcified on the query (by the user) is not in the value of the SQL query, for ANY of the
		# query children, store None (since all values are required for the query to match).
		query_children_info = {}
		for query_child in self.query_children:
			# check for subscript on query_child
			if query_child in self.qi["plocs"][self.pi]["cloc_parts"]:
				child, subscript = self.qi["plocs"][self.pi]["cloc_parts"][query_child]
			else:
				child = query_child
				subscript = None
			sql_ci = self.sql_children_info[child]
			decoded_value, using_index = self.decode_sql_value(subscript, sql_ci["value"], sql_ci["value_type"])
			if decoded_value is None:
				# specified subscript not found, so unable to obtain value for this child
				self.query_children_info = None
				return
			drow = sql_ci["value_type"] in ("I", "F", "c", "M")  # set true if part of dynamic row
			assert sql_ci["node_type"] in ("d", "a")  # should be either attribute or dataset
			node_type = "attribute" if sql_ci["node_type"] == "a" else "Dataset"
			query_children_info[query_child] = {"decoded_value": decoded_value, "drow": drow,
				"node_type": node_type, "using_index": using_index}
		self.query_children_info = query_children_info
		# print("query_children_info = ")
		# pp.pprint(self.query_children_info)

	def decode_sql_value(self, subscript, packed_value, value_type):
		# convert packed_value (saved as string in sqlite) into list that can be used directly
		# for evaluating expression.
		# subscript is subscript used to access value stored in column of array or None if not
		# present.
		# value_type is "c" if subscript needed, otherwise something else
		# all possible value types are: ('i', 'f', 's','I', 'F', 'S', 'c','M'),
		# -- either: i-integer, f-float, s-string, I-int array, F-float array,
		#    S-string array, c-compound or 2-d
		#    M - string array part of table (type 'I', 'F' and 'c' also part of table)
		assert value_type in ('i', 'f', 's', 'I', 'F', 'S', 'c', 'M')
		subscript_needed = value_type == "c"
		have_subscript = subscript is not None
		if subscript_needed != have_subscript:
			# either subscript needed and not present or present and not needed.  In either case
			# value required (from query) does not match value stored
			return None
		# check for numeric scalar
		if value_type in ('i', 'f'):
			assert ((value_type == 'i' and isinstance(packed_value, int))
				or (value_type == 'f' and isinstance(packed_value, float))
				or (packed_value == 'nan') )
			value = [packed_value, ] # return list of one number
			using_index = False
			return (value, using_index)
		# check for single string
		if value_type in ('s'):
			assert (isinstance(packed_value, str))
			value = [packed_value, ] # return list of one string
			using_index = False
			return (value, using_index)
		# strip off "_index" values if present
		packed_value, separator, packed_index_values = packed_value.partition(";i;")
		using_index = packed_index_values != ''
		# if subscript used, extract specified column
		if have_subscript:
			subscripts, semicolon, concatenated_columns = sql_ci["value"].partition(";")
			available_subscripts = subscripts.split(",")
			# last character of subscript is type code.  Extract names and type codes
			available_subscript_types = [x[-1] for x in available_subscripts]
			available_subscript_names = [x[0:-1] for x in available_subscripts]
			found_subscript = subscript in available_subscript_names
			if found_subscript:
				index = available_subscript_names.index(subscript)
				type_code = available_subscript_types[index]
				packed_value = concatenated_columns.split(";")[index]
			else:
				# specified subscript not found
				return None
			# replace value_type 'c' with type_code obtained from last character of column subscript
			assert(value_type == 'c')
			value_type = type_code
		# unpack packed_values
		# if value_type == "n":
		# 	value = list(float(packed_value))
		# elif value_type == 's':
		# 	value = [packed_value, ]  # convert to list with one element
		if value_type == 'I':
			# list of integers
			value = list(map(int, packed_value.split(',')))
		elif value_type == 'F':
			# list of floats
			value = list(map(float, packed_value.split(',')))
		else:
			# should be array of strings
			assert packed_value[0] == "'" and packed_value[-1] == "'", (
				"decode_sql_value: packed value '%s' not string, value_type == '%s'" % (
					packed_value, value_type))
			value = packed_value[1:-2].split("','")
		if using_index:
			# need to modify list of items using _index values
			index_values = list(map(int, packed_index_values.split(',')))
			value = self.make_indexed_lists(value, index_values)
		return (value, using_index)

	def make_indexed_lists(self, tags, tags_index):
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

# end of class Cloc_info_manager:


# def initialize_editoken(sc, qi):
# 	# editoken needs to be refreshed for every new node searching
# 	sc["editoken"] = qi["tokens"].copy()

def make_like_pattern(sql_pattern):
	# convert SQL like pattern (with "%" as wildcard) to regular expression pattern (with ".*" wildcard)
	re_pattern = sql_pattern.replace("%", ".*")
	# re_pattern = re_pattern.strip("\"'")
	return re_pattern

def like(pattern, text):
	# implements LIKE operator.  pattern must be a regular expression, with "%" replaced by .*
	if isinstance(text, bytes):
		text = text.decode("utf-8")
	match = re.fullmatch(pattern, text)
	found_match = match is not None
	return found_match

def runsubquery(pi, cim, qr):
	# Run subquery with current ploc_index pi, Cloc_info_manager (cim).
	# Store search results in qr, which is a results.File_result object (see file results.py).
	# return True if search results found, False otherwise

	def check_node():
		# check one node (parent) may be group or dataset.
		# pi - parent index (ploc index, e.g. subquery index)
		# subquery and node being checked in specified by state of cim
		# qr - container for query results
		nonlocal pi, cim, qr
		children_info = cim.get_children_info()
		if children_info is None:
			# could not obtain all values for this node, only reason should be because subscripts don't match 
			return
		# editoken needs to be refreshed for every new node searching
		editoken = cim.qi["tokens"].copy()
		vi_res = results.Vind_result()	# for storing individual results
		get_individual_values(editoken, vi_res)	# fills vi_res, edits editoken"]
		vtbl_res = results.Vtbl_result()	# for storing row results
		found = get_row_values(editoken, vtbl_res)
		if found:
			# found some results, save them
			node_name = cim.get_node_name()
			# in following put a slash in front of the node so the path will start with a '/'
			node_result = results.Node_result('/' + node_name, vi_res, vtbl_res)
			qr.add_node_result(node_result, pi)

	def get_individual_values(editoken, vi_res):
		# Fills vi_res (a results.Vind_result object) with individual results; edits editoken.
		# Finds values of individual variables (not part of table) satisifying search criteria
		# to do that, for each individual variable, evals the binary expression, saving values that
		# result in True.  Edit editoken replacing: var op const with True or False in
		# preparation for eval done in get_row_values.
		nonlocal cim
		qi = cim.qi
		cpi = cim.pi  # cpi == current ploc index
		query_children = cim.get_query_children()
		children_info = cim.get_children_info()
		for i in range(len(query_children)):
			child = query_children[i]
			child_info = children_info[child]
			if child_info["drow"]:
				# skip values part of a table with rows
				continue			
			value = child_info["decoded_value"]
			if i < len(qi["plocs"][cpi]["display_clocs"]): 
				# just displaying these values, not part of expression.  Save it.  (display_clocs are first in children)
				vi_res.add_vind_value(child, value)
			else:
				# child is part of expression.  Need to make string for eval to find values
				# matching criteria, save matching values, and edit sc["editoken"]
				tindx = qi["plocs"][cpi]["cloc_index"][i - len(qi["plocs"][cpi]["display_clocs"])]  # token index
				if qi["ttypes"][tindx] != "CLOC":
					node_name = cim.get_node_name()
					sys.exit(("%s/%s, expected token CLOC, found token: %s value: %s"
					" i=%i, tindx=%i, ttypes=%s, editoken=%s") % (node_name, child, qi["ttypes"][tindx],
					editoken[tindx], i, tindx, qi["ttypes"], editoken))
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
				editoken[tindx] = ""
				editoken[tindx+1] = "%s" % found_match
				editoken[tindx+2] = ""

	def get_row_values(editoken, vtbl_res):
		# evals editoken, stores results in vtbl_res (a results.Vtbl_result object)
		# Does search for rows within a table stored as datasets with aligned columns, some of which
		# might have an associated index array.
		# Does this by getting all values from the columns, using zip to create aligned tuples
		# and making expression that can be run using eval, with filter function.
		# Store found values in vtbl_res and return True if expression evaluates as True, otherwise
		# False.
		nonlocal cim
		qi = cim.qi
		cpi = cim.pi  # cpi == current ploc index
		query_children = cim.get_query_children()
		children_info = cim.get_children_info()
		cvals = []   # for storing all the column values
		cnames = []  # variable names associed with corresponding cval entry
		made_by_index = []  # list of clocs with associated _index.  Has an array in cvals.
		# made_by_index = []  # list of clocs with associated _index.  Has an array in cvals.
		for i in range(len(query_children)):
			child = query_children[i]
			child_info = children_info[child]
			if not child_info["drow"]:
				# skip values not part of a table with rows
				continue
			# check to see if this child was referenced before
			if child in cnames:
				# child was referenced before, use previous index
				val_idx = cnames.index(child)
			else:
				val_idx = len(cnames)
				cnames.append(child)
				value = child_info["decoded_value"]
				if child_info["using_index"]:
					made_by_index.append(child)
				cvals.append(value)
			# now have value and val_index associated with child. Edit expression if this child is in expression
			if i >= len(qi["plocs"][cpi]["display_clocs"]):
				# this appearence of child corresponds to an expression (display_clocs are first in children)
				# need to edit tokens
				node_name = cim.get_node_name()
				cloc_idx = qi["plocs"][cpi]["cloc_index"][i - len(qi["plocs"][cpi]["display_clocs"])]
				assert qi["ttypes"][cloc_idx] == "CLOC", "%s/%s token CLOC should be at location with cloc_idx" %(
					node_name, child)
				assert qi["ttypes"][cloc_idx+2] in ("SC", "NC"), ("%s/%s child should be compared to string or number,"
					" found type '%i', value: '%s'" )% ( node_name, child, 
					qi["ttypes"][cloc_idx+2], editoken[cloc_idx+2])
				op = editoken[cloc_idx+1]
				const = editoken[cloc_idx+2]
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
				editoken[cloc_idx] = ""
				editoken[cloc_idx+1] = opstr
				editoken[cloc_idx+2] = ""				
		# Done with loop creating expression to evaluate
		# perform evaluation
		# replace "&" and "|" with and
		sqr = qi["plocs"][cpi]["range"]  # subquery range
		equery = [ "and" if x == "&" else "or" if x == "|" else x for x in editoken[sqr[0]:sqr[1]]]
		equery = " ".join(equery)  # make it a single string
		# print("equery is: %s" % equery)
		if len(cvals) == 0:
			# are no column values in this expression.  Just evaluate it
			result = eval(equery)
		else:
			zipl = list(zip(*(cvals)))
			# print("zipl = %s" % zipl)
			str_filt = "filter( (lambda x: %s), zipl)" % equery
			# print("str_filt=%s" % str_filt)
			result = list(eval(str_filt))
			if len(result) > 0:
				vtbl_res.set_tbl_result(cnames, result)
				result = True
			else:
				result = False
		return result

	# start of main body of runsubqeury
	# children = get_list_of_children(cpi, qi)
	# loop through each node in fqr
	cim.set_ploc_index(pi)
	num_nodes = cim.get_number_of_nodes()
	for node_index in range(num_nodes):
		cim.set_node_index(node_index)
		check_node()
	found = qr.get_subquery_length(pi) > 0	# will have length > 1 if result found
	return found

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
			cs_tokens.append("runsubquery(%i,cim,qr)" % cpi)
			i = qi['plocs'][cpi]["range"][1]  # advance to end (skiping all tokens in subquery)
			cpi += 1
	return " ".join(cs_tokens)

def perform_query(qi):
	# Execute the query
	compiled_query_results = results.Results()
	# following creates cim.sqr - subquery results which stores result of each SQL subquery
	# this is used by runsubquery to determin the final (merged) results
	cim = Cloc_info_manager(qi)
	# now have results of SQL queries on database stored in sqr
	# use that to determin result of overall query (by combining results of subqueries)
	subquery_call_string = make_subquery_call_string(qi)
	# print("%s" % subquery_call_string)
	# will be like: runsubquery(0,cim,qr) & runsubquery(1,cim,qr)
	for file_id in cim.get_file_ids():
		# specify which file to Cloc_info_manager
		cim.set_file_id(file_id)
		file_name = cim.get_file_name()
		# initialize File_result object for storing subquery results	
		qr = results.File_result(file_name, len(qi["plocs"]))
		result = eval(subquery_call_string)
		if result:
			compiled_query_results.add_file_result(qr)
	num_files_matching = compiled_query_results.get_num_files()
	print("Found %i matching files:" % num_files_matching)
	if num_files_matching > 0:
		pp.pprint( compiled_query_results.get_value() )

def do_interactive_queries():
	show_available_files()
	print("Enter query, control-d to quit")
	while True:
		try:
			query=input("> ")
		except EOFError:
			break;
		qi = parse2.parse(query)
		perform_query(qi)
	print("\nDone running all queries")

def process_command_line(query):
	# query is None (for interactive input), or a query to process from the command line
	if query is None:
		do_interactive_queries()
	else:
		qi = parse2.parse(query)
		perform_query(qi)

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
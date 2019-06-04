

# functions to generate SQL from parsed query
import parse2  # only used if testing


class SQL_maker:
	# class for generating SQL to perform query

	def __init__(self, qi):
		# qi is query information, output of parse2.
		self.qi = qi

		# qi is a dictionary, created by parse2.py.  Contents are:
		# qi['tokens'] - list of tokens, that represent expression to be put into SQL (before editing)
		# qi['ttypes'] - token types.  See parse2 for codes
		# qi['plocs'] - list of 'parent location' information.  Each entry is a dictionary with keys:
		#		path  - path to parent group or dataset
		#		range - tuple specifying start and end location of tokens in ploc (parent location) query
		#		cloc_index - index into tokens of child location(s) that are part of the query expression.
		#		cloc_parts - dict mapping clocs that have subscripts to a tuple having the main part and the subscript
		#		display_clocs - list of child locations to display (may not be in query expression)
		# Example, query:
		# (ploc1: p,q, r, (a[bar] >= 22 & b LIKE "sue") | (ploc2: t[0], m <= 14 & ploc3: x < 23))
		# qi contains:
		# {   'plocs': [   {   'cloc_index': [2, 6],
		#                      'cloc_parts': {'a[bar]': ('a', 'bar')},
		#                      'display_clocs': ['p', 'q', 'r'],
		#                      'path': 'ploc1',
		#                      'range': (1, 10)},
		#                  {   'cloc_index': [12],
		#                      'cloc_parts': {'t[0]': ('t', '0')},
		#                      'display_clocs': ['t[0]'],
		#                      'path': 'ploc2',
		#                      'range': (12, 15)},
		#                  {'cloc_index': [16], 'cloc_parts': {}, 'display_clocs': [], 'path': 'ploc3', 'range': (16, 19)}],
		#     'tokens': [   '(', '(', 'a[bar]', '>=', '22', '&', 'b', 'LIKE', '"sue"', ')', '|', '(', 'm', '<=', '14', '&', 'x',
		#                   '<', '23', ')', ')'],
		#     'ttypes': [   '(', '(', 'CLOC', 'ROP', 'NC', 'AOR', 'CLOC', 'ROP', 'SC', ')', 'AOR', '(', 'CLOC', 'ROP', 'NC',
		#                   'AOR', 'CLOC', 'ROP', 'NC', ')', ')']}

	def make_normal_sql(self, cpi):
		# generate SQL for normal query (not part of NWB 2 table)
		# cpi - current ploc index - index of ploc (subquery) to use for generating query
		self.cpi = cpi
		self.build_sql_parts()
		# for normal query, only there where needs to be modified from the common query parts
		sql_select = self.sql_parts["sql_select"]
		sql_from = self.sql_parts["sql_from"]
		sql_where = self.sql_parts["sql_where"] + self.sql_parts["sql_normal_where"]
		sql = self.merge_parts(sql_select, sql_from, sql_where)
		return sql

	def make_table_sql(self):
		# generate SQL for query of NWB 2 tables
		assert self.cpi >= 0, "make_table_sql must be called AFTER make_normal_sql"
		sql_select = self.sql_parts["sql_select"] + self.sql_parts["sql_colnames_select"]
		sql_from = self.sql_parts["sql_from"] + self.sql_parts["sql_colnames_from"]
		sql_where = self.sql_parts["sql_where"] + self.sql_parts["sql_colnames_where"]
		sql = self.merge_parts(sql_select, sql_from, sql_where)
		return sql

	def merge_parts(self, sql_select, sql_from, sql_where):
		sql = ("SELECT\n\t" + ",\n\t".join(sql_select)
			+ "\nFROM\n\t" + ",\n\t".join(sql_from)
			+ "\nWHERE\n\t" + " AND\n\t".join(sql_where))
		return sql

	def build_sql_parts(self):
		# create query parts using self.qi and self.cpi
		sql_select = ["f.id as file_id", "f.location as file"]
		sql_from = ["file as f"]
		sql_where = []
		sql_colnames_select = []
		sql_colnames_from = []
		sql_colnames_where = []
		sql_normal_where = []
		qi = self.qi
		alphabet = "abcdefghijklmnopqrstuvwxyz"  # for building name of sql variables
		# editokens stores edited version of tokens
		editokens = qi["tokens"].copy()
		# replace '&' and '|' in editokens expression with AND and OR (what is used in SQL)
		for i in range(len(qi["tokens"])):
			if qi['ttypes'][i] == 'AOR':
				assert(editokens[i] in ('&', '|')), "Expecting & or |, found %s" % editokens[i]
				editokens[i] = "AND" if editokens[i] == "&" else "OR"
		# build query parts for current parent location (ploc)
		cpi = self.cpi 	# cpi - current ploc index (subquery)
		cpi_alpha = alphabet[cpi]  # e.g. "a", "b", "c", ...   ; used to build unique alias names
		ploc_alias_base = "b" + cpi_alpha	# e.g. "ba" for 1st parent location (ploc), "bb" for 2nd ...
		parent_path_alias = "%sp" % ploc_alias_base
		parent_node_alias = "%sn" % ploc_alias_base
		sql_select.append("%s.path as parent_%s" % (parent_path_alias, cpi_alpha))	# select the parent path
		sql_select.append("%s.node_type as node_type" % parent_node_alias)
		sql_from.append("node as %s" % parent_node_alias)
		sql_from.append("path as %s" % parent_path_alias)
		# replace '*' in path with '%' for LIKE operator and remove any leading '/' for searching
		like_path = qi['plocs'][cpi]['path'].replace("*", "%").lstrip("/")
		sql_where.append("%s.path LIKE '%s'" % (parent_path_alias, like_path))
		sql_where.append("%s.id = %s.path_id" % (parent_path_alias, parent_node_alias))
		sql_where.append("f.id = %s.file_id" % parent_node_alias)
		# colnames node and name alias used to check if a group contains a NWB 2 table
		colnames_node_alias = "%sn_colnames" % ploc_alias_base
		colnames_name_alias = "%sna_colnames" % ploc_alias_base
		colnames_value_alias = "%sv_colnames" % ploc_alias_base
		sql_colnames_from.append("node as %s" % colnames_node_alias)
		sql_colnames_from.append("name as %s" % colnames_name_alias)
		sql_colnames_from.append("value as %s" % colnames_value_alias)
		sql_colnames_where.append("%s.value_id = %s.id" % (colnames_node_alias, colnames_value_alias))
		# commented out below line because do not need colnames in results
		# sql_colnames_select.append("%s.sval as %s" % (colnames_value_alias, colnames_name_alias))

		# done appending query parts for parent location (ploc), except for expression in where
		# Append query parts for each display child
		# first make list of all children to display, including display_clocs and those in expression
		clocs = qi["plocs"][cpi]["display_clocs"] + [ qi["tokens"][i] for i in qi["plocs"][cpi]["cloc_index"] ]
		# custom_call_values = [] # for storing value table elements passed to custom call for nwb 2 table
		for ic in range(len(clocs)):
			cloc = clocs[ic]  # actual name of child location
			# if cloc in qi['plocs'][cpi]['cloc_parts']:
			# 	# skip this child since it has components (is part of table).  Those managed by callback.
			# 	continue
			# add child location to select since it does not have subcomponents
			cloc_alias_base = "%s%i" % (ploc_alias_base, ic) # e.g. "ba0" for 1st parent, 1st child; bb3 -2nd parent, 4rd child
			child_node_alias = "%sn" % cloc_alias_base
			child_name_alias = "%sna" % cloc_alias_base
			child_value_alias = "%sv" % cloc_alias_base
			# get child token index if this child is in the expression
			eti = ic - len(qi["plocs"][cpi]["display_clocs"])  # expression token index
			cti = qi["plocs"][cpi]["cloc_index"][eti] if eti >= 0 else -1
			# perhaps try using case all of the time (value type 'N' will still be numeric)
			if cti >= 0:
				# this child in the expression, replace the cloc in editokens with the 'value'
				# table value for including it in the where clause
				assert (qi["ttypes"][cti] == "CLOC" and qi["ttypes"][cti+1] in("ROP", "LIKE") and
					qi["ttypes"][cti+2] in ("NC", "SC")), "tokens do not match expected values"
				is_string = qi["ttypes"][cti+2] == "SC"
				value_select = "%s.sval" % child_value_alias if is_string else "%s.nval" % child_value_alias
				editokens[cti] = value_select
				# custom_call_values.append(value_select)
			else:
				# this child is display only, not in expression.  Can't determine type of vaulue (string or number)
				value_select = "case when %s.type = 'n' then %s.nval else %s.sval end" % (
					child_value_alias, child_value_alias, child_value_alias)
			sql_select.append("'%s'" % cloc)  # include name of child location in select
			sql_select.append("%s.node_type as node_type" % child_node_alias)  # include node_type in select
			sql_select.append("%s.type as type" % child_value_alias)  # include value_type in select
			sql_select.append("%s as %s_value" % (value_select, cloc))
			sql_from.append("value as %s" % child_value_alias)
			sql_from.append("node as %s" % child_node_alias)
			sql_from.append("name as %s" % child_name_alias)
			sql_where.append("%s.parent_id = %s.id" % (child_node_alias, parent_node_alias))
			sql_where.append("%s.name_id = %s.id" % (child_node_alias, child_name_alias))
			sql_where.append("%s.name = '%s'" % (child_name_alias, cloc))
			sql_where.append("%s.id = %s.value_id" % (child_value_alias, child_node_alias))
		# done adding query parts for child locations.  Now create query expression which will
		# be added to where clause for this parent location (ploc)
		i_start = qi['plocs'][cpi]["range"][0]
		i_end = qi['plocs'][cpi]["range"][1]
		query_expression = " ".join([t for t in editokens[i_start:i_end]])
		sql_normal_where.append('(' + query_expression + ')')
		# for normal query, parent node must not be group of type "G" (e.g. group with NWB 2 table)
		sql_normal_where.append("\t%s.node_type != 'G'" % parent_node_alias)
		# custom_call = "check_nwb2_table(%i, %s.path, %s)" % (cpi, parent_path_alias, ", ".join(custom_call_values)) # need to fill this in to include cloc values
		# ploc_exp_where = []
	# 	ploc_exp_where.append('''
	# case
	# 	when
	# 		%s.parent_id = %s.id and
	# 		''' % (colnames_node_alias, parent_node_alias)
		# create part for table query (selecting colnames attribute; constraint on parent node to be type 'G')
		sql_colnames_where.append("\t%s.parent_id = %s.id" % (colnames_node_alias, parent_node_alias))
		sql_colnames_where.append("\t%s.node_type = 'G'" % parent_node_alias)
		sql_colnames_where.append("\t%s.node_type = 'a'" % colnames_node_alias)
		sql_colnames_where.append("\t%s.name_id = %s.id" % (colnames_node_alias, colnames_name_alias))
		sql_colnames_where.append("\t%s.name = 'colnames'" % colnames_name_alias)

		# save the query parts:
		self.sql_parts = {
			"sql_select": sql_select,
			"sql_from": sql_from,
			"sql_where": sql_where,
			"sql_normal_where": sql_normal_where,
			"sql_colnames_select": sql_colnames_select,
			"sql_colnames_from": sql_colnames_from,
			"sql_colnames_where": sql_colnames_where
		}

		# ploc_exp_where.append("\tcase")
		# ploc_exp_where.append("\t\twhen")
		# ploc_exp_where.append("\t\t\t%s.parent_id = %s.id and" % (colnames_node_alias, parent_node_alias))		
		# ploc_exp_where.append("\t\t\t%s.node_type = 'a' and" % colnames_node_alias)
		# ploc_exp_where.append("\t\t\t%s.name_id = %s.id and" % (colnames_node_alias, colnames_name_alias))
		# ploc_exp_where.append("\t\t\t%s.name = 'colnames'" % colnames_name_alias)
		# ploc_exp_where.append("\t\tthen")
		# ploc_exp_where.append("\t\t\t%s" % custom_call)
		# ploc_exp_where.append("\t\telse")
		# ploc_exp_where.append("\t\t\t%s.id = 1 and" % colnames_node_alias)			
		# ploc_exp_where.append("\t\t\t%s.id = 1 and" % colnames_name_alias)
		# ploc_exp_where.append("\t\t\t( %s )" % query_expression)		
		# ploc_exp_where.append("\tend")
		# # ploc_expression_where.append("\n".join(ploc_exp_where))
		# sql_where.append("\n".join(ploc_exp_where))
		# finally, create the sql command
		# sql = ",\n\t".join(sql_select) + "\n" + ",\n\t".join(sql_from) + "\nWHERE\n\t" + " AND\n\t".join(sql_where)
		# return sql










# def path_query():
# 	# path_query generates the paths from all root nodes.  Hopefully, the
# 	# optomizer will enable this to be done effeciently
# 	# If not, this could be replaced by a table storing all of the paths
# 	# explicitly
# 	path_query = '''
#     ( WITH RECURSIVE tree(node_id, node_path) AS (
#     SELECT
#         n.id, ''  -- select all root nodes
#         from node n
#         where n.parent_id is NULL
#     UNION ALL
#         SELECT n.id, tree.node_path || '/' || p.name
#         FROM node n, prenom p
#         JOIN tree on tree.node_id = n.parent_id
#         WHERE n.prenom_id= p.id
#     ) select node_id, node_path from tree)
#     ''';
#     return path_query

# def make_like_path(star_path):
# 	# replace any "*" characters in path with %.  Removing any leading /"
# 		like_path = star_path.replace("*", "%").lstrip("/")

# 	if len(like_path) == 0 or like_path[0] not in ('/', '%'):
# 		like_path = '/' + like_path
# 	return like_path

# def make_value_select(child_value_alias):
# 	value_select = "case when %s.type = "n" then %s.nval else %s.sval end" % (
# 		child_value_alias, child_value_alias, child_value_alias)
# 	return value_select

# def get_search_criteria(cpi, qi):
# 	# get sc (search_criteria) for finding hdf5 group or dataset to perform search
# 	# cpi - current ploc index
# 	# qi - query information
# 	# Returns:
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

def make_sql_old(qi):
	# generate sql to perform query
	# qi is a dictionary, created by parse2.py.  Contents are:
	# qi['tokens'] - list of tokens, that represent expression to be put into SQL (before editing)
	# ti['ttypes'] - token types.  See parse2 for codes
	# ti['plocs'] - list of 'parent location' information.  Each entry is a dictionary with keys:
	#		path  - path to parent group or dataset
	#		range - tuple specifying start and end location of tokens in ploc (parent location) query
	#		cloc_index - index into tokens of child location(s) that are part of the query expression.
	#		cloc_parts - dict mapping clocs that have subscripts to a tuple having the main part and the subscript
	#		display_clocs - list of child locations to display (may not be in query expression)
	# Example, query:
# (ploc1: p,q, r, (a[bar] >= 22 & b LIKE "sue") | (ploc2: t[0], m <= 14 & ploc3: x < 23))
# {   'plocs': [   {   'cloc_index': [2, 6],
#                      'cloc_parts': {'a[bar]': ('a', 'bar')},
#                      'display_clocs': ['p', 'q', 'r'],
#                      'path': 'ploc1',
#                      'range': (1, 10)},
#                  {   'cloc_index': [12],
#                      'cloc_parts': {'t[0]': ('t', '0')},
#                      'display_clocs': ['t[0]'],
#                      'path': 'ploc2',
#                      'range': (12, 15)},
#                  {'cloc_index': [16], 'cloc_parts': {}, 'display_clocs': [], 'path': 'ploc3', 'range': (16, 19)}],
#     'tokens': [   '(', '(', 'a[bar]', '>=', '22', '&', 'b', 'LIKE', '"sue"', ')', '|', '(', 'm', '<=', '14', '&', 'x',
#                   '<', '23', ')', ')'],
#     'ttypes': [   '(', '(', 'CLOC', 'ROP', 'NC', 'AOR', 'CLOC', 'ROP', 'SC', ')', 'AOR', '(', 'CLOC', 'ROP', 'NC',
#                   'AOR', 'CLOC', 'ROP', 'NC', ')', ')']}
	sql_select = ["""SELECT
	f.location as file"""]
	sql_from = ["""FROM
	file as f"""]
	sql_where = []
	# ploc_expression_where = []	# for storing where clause expressions for each parent location (ploc)
	alphabet = "abcdefghijklmnopqrstuvwxyz"  # for building name of sql variables
	# editokens stores edited version of tokens
	editokens = qi["tokens"].copy()
	# replace '&' and '|' in editokens expression with AND and OR (what is used in SQL)
	for i in range(len(qi["tokens"])):
		if qi['ttypes'][i] == 'AOR':
			assert(editokens[i] in ('&', '|')), "Expecting & or |, found %s" % editokens[i]
			editokens[i] = "AND" if editokens[i] == "&" else "OR"
	# start loop through each parent location (ploc)
	for cpi	in range(len(qi['plocs'])):  # cpi - current ploc index, iterate over each ploc (subquery)
		cpi_alpha = alphabet[cpi]  # e.g. "a", "b", "c", ...   ; used to build unique alias names
		ploc_alias_base = "b" + cpi_alpha	# e.g. "ba" for 1st parent location (ploc), "bb" for 2nd ...
		parent_path_alias = "%sp" % ploc_alias_base
		parent_node_alias = "%sn" % ploc_alias_base
		sql_select.append("%s.path as parent_%s" % (parent_path_alias, cpi_alpha))	# select the parent path
		sql_from.append("node as %s" % parent_node_alias)
		sql_from.append("path as %s" % parent_path_alias)
		# replace '*' in path with '%' for LIKE operator and remove any leading '/' for searching
		like_path = qi['plocs'][cpi]['path'].replace("*", "%").lstrip("/")
		sql_where.append("%s.path LIKE '%s'" % (parent_path_alias, like_path))
		sql_where.append("%s.id = %s.path_id" % (parent_path_alias, parent_node_alias))
		sql_where.append("f.id = %s.file_id" % parent_node_alias)
		# colnames node and name alias used to check if a group contains a NWB 2 table
		colnames_node_alias = "%sn_colnames" % ploc_alias_base
		colnames_name_alias = "%sna_colnames" % ploc_alias_base
		sql_from.append("node as %s" % colnames_node_alias)
		sql_from.append("name as %s" % colnames_name_alias)
		# done appending query parts for parent location (ploc), except for expression in where
		# Append query parts for each display child
		# first make list of all children to display, including display_clocs and those in expression
		clocs = qi["plocs"][cpi]["display_clocs"] + [ qi["tokens"][i] for i in qi["plocs"][cpi]["cloc_index"] ]
		custom_call_values = [] # for storing value table elements passed to custom call for nwb 2 table
		for ic in range(len(clocs)):
			cloc = clocs[ic]  # actual name of child location
			if cloc in qi['plocs'][cpi]['cloc_parts']:
				# skip this child since it has components (is part of table).  Those managed by callback.
				# TODO: need to include these, and check to make sure not duplicate values
				continue
			# add child location to select since it does not have subcomponents
			cloc_alias_base = "%s%i" % (ploc_alias_base, ic) # e.g. "ba0" for 1st parent, 1st child; bb3 -2nd parent, 4rd child
			child_node_alias = "%sn" % cloc_alias_base
			child_name_alias = "%sna" % cloc_alias_base
			child_value_alias = "%sv" % cloc_alias_base
			# get child token index if this child is in the expression
			eti = ic - len(qi["plocs"][cpi]["display_clocs"])  # expression token index
			cti = qi["plocs"][cpi]["cloc_index"][eti] if eti >= 0 else -1
			if cti >= 0:
				# this child in the expression, replace the cloc in editokens with the 'value'
				# table value for including it in the where clause
				assert (qi["ttypes"][cti] == "CLOC" and qi["ttypes"][cti+1] in("ROP", "LIKE") and
					qi["ttypes"][cti+2] in ("NC", "SC")), "tokens do not match expected values"
				is_string = qi["ttypes"][cti+2] == "SC"
				value_select = "%s.sval" % child_value_alias if is_string else "%s.nval" % child_value_alias
				editokens[cti] = value_select
				custom_call_values.append(value_select)
			else:
				# this child is display only, not in expression.  Can't determine type of vaulue (string or number)
				value_select = "case when %s.type = 'n' then %s.nval else %s.sval end" % (
					child_value_alias, child_value_alias, child_value_alias)
			sql_select.append("%s as %s" % (value_select, cloc))
			sql_from.append("value as %s" % child_value_alias)
			sql_from.append("node as %s" % child_node_alias)
			sql_from.append("name as %s" % child_name_alias)
			sql_where.append("%s.parent_id = %s.id" % (child_node_alias, parent_node_alias))
			sql_where.append("%s.name_id = %s.id" % (child_node_alias, child_name_alias))
			sql_where.append("%s.name = '%s'" % (child_name_alias, cloc))
			sql_where.append("%s.id = %s.value_id" % (child_value_alias, child_node_alias))
		# done adding query parts for child locations.  Now create query expression which will
		# be added to where clause for this parent location (ploc)
		i_start = qi['plocs'][cpi]["range"][0]
		i_end = qi['plocs'][cpi]["range"][1]
		query_expression = " ".join([t for t in editokens[i_start:i_end]])
		custom_call = "check_nwb2_table(%i, %s.path, %s)" % (cpi, parent_path_alias, ", ".join(custom_call_values)) # need to fill this in to include cloc values
		ploc_exp_where = []
	# 	ploc_exp_where.append('''
	# case
	# 	when
	# 		%s.parent_id = %s.id and
	# 		''' % (colnames_node_alias, parent_node_alias)
		ploc_exp_where.append("\tcase")
		ploc_exp_where.append("\t\twhen")
		ploc_exp_where.append("\t\t\t%s.parent_id = %s.id and" % (colnames_node_alias, parent_node_alias))		
		ploc_exp_where.append("\t\t\t%s.node_type = 'a' and" % colnames_node_alias)
		ploc_exp_where.append("\t\t\t%s.name_id = %s.id and" % (colnames_node_alias, colnames_name_alias))
		ploc_exp_where.append("\t\t\t%s.name = 'colnames'" % colnames_name_alias)
		ploc_exp_where.append("\t\tthen")
		ploc_exp_where.append("\t\t\t%s" % custom_call)
		ploc_exp_where.append("\t\telse")
		ploc_exp_where.append("\t\t\t%s.id = 1 and" % colnames_node_alias)			
		ploc_exp_where.append("\t\t\t%s.id = 1 and" % colnames_name_alias)
		ploc_exp_where.append("\t\t\t( %s )" % query_expression)		
		ploc_exp_where.append("\tend")
		# ploc_expression_where.append("\n".join(ploc_exp_where))
		sql_where.append("\n".join(ploc_exp_where))
	# finally, create the sql command
	sql = ",\n\t".join(sql_select) + "\n" + ",\n\t".join(sql_from) + "\nWHERE\n\t" + " AND\n\t".join(sql_where)
	return sql

			# if this child is in the expression, replace the cloc in editokens with the value
			#  table value for including in the where clause



	# query_sql_expression = "( %s )" % " ".join([t for t in editokens if t])
	# # add in query components needed to check for nwb2 tables
	# sql_from.append("")

	# # ?? where exactly should case be located -- at the ploc (parent) level

	# sql_where.append("( %s )" % " ".join(editokens))
	# # finally, create the sql command
	# sql = ",\n\t".join(sql_select) + "\n" + ",\n\t".join(sql_from) + "\nWHERE\n\t" + " AND\n\t".join(sql_where)
	# return sql

# need to make where expression like this:
'''
	case
		when
			-- colnames attribute is present
			-- parent_node.type = 'g'
			-- node_colnames.parent_id = parent_node.id
			-- node_colnames.type = "a"  -- attribute
			-- node_colnames.name_id = colnames_name.id
			-- colnames_name.name = "colnames"
		then
			-- call function
			-- check_nwb2_table(
			--   cpi, -- current ploc index
			--   cloc1 val, cloc2 val, ...
			-- )
			-- return 1 if found value (save in qr[cpi])
			-- return 0 if did not find value
			-- Q: ? what is returned in normal sql variables if value found ?
			-- A:	The full values (as a string), not individual values
			--		can maybe fix to use conditional so return null if function called
		else
			-- constrain all colnames variables to be one row
			node_colnames.id = 1
			colnames_name.name = 1
	end
-- query used in previous testing:
	case
		when
		  n2_colnames.parent_id = n1_e.id and
		  n2_colnames.path_id = p2_colnames.id and
		  n2_colnames.node_type = "a" and
		  p2_colnames.name LIKE "%/colnames" and
		  v_st1.type = "N" and
		  v_st1.idx =  s2_st.id
	   then
		  cust(s2_st.value, "test constant")
	   else
		  v_st1.type = "n" and
		  s2_st.id = 1 and -- constrain to one row even though not used
		  n2_colnames.id = 1 and -- constrain to one row even though not used
		  p2_colnames.id = 1 -- constrain to one row even though not used
	end
'''



	# tokens = qi["tokens"]
	# ttypes = qi["ttypes"]
	# # warning: plocs here used as single tuple in ti["plocs"] (was named "current_ploc" in parse function)
	# sql_select = ["""select
	# fp.name as file"""]
	# sql_from = ["""from
	# file as f,
	# prenom as fp"""]
	# sql_where = ["""where
	# f.prenom_id = fp.id"""]
	# alphabet = "abcdefghijklmnopqrstuvwxyz"  # for building name of sql variables
	# for ipl in range(len(qi['plocs'])):		# iterate over ploc locations
	# 	plocs = qi['plocs'][ipl]
	# 	ploc = plocs[0]   # name of parent location
	# 	# (ploc, ploc_node_type) = get_node_type(ploc, "group")	# default is group
	# 	# assert ploc_node_type != "attribute", "Cannot specify parent location node as attribute (A): %s" % ploc
	# 	ipl_alpha = alphabet[ipl]  # e.g. "a", "b", "c", ...
	# 	ploc_alias_base = "b" + ipl_alpha	# e.g. "ba" for 1st parent, "bb" for 2nd parent, ...
	# 	sql_select.append("%sp.name as group_%s" % (ploc_alias_base, ipl_alpha))
	# 	sql_from.append("node as %sg" % ploc_alias_base)
	# 	sql_from.append("path as %sp" % ploc_alias_base)
	# 	sql_where.append("%sg.path_id = %sp.id" % (ploc_alias_base, ploc_alias_base))
	# 	ppat = get_parent_pattern(ploc)
	# 	if ppat:
	# 		# include search pattern for parent group
	# 		sql_where.append("%sp.name LIKE '%s'" % (ploc_alias_base, ppat))
	# 	sql_where.append("%sg.file_id = f.id" % ploc_alias_base) 
	# 	for ic in range(1, len(plocs)):
	# 		cti = plocs[ic]  # child token index
	# 		cloc_alias_base = "%s%i" % (ploc_alias_base, ic) # e.g. "ba1" for 1st parent, 1st child; bb3 -2nd parent, 3rd child
	# 		sql_select.append("%sp.name as dataset_%s%i" % (cloc_alias_base, ipl_alpha, ic))
	# 		# is string if this cloc variable is being compared to a string constant
	# 		# check constant on either side of adjancent relational operator
	# 		isstring = (cti < len(tokens)-2 and ttypes[cti+1] == "ROP" and ttypes[cti+2] == "SC") or (
	# 				cti > 1 and ttypes[cti-1] == "ROP" and ttypes[cti-2] == "SC")
	# 		if isstring:
	# 			sql_select.append("%ss.value as %s%i_value" % (cloc_alias_base, ipl_alpha, ic))
	# 		else:
	# 			sql_select.append("%sv.nval as %s%i_value" % (cloc_alias_base, ipl_alpha, ic))
	# 		sql_from.append("node as %sd" % cloc_alias_base)
	# 		sql_from.append("path as %sp" % cloc_alias_base)
	# 		sql_from.append("value as %sv" % cloc_alias_base)
	# 		if isstring:
	# 			sql_from.append("string as %ss" % cloc_alias_base)
	# 			sql_where.append("%sv.str_id = %ss.id" % (cloc_alias_base, cloc_alias_base))
	# 		sql_where.append("%sd.parent_id = %sg.id" % (cloc_alias_base, ploc_alias_base))
	# 		sql_where.append("%sd.path_id = %sp.id" % (cloc_alias_base, cloc_alias_base))
	# 		sql_where.append("%sd.value_id = %sv.id" % (cloc_alias_base, cloc_alias_base))
	# 		sql_where.append("%sp.name LIKE '%s'" % (cloc_alias_base, "%" + tokens[cti]))
	# 		# replace string in tokens with sql to retrieve value, either numeric or string
	# 		if isstring:
	# 			tokens[cti] = "%ss.value" % cloc_alias_base
	# 		else:
	# 			tokens[cti] = "%sv.nval" % cloc_alias_base
	# # done building sql_select, sql_from and sql_where for parent and child datasets
	# # Now, add in expression from tokens
	# sql_where.append("( %s )" % " ".join(tokens))
	# # finally, create the sql command
	# sql = ",\n\t".join(sql_select) + "\n" + ",\n\t".join(sql_from) + "\n" + " AND\n\t".join(sql_where)
	# return sql


test_queries = """
/ploc_a: cloc_a1 <= 789 & (cloc_a2 >= 200 | cloc_a3 <= 100) | ploc_b: cloc_b1 >= 20 & cloc_b2 LIKE "Name: Smith" & ploc_c: cloc_c1 >= "34 ( : )"
/general/subject: (age LIKE "3 months 16 days" & species LIKE "Mus musculu") & /:file_create_date LIKE "2017-04" & /epoch : start_time < 150
/general/subject: (age LIKE "3 months 16 days" & species LIKE "Mus musculu") & /:file_create_date LIKE "2017-04"
/file_create_date LIKE "2017-04" & epochs: start_time>200 & stop_time<250
epochs: start_time>200 & stop_time<250
/file_create_date LIKE "2017-04"
epochs:((start_time>200 & stop_time<250) | (start_time > 1600 & stop_time < 1700))
epochs:(start_time>200 & stop_time<250) | epochs : (start_time > 1600 & stop_time < 1700)
epochs: start_time>200 & stop_time<250 & /file_create_date LIKE "2017-04"
epochs: start_time>200 & file_create_date LIKE "2017-04"
"""
test_queries = """
/general/subject/: (age LIKE "3 months 16 days" & species LIKE "Mus musculu") & /:file_create_date LIKE "2017-04" & /epochs : start_time < 150
"""

def main():
	global test_queries;
	queries = test_queries.splitlines()
	for query in queries:
		if query:
			print ("query=%s"% query)
			qi = parse2.parse(query)
			sql_maker = SQL_maker(qi)
			for cpi in range(len(qi["plocs"])):
				print("ploc %i, normal sql:" % cpi)
				sql = sql_maker.make_normal_sql(cpi)
				print("%s" % sql)
				print("ploc %i, table sql:" % cpi)
				sql = sql_maker.make_table_sql()
				print("%s" % sql)

if __name__ == "__main__":
	main()

# function to generate SQL from parsed query


def make_sql(qi, cpi, query_type):
	# create query parts
	# qi (query information, output of parse.parse)
	# cpi (current ploc index, same as subquery index)
	# query_type, must be either:
	#  - "normal" indicates normal query (not NWB 2 table groups)
	#  - "table"  NWB 2 table group query
	assert query_type in ("normal", "table")
	is_normal_query = query_type == "normal"
	sql_select = ["f.id as file_id", "f.location as file"]
	sql_from = ["file as f"]
	sql_where = []
	sql_colnames_select = []
	sql_colnames_from = []
	sql_colnames_where = []
	sql_normal_where = []
	alphabet = "abcdefghijklmnopqrstuvwxyz"  # for building name of sql variables
	# editokens stores edited version of tokens
	editokens = qi["tokens"].copy()
	# replace '&' and '|' in editokens expression with AND and OR (what is used in SQL)
	for i in range(len(qi["tokens"])):
		if qi['ttypes'][i] == 'AOR':
			assert(editokens[i] in ('&', '|')), "Expecting & or |, found %s" % editokens[i]
			editokens[i] = "AND" if editokens[i] == "&" else "OR"
	# build query parts for current parent location (ploc)
	cpi_alpha = alphabet[cpi]  # e.g. "a", "b", "c", ...   ; used to build unique alias names
	ploc_alias_base = "b" + cpi_alpha	# e.g. "ba" for 1st parent location (ploc), "bb" for 2nd ...
	parent_path_alias = "%sp" % ploc_alias_base
	parent_node_alias = "%sn" % ploc_alias_base
	sql_select.append("%s.path as parent_%s" % (parent_path_alias, cpi_alpha))	# select the parent path
	sql_select.append("%s.node_type as node_type" % parent_node_alias)
	sql_from.append("node as %s" % parent_node_alias)
	sql_from.append("path as %s" % parent_path_alias)
	# replace '*' in path with '%' for LIKE operator and remove any leading or trailing '/' for searching
	like_path = qi['plocs'][cpi]['path'].replace("*", "%").strip("/")
	sql_where.append("%s.path LIKE '%s'" % (parent_path_alias, like_path))
	sql_where.append("%s.id = %s.path_id" % (parent_path_alias, parent_node_alias))
	sql_where.append("f.id = %s.file_id" % parent_node_alias)
	# colnames node and name alias used to check if a group contains a NWB 2 table
	if not is_normal_query:
		colnames_node_alias = "%sn_colnames" % ploc_alias_base
		colnames_name_alias = "%sna_colnames" % ploc_alias_base
		colnames_value_alias = "%sv_colnames" % ploc_alias_base
		sql_from.append("node as %s" % colnames_node_alias)
		sql_from.append("name as %s" % colnames_name_alias)
		sql_from.append("value as %s" % colnames_value_alias)
		sql_where.append("%s.value_id = %s.id" % (colnames_node_alias, colnames_value_alias))
		# commented out below line because do not need colnames in results.  Table columns are
		# indicated by value_table value_type in ('I', 'F', 'c', or 'M')
		# sql_select.append("%s.sval as %s" % (colnames_value_alias, colnames_name_alias))
	# done appending query parts for parent location (ploc)
	# Append query parts for each display child
	# first make list of all children to display, including display_clocs and those in expression
	clocs = qi["plocs"][cpi]["display_clocs"] + [ qi["tokens"][i] for i in qi["plocs"][cpi]["cloc_index"] ]
	# following for keeping track of which child locations (clocs) are included on the generated sql.
	# It maps cloc to the child_value_alias so the value can be used again in the expression.
	# This is needed to be sure some clocs are not included multiple times which could happen with
	# different subscripts since the subscripts are ignored when doing the SQL query.  Also a given
	# cloc may appear more than once in an expression, such as the query:
	# '/epochs/* : (start_time>100 & start_time<110)'
	child_value_aliases = {}
	for ic in range(len(clocs)):
		cloc = clocs[ic]  # actual name of child location
		if cloc in qi['plocs'][cpi]['cloc_parts']:
			# this has a subscript, replace by name without subscript
			cloc = qi['plocs'][cpi]['cloc_parts'][cloc][0]
		have_child_value_alias = cloc in child_value_aliases
		if not have_child_value_alias:
			cloc_alias_base = "%s%i" % (ploc_alias_base, ic) # e.g. "ba0" for 1st parent, 1st child; bb3 -2nd parent, 4rd child
			child_node_alias = "%sn" % cloc_alias_base
			child_name_alias = "%sna" % cloc_alias_base
			child_value_alias = "%sv" % cloc_alias_base
			child_value_aliases[cloc] = child_value_alias
		else:
			child_value_alias = child_value_aliases[cloc]
		# get child token index if this child is in the expression
		eti = ic - len(qi["plocs"][cpi]["display_clocs"])  # expression token index
		cti = qi["plocs"][cpi]["cloc_index"][eti] if eti >= 0 else -1
		if cti >= 0 and is_normal_query:
			# replace the cloc in editokens with the 'value'
			# table value for including it in the where clause
			assert (qi["ttypes"][cti] == "CLOC" and qi["ttypes"][cti+1] in("ROP", "LIKE") and
				qi["ttypes"][cti+2] in ("NC", "SC")), "tokens do not match expected values"
			is_string = qi["ttypes"][cti+2] == "SC"
			value_select = "%s.sval" % child_value_alias if is_string else "%s.nval" % child_value_alias
			editokens[cti] = value_select
			# check for string constant, make sure has wildcard prefix and suffix for SQL match
			# replace operator with LIKE if is not like so SQL search will find item
			if qi["ttypes"][cti+2] == "SC":
				sc = editokens[cti+2]
				assert sc[0] in ("'", '"') and sc[-1] == sc[0], "string constant not in quotes: %s" % sc
				assert len(sc) > 2
				sc_before = sc
				if sc[1] != '%':
					sc = "%s%%%s" % (sc[0], sc[1:])
				if sc[-2] != "%":
					sc = "%s%%%s" % (sc[0:-1], sc[-1])
				# print("sc before: %s, after:%s" % (sc_before, sc))
				if sc_before != sc:
					# replace string constant with wildcard version
					editokens[cti+2] = sc
				# check if operator is not LIKE
				op = editokens[cti+1]
				assert op in ('LIKE','<','>','<=','>=','==', '!='), "invalid operator before string: %s" % op
				if op != "LIKE":
					editokens[cti+1] = "LIKE"

			if have_child_value_alias:
				# now that have edited the tokens, if already processed this child, no need to do anything else
				# possible todo: check for mismatch in child use, e.g. used as both string and number in expression
				continue
		else:
			# this child is display only, not in expression, or it's a table query. Either way,
			# Can't determine type of value (string or number)
			if have_child_value_alias:
				# value is already selected, no need to select it again
				continue
			value_select = "case when %s.type in ('i', 'f') then %s.nval else %s.sval end" % (
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
	if is_normal_query:
		i_start = qi['plocs'][cpi]["range"][0]
		i_end = qi['plocs'][cpi]["range"][1]
		if i_start < i_end:
			# expression present
			query_expression = " ".join([t for t in editokens[i_start:i_end]])
		else:
			# expression not present, must be displaying values only.  replace expression with 1 (true)
			query_expression = "1"
		sql_where.append('(' + query_expression + ')')
		# for normal query, parent node must not be group of type "G" (e.g. group with NWB 2 table)
		sql_where.append("\t%s.node_type != 'G'" % parent_node_alias)
	else:
		# create part for table query (selecting colnames attribute; constraint on parent node to be type 'G')
		sql_where.append("\t%s.parent_id = %s.id" % (colnames_node_alias, parent_node_alias))
		sql_where.append("\t%s.node_type = 'G'" % parent_node_alias)
		sql_where.append("\t%s.node_type = 'a'" % colnames_node_alias)
		sql_where.append("\t%s.name_id = %s.id" % (colnames_node_alias, colnames_name_alias))
		sql_where.append("\t%s.name = 'colnames'" % colnames_name_alias)

	# finally, generate the SQL query
	sql = ("SELECT\n\t" + ",\n\t".join(sql_select)
		+ "\nFROM\n\t" + ",\n\t".join(sql_from)
		+ "\nWHERE\n\t" + " AND\n\t".join(sql_where))
	return sql



test_queries = """
/general/subject/: (age LIKE "3 months 16 days" & species LIKE "Mus musculu") & /:file_create_date LIKE "2017-04" & /epochs : start_time < 150
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
*: colnames
/epochs/* : tags == 'performing' & tags LIKE "ion trial" & start_time == 2.284463
"""
test_queries = """
general/subject: species == "mouse"
*:(neurodata_type == "RoiResponseSeries")
units: (id > -1 & location == "CA3" & quality > 0.8)
"""

def main():
	import parse as parse  # only used if testing
	global test_queries;
	queries = test_queries.splitlines()
	for query in queries:
		if query:
			print ("query=%s"% query)
			qi = parse.parse(query)
			for cpi in range(len(qi["plocs"])):
				for query_type in ("normal", "table"):
					sql = make_sql(qi, cpi, query_type)
					print("ploc %i, %s sql:\n%s" % (cpi, query_type, sql))

if __name__ == "__main__":
	main()

import re
import shlex

# following worked:
# /general/subject=(age LIKE "3 months 16 days" & species LIKE "Mus musculu") & /=(file_create_date LIKE "2017-04")

test_queries = """
/general/subject/: (age LIKE "3 months 16 days" & species LIKE "Mus musculu") & /:file_create_date LIKE "2017-04" & /epochs : start_time < 150
"""
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



# def parse(query):
# 	pattern = re.compile(r"""\s*                 # whitespace
#                              (?P<ploc>[^: ]*)      # quoted name
#                              \s*:\s*\(			# colon and opening "("
#                              \s*(?P<cloc>[^ <>=]+)	# cloc - child location
#                              \s*(?P<op>(<=|>=|==|<|>|LIKE))	# operator
#                              \s*(?P<const>(?:[-+]?[0-9]*\.?[0-9]+|"[^"]*"|'[^']*')) # number or string constant
#                              \s*(?P<)
#                              ?P<n1>.*?)   # whitespace, next bar, n1
#                              \s*\|\s*(?P<n2>.*?)   # whitespace, next bar, n2
#                              \s*\|""", re.VERBOSE)
#     match = pattern.match(s)

def parse(query):
	print("parsing: '%s'" % query)
	# raw_tokens = list(shlex.shlex(query, punctuation_chars=True))  # original, did not split "))"
	raw_tokens = list(shlex.shlex(query, punctuation_chars="="))  # seems to work, splits "))", keeps "=="
	# raw_tokens = list(shlex.shlex(query))  # fails, splits words on slash
	# list of tuples, each tuple has index of parent locations (ploc) and 
	# indexes of child locations for the parent locaton
	plocs = []
	# list with current ploc as fist element and index of clocs as subsequent elements
	current_ploc = [""]
	# processed tokens, ready to be used in SQL statement
	tokens = []
	ttypes = []  # token types; "ROP" - relational operator, "(", ")", "CLOC" - child location,
		# "NC" -numeric constant, "SC" - string constant, "AOR" - and / or  
	i = 0	# index of raw token
	while i < len(raw_tokens):
		token = raw_tokens[i]
		next_token = raw_tokens[i+1] if i+1 < len(raw_tokens) else None
		if next_token == ":":
			# found ploc (parent location).  Save any previous, start new current_ploc
			if len(current_ploc) > 1:
				plocs.append(current_ploc)
			current_ploc = [token]
			i += 2  # skip ":"
		elif (token == "<" or token == ">") and next_token == "=":
			# found <= or >=
			ttypes.append("ROP")
			tokens.append(token + next_token)
			i += 2  # skip "="
		elif token in ("<", ">", "==", "LIKE"):
			# found relational operator, copy directly
			ttypes.append("ROP")
			tokens.append(token)
			i += 1
		elif token in ("(", ")", "[", "]"):
			# found parentheses or brackets, copy directly
			ttypes.append(token)
			tokens.append(token)
			i += 1
		elif token in ("&", "|"):
			ttypes.append("AOR")
			# replace & and | with AND, OR for SQL
			token = "AND" if token == "&" else "OR"
			tokens.append(token)
			i += 1
		elif token[0] in ("'", '"'):
			# found string constant
			ttypes.append("SC")
			tokens.append(token)
			i += 1
		elif token[0] == ",":
			# comma indicates cloc value to display, but not compute with
			ttypes.append("COMMA")
			tokens.append(token)
			i += 1
		elif re.match("^-?[0-9]*\.?[0-9]*$", token):
			# found numeric constant
			ttypes.append("NC")
			tokens.append(token)
			i += 1
		else:
			# must be a child location, save index to it:
			ttypes.append("CLOC")
			current_ploc.append(len(tokens))
			tokens.append(token)
			i += 1
	# Save any current parent location
	if len(current_ploc) > 1:
		plocs.append(current_ploc)
	print("plocs=%s" % plocs)
	print("tokens=%s" % tokens)
	print("ttypes=%s" % ttypes)
	print("")
	# store everything in a dictionary
	ti = {"tokens":tokens, "ttypes":ttypes, "plocs":plocs, "query":query}
	return ti

def get_parent_pattern(ploc):
	# input is string before : in query
	# possible ploc cases:
	#	/ploc  - begin with slash, not at end.  Anchor to root.  Allow any location under. pattern = "/ploc%"
	#	ploc/  - slash at end, not at front.  Item directly under ploc which may be anywhere.  pat = "%ploc"
	#	/ploc/ - slash at front and end.  Anchor directly under item.  pat="ploc"
	#	ploc   - slash not at start or end.  Find ploc anywhere in tree. pat="%ploc%"
	#	/      - item following is directly under root.  pat=""
	#	* or empty     - item following is anywhere in tree.  pat not used.
	# In summary:
	#	/ by itself, pat=""
	#	* or empty - ignore
	#	leading slash, no trailing slash: append "%" to suffix
	#	trailing slash, no leading slash, prepend "%" to start
	#	leading and trailing slash, don't prepend anything
	#	no leading slash, no trailing slash -- append "%" to both leading and trailing
	if ploc == "" or ploc == "*":
		pattern = None
	elif ploc == "/":
		pattern = ""
	else:
		slash_at_start = ploc[0] == "/"
		slash_at_end = ploc[-1] == "/"
		pattern = ploc.strip("/")
		if not slash_at_start:
			pattern = "%" + pattern
		if not slash_at_end:
			pattern += "%"
	return pattern

def NOT_USED_get_node_type(loc, default):
	# implements quick way to specify group, dataset or attribute by appending "G", "D" or "A" to location name
	codes = {"G": "group", "D": "dataset", "A": "attribute"}
	assert default in codes.values(), "get_node_type default must be one of: '%s', found '%s'" % (code.values(), default)
	if len(loc) > 0:
		if loc[-1] in codes.keys():
			node_type = codes(loc[-1])
			loc = loc[0:-1]	# strip off suffix code character
		else:
			node_type = default
	return (loc, node_type)

def make_sql(ti):
	# generate sql to perform query
	# imputs are:
	# ti['tokens'] - list of tokens, that represent expression to be put into SQL
	# ti['ttypes'] - token types.  See parse for codes
	# ti['plocs'] - list of tuples.  Each tuple has info about one "ploc" (parent location, i.e. name before ":")
	#	format is: (<ploc_name> <token_index_1> <token_index_2> ....), where each <token_index_N> is the
	# 		index of a child location (e.g. dataset name) to search for within the parent.
	tokens = ti["tokens"]
	ttypes = ti["ttypes"]
	# warning: plocs here used as single tuple in ti["plocs"] (was named "current_ploc" in parse function)
	sql_select = ["""select
	fp.name as file"""]
	sql_from = ["""from
	file as f,
	path as fp"""]
	sql_where = ["""where
	f.path_id = fp.id"""]
	alphabet = "abcdefghijklmnopqrstuvwxyz"  # for building name of sql variables
	for ipl in range(len(ti['plocs'])):
		plocs = ti['plocs'][ipl]
		ploc = plocs[0]   # name of parent location
		# (ploc, ploc_node_type) = get_node_type(ploc, "group")	# default is group
		# assert ploc_node_type != "attribute", "Cannot specify parent location node as attribute (A): %s" % ploc
		ipl_alpha = alphabet[ipl]  # e.g. "a", "b", "c", ...
		ploc_alias_base = "b" + ipl_alpha	# e.g. "ba" for 1st parent, "bb" for 2nd parent, ...
		sql_select.append("%sp.name as group_%s" % (ploc_alias_base, ipl_alpha))
		sql_from.append("node as %sg" % ploc_alias_base)
		sql_from.append("path as %sp" % ploc_alias_base)
		sql_where.append("%sg.path_id = %sp.id" % (ploc_alias_base, ploc_alias_base))
		ppat = get_parent_pattern(ploc)
		if ppat:
			# include search pattern for parent group
			sql_where.append("%sp.name LIKE '%s'" % (ploc_alias_base, ppat))
		sql_where.append("%sg.file_id = f.id" % ploc_alias_base) 
		for ic in range(1, len(plocs)):
			cti = plocs[ic]  # child token index
			cloc_alias_base = "%s%i" % (ploc_alias_base, ic) # e.g. "ba1" for 1st parent, 1st child; bb3 -2nd parent, 3rd child
			sql_select.append("%sp.name as dataset_%s%i" % (cloc_alias_base, ipl_alpha, ic))
			# is string if this cloc variable is being compared to a string constant
			# check constant on either side of adjancent relational operator
			isstring = (cti < len(tokens)-2 and ttypes[cti+1] == "ROP" and ttypes[cti+2] == "SC") or (
					cti > 1 and ttypes[cti-1] == "ROP" and ttypes[cti-2] == "SC")
			if isstring:
				sql_select.append("%ss.value as %s%i_value" % (cloc_alias_base, ipl_alpha, ic))
			else:
				sql_select.append("%sv.nval as %s%i_value" % (cloc_alias_base, ipl_alpha, ic))
			sql_from.append("node as %sd" % cloc_alias_base)
			sql_from.append("path as %sp" % cloc_alias_base)
			sql_from.append("value as %sv" % cloc_alias_base)
			if isstring:
				sql_from.append("string as %ss" % cloc_alias_base)
				sql_where.append("%sv.str_id = %ss.id" % (cloc_alias_base, cloc_alias_base))
			sql_where.append("%sd.parent_id = %sg.id" % (cloc_alias_base, ploc_alias_base))
			sql_where.append("%sd.path_id = %sp.id" % (cloc_alias_base, cloc_alias_base))
			sql_where.append("%sd.value_id = %sv.id" % (cloc_alias_base, cloc_alias_base))
			sql_where.append("%sp.name LIKE '%s'" % (cloc_alias_base, "%" + tokens[cti]))
			# replace string in tokens with sql to retrieve value, either numeric or string
			if isstring:
				tokens[cti] = "%ss.value" % cloc_alias_base
			else:
				tokens[cti] = "%sv.nval" % cloc_alias_base
	# done building sql_select, sql_from and sql_where for parent and child datasets
	# Now, add in expression from tokens
	sql_where.append("( %s )" % " ".join(tokens))
	# finally, create the sql command
	sql = ",\n\t".join(sql_select) + "\n" + ",\n\t".join(sql_from) + "\n" + " AND\n\t".join(sql_where)
	return sql


def main():
	global test_queries;
	queries = test_queries.splitlines()
	for query in queries:
		if query:
			ti = parse(query)
			# sql = make_sql(ti)
			# print ("sql=\n%s" % sql)

if __name__ == "__main__":
	main()

import parse
import pprint
pp = pprint.PrettyPrinter(indent=4, width=120, compact=True)


queries = [
	# "epochs: start_time > 10",
	# "(epochs: start_time > 10)",
	# "epochs: id, location, start_time > 10 & general/subject: species LIKE '%Mus%'",
	# "epochs: start_time > 10 | general/subject: species LIKE '%Mus%'",
	"(epochs: id, location, start_time > 10 | general/subject: species LIKE '%Mus%') & /nwb_version == '2.3'",
	# "(p1: c1 > 10 & (c2 == 27)) | ( p2: x = y & p3: w = q)",
]


def find_subqueries(ti):
	# locate subqueries in query,  Return list of index ranges for subqueries
	subquery_indices = []
	for ploc_info in ti['plocs']:
		ploc = ploc_info[0]
		cloc_indices = ploc_info[1:]
		

	stack = []  # contains tokens and positions
	current_ploc = 0;
	last_cloc = ti['plocs'][current_ploc][-1]   # index to last cloc in current ploc

	stack.append(("START", 0))
	for i in range(ti['ttypes'] + 1):
		ttype = "END" if i == len(ti['ttypes']) else ti['ttypes'][i];
		if ttype == "(":
			stack.append(ttype, i)
		elif ttype == "CLOC":
			assert stack[-1] is 
		elif ttype == "NC" or ttype == "SC":
			# found constant, should be CLOC OP
		elif ttype == ")":
			if (!stack):
				sys.exit("Unmatched parentheses: closing ')' found, but no matching opening '('")
			stk_ttype, stk_indx = stack.pop()
			assert stk_ttype == "(", "expected '(' on stack, found %s" % stk_ttype
			if i > last_cloc:
				# founding closing parentheses and already past last child location index, this must indicate the end
				# of the current subquery, beginning of current subquery is the position on the stack
				subquery_indicies.append((stk_indx, i))
				current_ploc += 1
				if current_ploc >= len(ti['plocs']):
					current_ploc = None  # flag done, but may have more parentheses
				else:
					last_cloc = ti['plocs'][current_ploc][-1]  # get new last ploc
		elif ttype 


	pp.pprint(ti)

for i in range(len(queries)):
	query = queries[i]
	ti = parse.parse(query)
	print("\n%i. %s\n" % (i, query))
	patch = make_patch(ti)
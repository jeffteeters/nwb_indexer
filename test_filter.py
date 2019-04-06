import pprint
# pp = pprint.PrettyPrinter(indent=4)
pp = pprint.PrettyPrinter(indent=4)



id = [1, 2, 3]
start_time = [1.1, 2.2, 3.3]
stop_time = [1.8, 2.8, 3.8]
tags = ['good', 'left', 'strong', # trial_1 tags
    'bad',				# trial_3 tag; are no trial_2 tags
	'left', 'bad']		# trial_4 tags
tags_index = [3, 3, 4, 6]


# build tags_lists - list of tags in array by ids
tags_lists = []
cur_from = 0
i = 0
for cur_to in tags_index:
	if cur_to > cur_from:
		tags_lists.append(tags[cur_from:cur_to])
	else:
		tags_lists.append([])
	cur_from = cur_to


def do_filter(query, zipl):
	# query like:
	# x[1] > 2.1 and 'left' in x[3]
	# scope = locals()
	#nprint("locals are: %s" % scope)
    # _globals = globals()
	str_filt = "filter( (lambda x: %s), zipl)" % query
	# result = list(eval(str_filt, None, scope))
	result = list(eval(str_filt))
	return result


print("tags_lists = %s" % tags_lists)

zipl = list(zip(id, start_time, stop_time, tags))

result = list(filter( (lambda x: x[1] > 2.1 and 'left' in x[3]), zipl))

str_filt =   "filter( (lambda x: x[1] > 2.1 and 'left' in x[3]), zipl)"

scope = globals()
result2 = list(eval(str_filt))

print("result is:")
pp.pprint(result)

print("result2 is:")
pp.pprint(result2)

query = "x[1] > 2.1 and 'left' in x[3]"
result3 = do_filter(query, zipl)

print("result3 is:")
pp.pprint(result3)



# query = "start_time > 2.1 and ('left' in tags_lists)"

# result = list(filter( (lambda time0, t_tag:  start_time > time0 and t_tag in tags_lists), )

# result = (st, tl) (for st, tl in zip(start_time, tags_lists) if st > 2.1 and 'left' in tl);

# del_ids = [2, 4]
# ids = [3, 2, 4, 1]
# other = ['a', 'b', 'c', 'd']
# ids, other = zip(*((id, other) for id, other in zip(ids, other) if id not in del_ids))

# print("ids=%s, other=%s", (ids, other))


# result = ((st, tl) for st, tl in zip(start_time, tags_lists) if st > 2.1 and 'left' in tl);
# print ("result is %s" % result)


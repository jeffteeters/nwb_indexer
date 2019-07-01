import re
import pprint
import numpy as np
import h5py
import timeit
# from io import StringIO
import io
import csv

pp = pprint.PrettyPrinter(indent=4, width=120, compact=True)

# constants used for packing and unpacking

quotechar = '"'
delimiter=","	# between intems in list /column.  Example: a,b,c
escapechar = '\\'

def pack(cols, index_vals = None, col_names = None, in_table = False, node_path=None, fp=None):
	# pack array of values for storing in sqlite database, table "value" field "sval"
	# return as tuple: (packed_values, type_code)
	# packed_values for compound type (more than one column) stored as:
	#	<typeCodes><i/n><csv-data>[i]<index_values>
	# where:
	#   <typeCodes> either 'F'-float, 'I'-int, 'M'-string; one character for each column
	#   <i/n> set to 'i' if index values present, otherwise 'n'
	#   <index_values>, if present proceeded by 'i', csv values of index
	#   <csv-data> has column names followed by all column values appended
	# If not compound type, then <typecodes> and column names are not included, so looks like:
	#   <i/n><csv-data>[i]<index_values>

	def pack_column(col):
		# format an 1-d array of values as a comma separated string
		# return a tuple of type_code and formatted column
		# in_table is True if column is in a NWB 2 table, False otherwise
		assert len(col) > 0, "attempt to format empty column at %s" % node_path
		if isinstance(col[0], bytes):
			col = [x.decode("utf-8") for x in col]
			packed = make_csv(col)
			type_code = "M" if in_table else "S"
		elif isinstance(col[0], str):
			packed = make_csv(col)			
			type_code = "M" if in_table else "S"
		elif isinstance(col[0], (int, np.integer)):
			packed = delimiter.join(["%g" % x for x in col])
			type_code = 'I'
		elif isinstance(col[0], (float, np.float)):
			packed = delimiter.join(["%g" % x for x in col])
			type_code = 'F'
		elif isinstance(col[0], h5py.h5r.Reference):
			# convert reference to name of target
			col = [fp[x].name for x in col]
			packed = make_csv(col)
			type_code = "M" if in_table else "S"
		elif np.issubdtype(col.dtype, np.integer) or np.issubdtype(col.dtype, np.floating):
		# elif isinstance(col[0], np.number):
			packed = delimiter.join(["%g" % x.item() for x in col])  # convert to python type
			type_code = "I" if  np.issubdtype(col.dtype, np.integer) else "F"
		else:
			print("pack_column: Unknown type (%s) at %s" % (type(col[0]), node_path))
			import pdb; pdb.set_trace()
		return (packed, type_code)

	def make_csv(col):
		output = io.StringIO()
		writer = csv.writer(output, delimiter=delimiter, quotechar=quotechar,
			doublequote = False, escapechar = escapechar, lineterminator='')
		writer.writerow(col)
		packed = output.getvalue()
		return packed

	# start of main for pack
	if len(cols) > 1:
		# make sure columns of same length and one name for each column
		assert len(cols) == len(col_names)
		length_first_col = len(cols[0])
		for i in range(1,len(cols)):
			assert len(cols[i]) == length_first_col
	else:
		assert col_names is None
	packed_columns = []
	column_types = []
	for col in cols:
		packed, type_code = pack_column(col)
		packed_columns.append(packed)
		column_types.append(type_code)
	if index_vals is not None:
		index_str = "i" + delimiter.join(["%i" % x for x in index_vals])
		index_flag = "i"
	else:
		index_str = ""
		index_flag = "n"
	if col_names:
		packed_col_names = pack_column(col_names)[0]
		col_info_prefix = "".join(column_types) + index_flag + packed_col_names + delimiter 
		type_code = "c"
	else:
		col_info_prefix = index_flag
	packed_values = col_info_prefix + delimiter.join(packed_columns) + index_str
	return (packed_values, type_code)



def unpack(packed, value_type, required_col_names=None):
	# returns dictionary like: {
	# 'cols': [ [col1], [col2], ...]
	# 'col_names': [ col_names, ],
	# 'col_types': [ type_code, ...]
	# 'index_values': [... ]
	# }
	# or None if any required_subscripts are not present
	uv = { }  # dict for storing unpacked values

	def convert_column(col, value_type):
		# convert col values from string to type given in value_type
		assert value_type in ('I', 'F', 'S', 'M')
		if value_type == 'I':
			# list of integers
			value = list(map(int, col))
		elif value_type == 'F':
			# list of floats
			value = list(map(float, col))
		else:
			# should be array of strings, no need to convert
			value = col
		return value

	# start of main of unpack
	if value_type == "c":
		m = re.match("^([MFI]*)([in])", packed)
		column_types = m.group(1)
		num_columns = len(column_types)
		uv['col_types'] = column_types
		have_index_values = m.group(2) == "i"
		csv_start_index = num_columns + 1
	else:
		have_index_values = packed[0] == "i"
		csv_start_index = 1 # skip over i/n (first character)
	if have_index_values:
		i_index = packed.rfind("i")
		packed_index_values = packed[i_index+1:]
		uv['index_values'] = list(map(int, packed_index_values.split(',')))
		packed = packed[csv_start_index: i_index]
	else:
		packed = packed[csv_start_index:]
	f = io.StringIO(packed)
	reader = csv.reader(f, delimiter=delimiter, quotechar=quotechar,
		doublequote = False, escapechar = escapechar)
	vals = reader.__next__()
	# print("vals right after being read: %s" % vals)
	# because newline chars are treated as new line by reader, append any other lines to first
	for vals2 in reader:
		vals[-1] = vals[-1] + "\n" + vals2[0]
		if len(vals2) > 1:
			vals.extend(vals2[1:])
	# print("vals after extending: %s" % vals)
	if value_type == 'c':
		# get column names from front of vals
		uv['col_names'] = vals[0:num_columns]
		if required_col_names is not None:
			for col_name in required_col_names:
				if col_name not in uv['col_names']:
					# do not do any more processing, required column name is missing
					return None
		vals = vals[num_columns:]
		# print("vals=%s\nvals2=%s" % (vals, vals2))
		assert len(vals) % num_columns == 0, "len(vals)=%i not divisable by num_columns=%i" %(
			len(vals), num_columns)
		# print("num_columns=%s" % num_columns)
		column_length = int(len(vals) / num_columns)
		cols = [ ((i*column_length), ((i+1)*column_length)) for i in range(num_columns) ]
		# print("cols=%s" % cols)
		cols = [ convert_column(vals[(i*column_length): ((i+1)*column_length)], column_types[i])
			 for i in range(num_columns) ]
	else:
		# print("vals=%s, value_type=%s" % (vals, value_type))
		cols = [ convert_column(vals, value_type) , ]
	uv['cols'] = cols
	return uv



# constants used for packing and unpacking
quote_chars = "'\""
delimiter=","	# between intems in list /column.  Example: a,b,c
seperator=";"	# between lists / column, Example: a,b,c;d,e,f  (';' seperates two lists)

def pack_old(cols, index_vals = None, col_names = None, in_table = False, node_path=None, fp=None):
	# pack array of values for storing in sqlite database, table "value" field "sval"
	# return as tuple: (packed_values, type_code)

	def pack_column(col):
		# format an 1-d array of values as a comma separated string
		# return a tuple of type_code and formatted column
		# in_table is True if column is in a NWB 2 table, False otherwise
		assert len(col) > 0, "attempt to format empty column at %s" % node_path
		if isinstance(col[0], bytes):
			packed = delimiter.join( [escape(x.decode("utf-8")) for x in col ] )
			type_code = "M" if in_table else "S"
		elif isinstance(col[0], str):
			packed = delimiter.join( [escape(x) for x in col ] )			
			type_code = "M" if in_table else "S"
		elif isinstance(col[0], (int, np.integer)):
			packed = delimiter.join(["%g" % x for x in col])
			type_code = 'I'
		elif isinstance(col[0], (float, np.float)):
			packed = delimiter.join(["%g" % x for x in col])
			type_code = 'F'
		elif isinstance(col[0], h5py.h5r.Reference):
			# convert reference to name of target
			packed = delimiter.join( [escape(fp[x].name) for x in col] )
			type_code = "M" if in_table else "S"
		elif np.issubdtype(col.dtype, np.integer) or np.issubdtype(col.dtype, np.floating):
		# elif isinstance(col[0], np.number):
			packed = delimiter.join(["%g" % x.item() for x in col])  # convert to python type
			type_code = "I" if  np.issubdtype(col.dtype, np.integer) else "F"
		else:
			print("format_column: Unknown type (%s) at %s" % (type(col[0]), node_path))
			import pdb; pdb.set_trace()
		return (packed, type_code)

	def escape(value):
		# convert value to escaped version if necessary
		assert isinstance(value, str)
		if delimiter in value or seperator in value:
			# need to quote value, find quote character to use
			unused_quote_char = None
			for quote_char in quote_chars:
				if quote_char not in value:
					unused_quote_char = quote_char
					break
			if unused_quote_char is None:
			# both quote chars were used, use quote_chars[0] as quote char
				quote_char = quote_chars[0]
				# escape quote character
				value = value.replace(quote_char, "\\" + quote_char)
			value = quote_char + value + quote_char
		return value

	# start main for function pack

	# if compound type (more than one column) then col_names must be present, otherwise not
	assert (len(cols) > 1 and col_names) or (len(cols) == 1 and col_names is None), (
		"len(cols)=%s, colnames is %s, path=%s, cols=\n%s" % (len(cols), col_names, node_path, cols))
	packed_columns = []
	column_types = []
	for col in cols:
		packed, type_code = pack_column(col)
		packed_columns.append(packed)
		column_types.append(type_code)
	if index_vals is not None:
		index_str = "i" + delimiter.join(["%i" % x for x in index_vals])
	else:
		index_str = ""
	if col_names:
		# col_names given, form column with column names and column type
		assert len(col_names) == len(column_types)
		ssc_str = delimiter.join( [ escape(col_names[i] 
			+ column_types[i]) for i in range(len(column_types)) ]) + seperator
		type_code = "c"
	else:
		ssc_str = ""
	packed_values = ssc_str + seperator.join(packed_columns) + index_str
	return (packed_values, type_code)




def unpack_old(packed, value_type, required_col_names=None):
	# returns dictionary like: {
	# 'cols': [ [col1], [col2], ...]
	# 'col_names': [ col_names, ],
	# 'col_types': [ type_code, ...]
	# 'index_values': [... ]
	# }
	# or None if any required_subscripts are not present
	uv = { }  # dict for storing unpacked values

	def extract_col_names(col):
		# extract subscript names and column types
		nonlocal uv
		names = []
		types = []
		for x in col:
			name = x[0:-1]
			typ = x[-1]
			assert typ in ('I', 'F', 'M'), "found type code was '%s'" % typ
			names.append(name)
			types.append(typ)
		uv['col_names'] = names
		uv['col_types'] = types

	def convert_cols(cols):
		# convert one or more columns of compound type, based on self.column_types
		nonlocal uv
		ccol = []
		assert len(uv['col_types']) == len(cols)
		for i in range(len(cols)):
			col = cols[i]
			value_type = uv['col_types'][i]
			ccol.append(convert_column(col, value_type))
		return ccol

	def convert_column(col, value_type):
		# convert col values from string to type given in value_type
		assert value_type in ('I', 'F', 'S', 'M')
		if value_type == 'I':
			# list of integers
			value = list(map(int, col))
		elif value_type == 'F':
			# list of floats
			value = list(map(float, col))
		else:
			# should be array of strings, no need to convert
			value = col
		return value

	# start of main for unpack
	# unpack values to index_vals and unpacked_values
	try:
		match = re.match("(?P<main_vals>^.*?)(?:i(?P<index_vals>\d+(?:,\d+)*))?$", packed,
			flags=re.DOTALL)
	except:
		import pdb; pdb.set_trace()
	assert match
	packed_main_vals = match.group("main_vals")
	packed_index_vals = match.group("index_vals")
	if packed_main_vals[-1] == delimiter:
		# if ends with ',' append ';' so will find last value which is an empty string
		packed_main_vals += seperator
	# print ("main_vals = %s, index_vals=%s" % (main_vals, index_vals))
	if packed_index_vals is not None:
		uv['index_vals'] = list(map(int, packed_index_vals.split(',')))

	pattern = re.compile(r'''(
		(?:(?P<quote>['\"])(?P<string>.*?)(?<!\\)(?P=quote)(?P<trail>(?:[,;]|$)))|
		(?:(?P<stringnq>.*?)(?P<trailnq>(?:[,;]|$)))
		)''', re.VERBOSE + re.DOTALL)
	cols = []
	cur_col = []
	for e in re.finditer(pattern, packed_main_vals):
		val = e.group('string')
		# print("string val = '%s'" % val)
		if val is not None:
			tail = e.group('trail')
		else:
			val = e.group('stringnq')
			tail = e.group('trailnq')
			# print("stringnq val = '%s', tail='%s'" % (val, tail))
			if val == '' and tail == '':
				# no more values, all done
				# print("val='%s', cols when all done:" % val)
				# pp.pprint(cols)
				break
		# print ("val=%s, tail=%s" % (val, tail))
		cur_col.append(val)
		if tail == ';' or tail == '':
			if required_col_names is not None and len(cols) == 0:
				# this is the first column which should be column names;
				# make sure all required_column_names present
				assert value_type == 'c'
				for col_name in required_col_names:
					if col_name not in cur_col:
						# did not find required_col_name
						return None
			cols.append(cur_col)
			cur_col = []
	if value_type == 'c':
		# first column should be subscript names with type codes, extract them
		assert len(cols) > 1
		extract_col_names(cols[0])
		cols = cols[1:]
		cols = convert_cols(cols)
	else:
		assert len(cols) == 1
		cols = [ convert_column(cols[0], value_type) , ]
	uv['cols'] = cols
	return uv


def run_tests():
	# vp = Value_packer(in_table = True)
	col_names = ["name1", "weight2", "age", "bday-3'rd", "city,4" ]
	cols1 = [
		["Mary", "Sue's", "Thom's", "sues-\"hello\"", "ss-'hi\"mom\"'"],
		[23.5, 33.5, 43.5, 53.5, 63.5],
		[22, 32, 45, 55, 66],
		["Jan,uary", "feb;uary", 'march', "April", "May"],
		["den-'ve\"r\"'", "Eau,claire", "New\nyork", "Sparta's", "Chip-\"pewa\"",]
	]
	index_vals = [ 1, 2, 3, 7, 10, 210]
	cols2 = [["Mary", "Sue's", "Thom's", "sues-\"hello\"", "ss-'hi\"mom\"'"], ]

	test_vals = [
		# cols, index_vals, col_names, in_table
		[cols1, index_vals, col_names, True],
		[cols2, None, None, False],
	]
	for i in range(len(test_vals)):
		tvals = test_vals[i]
		print("test %i:" % i)
		cols, index_vals, col_names, in_table = tvals
		print("col_names: %s" % col_names)
		print("index_vals: %s" % index_vals)
		print("in_table: %s" % in_table)
		print("cols:")
		pp.pprint(cols)
		packed, type_code = pack(cols, index_vals=index_vals, col_names=col_names, in_table=True)
		print("packed: %s" % packed)
		unpacked = unpack(packed, type_code)
		print("unpacked:")
		pp.pprint(unpacked)
		print("cols match: %s" % (str(cols) == str(unpacked['cols'])))
		if index_vals:
			print("index_vals match: %s" % (str(index_vals) == str(unpacked['index_vals'])))
		if col_names:
			print("col_names match: %s" % (str(col_names) == str(unpacked['col_names'])))

scratch = """
	print("Before packing:")
	print("subscript_names: %s" % col_names)
	pp.pprint(cols)
	# for col in cols:
	# 	vp.add_column( col )
	print("index_vals: %s" % index_vals)
	# vp.add_index_vals( index_vals )
	# vp.add_subscript_names(col_names)
	# packed_values = vp.get_packed_values()
	# print("packed values are:")
	# print(packed_values)

	# try packing with function
	pv2, type_code = pack(cols, index_vals=index_vals, col_names=col_names, in_table=True)
	print("packed values, type_code=%s:" % type_code)
	print(pv2)
	# if packed_values == pv2:
	# 	print("packed values match.")


	# now unpack
	# vp = Value_unpacker( packed_values, value_type='c')
	# unpacked_cols = vp.get_unpacked_values()
	# unpacked_index_vals = vp.get_index_vals()
	# unpacked_subscript_names = vp.get_subscript_names()
	# unpacked_subscript_types = vp.get_column_types()
	# print("unpacked values:")
	# print("subscript_names: %s" % unpacked_subscript_names)
	# print("subscript_types: %s" % unpacked_subscript_types)
	# print("cols:")
	# pp.pprint(unpacked_cols)
	# print("index vals=%s" % unpacked_index_vals)

	# try unpack function
	up2 = unpack(pv2, 'c')
	print("unpack function output:")
	pp.pprint(up2)
	if str(cols) == str(up2['cols']):
		print("original and unpacked cols match,\n%s" % str(cols))

	# try packing a single column
	cols = [["Mary", "Sue's", "Thom's", "sues-\"hello\"", "ss-'hi\"mom\"'"], ]
	pv3, tc3 = pack(cols, in_table=False)
	print("packed single column, type_code=%s" % tc3)
	print(pv3)
	up3=unpack(pv3, tc3)
	print("original single column:")
	pp.pprint(cols)
	print("unpacked single column:")
	pp.pprint(up3)
	if str(cols) == str(up3['cols']):
		print("single column values match after pack and unpack\n%s" % cols)
"""

def time_test():
	import time
	from io import StringIO
	import csv
	col_names = "col1M,col2M,col3M,col4M,col5M"
	col_pat = ','.join(["sue,mary\'s,'mark;\s'," + '"tom,mary",Jeff\'sM,kathryn' for i in range(50)])
	# packed = col_names + ';' + ';'.join(col_pat for i in range(5))
	packed = ','.join(col_pat for i in range(5))
	value_type = 'S'
	t0 = time.time()
	unpacked = unpack_old(packed, value_type)
	# time1 = timeit.timeit(call1, number=100, globals={'packed': packed, 'unpack': unpack, 'value_type': value_type})
	t1 = time.time()
	cols2 = packed.split(',')
	t2 = time.time()
	# time2 = timeit.timeit(call2, number=100, globals={'packed': packed})
	cols3 = unpack(packed, value_type)
	t3 = time.time()
	print("time1, unpack=%s" % ((t1 - t0)*1000))
	print("time2, split=%s" % ((t2 - t1)*1000))
	print("time3, csv=%s" % ((t3 - t2)*1000))
	print("cols2 has %i elements" % len(cols2))
	print('\t'.join(cols2[0:10]))
	print("cols3 has %i elements" % len(cols3['cols'][0]))
	print('\t'.join(cols3['cols'][0][0:10]))
	# for row in reader:
	# 	print("row has %i elements" % len(row))
	# 	print('\t'.join(row[0:10]))


if __name__ == "__main__":
	# time_test()
	run_tests()

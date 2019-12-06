import re
import pprint
import numpy as np
import h5py
import timeit
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
		def int_type_code():
			return 'I' if index_vals is None else "J"
		def float_type_code():
			return 'F' if index_vals is None else "G"
		def pack_numeric(col):
			return delimiter.join(["%g" % x for x in col])
		def pack_numpy_numeric(col):
			return delimiter.join(["%g" % x.item() for x in col])  # convert to python type
		def pack_numpy_bool(col):
			return delimiter.join(["1" if x else "0" for x in col])

		assert len(col) > 0, "attempt to format empty column at %s" % node_path
		if isinstance(col[0], bytes):
			col = [x.decode("utf-8") for x in col]
			packed, type_code = make_csv(col)
		elif isinstance(col[0], str):
			packed, type_code = make_csv(col)	
		elif isinstance(col[0], (int, np.integer)):
			packed = pack_numeric(col)
			type_code = int_type_code()
		elif isinstance(col[0], (float, np.float)):
			packed = pack_numeric(col)
			type_code = float_type_code()
		elif np.issubdtype(col.dtype, np.integer):
			packed = pack_numpy_numeric(col)
			type_code = int_type_code()
		elif np.issubdtype(col.dtype, np.floating):
			packed = pack_numpy_numeric(col)
			type_code = float_type_code()
		elif isinstance(col[0], h5py.h5r.Reference):
			# convert reference to name of target
			col = [fp[x].name for x in col]
			packed, type_code = make_csv(col)
		elif np.issubdtype(col.dtype, np.bool_):
			packed = pack_numpy_bool(col)
			type_code = int_type_code()
		else:
			print("pack_column: Unknown type (%s) at %s" % (type(col[0]), node_path))
			import pdb; pdb.set_trace()
		return (packed, type_code)

	def make_csv(col):
		# convert string array to csv, also return string type code
		assert isinstance(col[0], str)
		output = io.StringIO()
		writer = csv.writer(output, delimiter=delimiter, quotechar=quotechar,
			doublequote = False, escapechar = escapechar, lineterminator='')
		writer.writerow(col)
		packed = output.getvalue()
		str_type_code = "S" if not in_table else "M" if index_vals is None else "B"
		return (packed, str_type_code)

	# start of main for pack
	if len(cols) > 1:
		# make sure columns of same length and one name for each column
		assert len(cols) == len(col_names)
		length_first_col = len(cols[0])
		for i in range(1,len(cols)):
			assert len(cols[i]) == length_first_col
	else:
		assert len(cols) == 1
		if col_names is not None:
			assert len(col_names) == 1
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
		col_info_prefix = ""
	packed_values = col_info_prefix + delimiter.join(packed_columns) + index_str
	return (packed_values, type_code)



def unpack(packed, value_type, required_col_names=None):
	# returns dictionary like: {
	# 'cols': [ [col1], [col2], ...]
	# 'col_names': [ col_names, ],
	# 'col_types': [ type_code, ...]
	# 'index_vals': [... ]
	# }
	# or None if any required_subscripts are not present
	uv = { }  # dict for storing unpacked values

	def convert_column(col, value_type):
		# convert col values from string to type given in value_type
		assert value_type in ('I', "J", 'F', "G", 'S', 'M', "B")
		if value_type in ('I', "J"):
			# list of integers
			value = list(map(int, col))
		elif value_type in ('F', "G"):
			# list of floats
			value = list(map(float, col))
		else:
			# should be array of strings, no need to convert
			value = col
		return value

	# start of main of unpack
	if value_type == "c":
		m = re.match("^([MBFGIJ]*)([in])", packed)
		column_types = m.group(1)
		num_columns = len(column_types)
		uv['col_types'] = column_types
		have_index_values = m.group(2) == "i"
		csv_start_index = num_columns + 1
	else:
		have_index_values = value_type in ("J", "G", "B")
		csv_start_index = 0
	if have_index_values:
		i_index = packed.rfind("i")
		assert i_index > 0
		packed_index_values = packed[i_index+1:]
		uv['index_vals'] = list(map(int, packed_index_values.split(',')))
		packed = packed[csv_start_index: i_index]
	elif csv_start_index > 0:
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
		print("type_code=%s, packed: %s" % (type_code, packed))
		unpacked = unpack(packed, type_code)
		print("unpacked:")
		pp.pprint(unpacked)
		cols_match = str(cols) == str(unpacked['cols'])
		print("cols match: %s" % cols_match)
		if index_vals:
			index_vals_match = str(index_vals) == str(unpacked['index_vals'])
			print("index_vals match: %s" % index_vals_match)
		else:
			index_vals_match = True
		if col_names:
			col_names_match = str(col_names) == str(unpacked['col_names'])
			print("col_names match: %s" % col_names_match)
		else:
			col_names_match = True
		test_result = "PASSED" if cols_match and index_vals_match and col_names_match else "FAILED"
		print("Test %s" % test_result)



def time_test():
	import time
	from io import StringIO
	import csv
	col_names = "col1M,col2M,col3M,col4M,col5M"
	col_pat = ','.join(["sue,mary's,'mark's;'," + '"tom,mary",Jeff\'sM,kathryn' for i in range(50)])
	# packed = col_names + ';' + ';'.join(col_pat for i in range(5))
	packed = ','.join(col_pat for i in range(5))
	value_type = 'S'
	# t0 = time.time()
	# unpacked = unpack_old(packed, value_type)
	# time1 = timeit.timeit(call1, number=100, globals={'packed': packed, 'unpack': unpack, 'value_type': value_type})
	t1 = time.time()
	cols2 = packed.split(',')
	t2 = time.time()
	# time2 = timeit.timeit(call2, number=100, globals={'packed': packed})
	cols3 = unpack(packed, value_type)
	t3 = time.time()
	# print("time1, unpack=%s" % ((t1 - t0)*1000))
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

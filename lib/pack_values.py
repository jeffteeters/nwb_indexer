import re
import pprint
import numpy as np
import h5py

pp = pprint.PrettyPrinter(indent=4, width=120, compact=True)


# constants used for packing and unpacking
quote_chars = "'\""
delimiter=","	# between intems in list /column.  Example: a,b,c
seperator=";"	# between lists / column, Example: a,b,c;d,e,f  (';' seperates two lists)

def pack(cols, index_vals = None, col_names = None, in_table = False, node_path=None, fp=None):
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




class Value_store:
	# defines constants used in Value_packer and Value_unpacker
	quote_chars = "'\""
	delimiter=","
	seperator=";"

class Value_packer(Value_store):

	# Packs values stored in value.sval

	def __init__(self, in_table = False, node = None, fp = None):
		self.in_table = in_table
		self.node = node
		self.fp = fp
		self.packed_columns = []
		self.column_types = []
		self.subscript_names = None
		self.index_vals = None
		# final result of packing
		self.packed_values = None


	def add_column(self, col):
		# add column by converting to string, escaping (if necessary) and joining
		packed, type_code = self.pack_column(col)
		self.packed_columns.append(packed)
		self.column_types.append(type_code)

	def pack_column(self, col):
		# format an 1-d array of values as a comma separated string
		# return a tuple of type_code and formatted column
		# in_table is True if column is in a NWB 2 table, False otherwise
		assert len(col) > 0, "attempt to format empty column at %s" % self.node.name
		if isinstance(col[0], bytes):
			packed = self.delimiter.join( [self.escape(x.decode("utf-8")) for x in col ] )
			type_code = "M" if self.in_table else "S"
		elif isinstance(col[0], str):
			packed = self.delimiter.join( [self.escape(x) for x in col ] )			
			type_code = "M" if self.in_table else "S"
		elif isinstance(col[0], (int, np.integer)):
			packed = self.delimiter.join(["%g" % x for x in col])
			type_code = 'I'
		elif isinstance(col[0], (float, np.float)):
			packed = self.delimiter.join(["%g" % x for x in col])
			type_code = 'F'
		elif isinstance(col[0], h5py.h5r.Reference):
			# convert reference to name of target
			packed = self.delimiter.join( [self.escape(fp[x].name) for x in col] )
			type_code = "M" if self.in_table else "S"
		elif np.issubdtype(col.dtype, np.integer) or np.issubdtype(col.dtype, np.floating):
		# elif isinstance(col[0], np.number):
			packed = self.delimiter.join(["%g" % x.item() for x in col])  # convert to python type
			type_code = "I" if  np.issubdtype(col.dtype, np.integer) else "F"
		else:
			print("format_column: Unknown type (%s) at %s" % (type(col[0]), node.name))
			import pdb; pdb.set_trace()
		return (packed, type_code)

	def add_index_vals(self, index_vals):
		assert isinstance(index_vals, list) and isinstance(index_vals[0], int)
		self.index_vals = index_vals

	def add_subscript_names(self, subscript_names):
		assert isinstance(subscript_names, list) and isinstance(subscript_names[0], str)
		assert self.in_table, "if adding subscript_names must be in_table"
		self.subscript_names = subscript_names

	def escape(self, value):
		# convert value to escaped version if necessary
		assert isinstance(value, str)
		if self.delimiter in value or self.seperator in value:
			# need to quote value, find quote character to use
			unused_quote_char = None
			for quote_char in self.quote_chars:
				if quote_char not in value:
					unused_quote_char = quote_char
					break
			if unused_quote_char is None:
			# both quote chars were used, use quote_chars[0] as quote char
				quote_char = self.quote_chars[0]
				# escape quote character
				value = value.replace(quote_char, "\\" + quote_char)
			value = quote_char + value + quote_char
		return value

	def get_packed_values(self):
		if self.index_vals:
			index_str = "i" + self.delimiter.join(["%i" % x for x in self.index_vals])
		else:
			index_str = ""
		if self.subscript_names:
			# subscript names given, form column with subscript names and column names
			assert len(self.subscript_names) == len(self.column_types)
			ssc_str = self.delimiter.join( [ self.escape(self.subscript_names[i] 
				+ self.column_types[i]) for i in range(len(self.column_types)) ]) + self.seperator
		else:
			ssc_str = ""
		self.packed_values = ssc_str + self.seperator.join(self.packed_columns) + index_str
		return self.packed_values



def unpack(packed, value_type, required_col_names=None):
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


	# def __init__(self, packed_values, value_type, required_subscripts=None):
	# 	self.packed_values = packed_values
	# 	assert value_type in ('I', 'F', 'S', 'c', 'M')
	# 	self.value_type = value_type
	# 	self.cols = None
	# 	self.index_vals = None
	# 	self.subscript_names = None
	# 	self.column_types = None




class Value_unpacker(Value_store):

	# unpacks values stored in value.vstr

	def __init__(self, packed_values, value_type, required_subscripts=None):
		self.packed_values = packed_values
		assert value_type in ('I', 'F', 'S', 'c', 'M')
		self.value_type = value_type
		self.required_subscripts = required_subscripts
		self.cols = None
		self.index_vals = None
		self.subscript_names = None
		self.column_types = None

	def get_unpacked_values(self):
		# unpack values to index_vals and unpacked_values
		match = re.match("(?P<main_vals>^.*?)(?:i(?P<index_vals>\d+(?:,\d+)*)?)$", self.packed_values,
			flags=re.DOTALL)
		assert match
		packed_main_vals = match.group("main_vals")
		packed_index_vals = match.group("index_vals")
		if packed_main_vals[-1] == self.delimiter:
			# if ends with ',' append ';' so will find last value which is an empty string
			packed_main_vals += self.seperator
		# print ("main_vals = %s, index_vals=%s" % (main_vals, index_vals))
		if packed_index_vals is not None:
			self.index_vals = list(map(int, packed_index_vals.split(',')))

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
				cols.append(cur_col)
				# check for wanted subscript, if not found abort - Jeff
				cur_col = []
		if self.value_type == 'c':
			# first column should be subscript names with type codes, extract them
			assert len(cols) > 1
			self.extract_subscript_names(cols[0])
			cols = cols[1:]
			cols = self.convert_cols(cols)
		else:
			assert len(cols) == 1
			cols = [ self.convert_column(cols[0], self.value_type), ]
		self.cols = cols
		return self.cols

	def get_index_vals(self):
		return self.index_vals

	def get_subscript_names(self):
		return self.subscript_names

	def get_column_types(self):
		return self.column_types

	def extract_subscript_names(self, col):
		# extract subscript names and column types
		names = []
		types = []
		for x in col:
			name = x[0:-1]
			typ = x[-1]
			assert typ in ('I', 'F', 'M'), "found type code was '%s'" % typ
			names.append(name)
			types.append(typ)
		self.subscript_names = names
		self.column_types = types

	def convert_cols(self, cols):
		# convert one or more columns of compound type, based on self.column_types
		ccol = []
		assert len(self.column_types) == len(cols)
		for i in range(len(cols)):
			col = cols[i]
			value_type = self.column_types[i]
			ccol.append(self.convert_column(col, value_type))
		return ccol

	def convert_column(self, col, value_type):
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

def run_tests():
	vp = Value_packer(in_table = True)
	col_names = ["name1", "weight2", "age", "bday-3'rd", "city,4" ]
	cols = [
		["Mary", "Sue's", "Thom's", "sues-\"hello\"", "ss-'hi\"mom\"'"],
		[23.5, 33.5, 43.5, 53.5, 63.5],
		[22, 32, 45, 55, 66],
		["Jan,uary", "feb;uary", 'march', "April", "May"],
		["den-'ve\"r\"'", "Eau,claire", "New\nyork", "Sparta's", "Chip-\"pewa\"",]
	]
	index_vals = [ 1, 2, 3, 7, 10, 210]
	print("Before packing:")
	print("subscript_names: %s" % col_names)
	pp.pprint(cols)
	for col in cols:
		vp.add_column( col )
	print("index_vals: %s" % index_vals)
	vp.add_index_vals( index_vals )
	vp.add_subscript_names(col_names)
	packed_values = vp.get_packed_values()
	print("packed values are:")
	print(packed_values)

	# try packing with function
	pv2, type_code = pack(cols, index_vals=index_vals, col_names=col_names, in_table=True)
	print("by calling pack, type_code=%s:" % type_code)
	print(pv2)
	if packed_values == pv2:
		print("packed values match.")


	# now unpack
	vp = Value_unpacker( packed_values, value_type='c')
	unpacked_cols = vp.get_unpacked_values()
	unpacked_index_vals = vp.get_index_vals()
	unpacked_subscript_names = vp.get_subscript_names()
	unpacked_subscript_types = vp.get_column_types()
	print("unpacked values:")
	print("subscript_names: %s" % unpacked_subscript_names)
	print("subscript_types: %s" % unpacked_subscript_types)
	print("cols:")
	pp.pprint(unpacked_cols)
	print("index vals=%s" % unpacked_index_vals)

	# try unpack function
	up2 = unpack(packed_values, 'c')
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
	print("unpacked single column:")
	pp.pprint(up3)
	if str(cols) == str(up3['cols']):
		print("single column values match after pack and unpack\n%s" % cols)



if __name__ == "__main__":
	run_tests()

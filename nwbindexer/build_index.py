import sys
import os
import h5py
import sqlite3
import numpy as np
import math
import nwbindexer.lib.pack_values as pack_values

# global variables
default_dbname="nwb_index.db"  # default database name
con = None     # database connection
cur = None     # database cursor
file_id = None # id of current file (id of row in sqlite2 "file" table)

# global constants used to control what is indexed

# maximum length of single string
MAX_STRING_LENGTH = 3000

# maximum length (number elements) of string array not part of NWB 2 table
MAX_STRING_ARRAY_LENGTH = 20

# maximum length of packed string array, not part of NWB 2 table
MAX_PACKED_STRING_LENGTH = 3000

# maximum length of packed string array, not part of NWB 2 table
MAX_NWB2_TABLE_SIZE = 10000		# maxium total size (number of elements) in dataset in NWB 2 table

# maximum length of packed string array, that is part of NWB 2 table
MAX_NWB2_PACKED_STRING_LENGTH = 10000

# maximum number of columns in a 2-d dataset or in a compound dataset in a NWB 2 table
MAX_NWB2_TABLE_NUMBER_OF_COLUMNS = 20


# sqlite3 database schema
schema='''
create table name (			-- name (last component of path) of hdf5 entities.  Used to locate child nodes of parent
	id integer primary key,
	name text not null
);
create index name_idx on name(name);  -- not sure if this helps.  Yes it does, if used with node name_id_idx

create table path (  -- paths listed explicitly.  Used to search for 'parent' entities specified in query.
  id integer primary key,
  path text not null  -- full path, without leading '/'
);

create index path_idx on path(path);  -- not sure if this helps

create table file (				-- hdf5 files
	id integer primary key,
	location text	-- contains full path to file 
);

create table node (  -- stores groups, dataseta AND attributes
	id integer primary key,
	file_id integer not null references file,
	parent_id integer references node, -- parent group (if group or dataset) or parent group or dataset (if attribute)
	name_id integer references name, -- name of this node (last component of full path)
	path_id integer references path, -- full path to this node.  Only saved if this node has any children.
	node_type char(1) not null CHECK( node_type in ('g', 'd', 'a', 'G') ),
		-- either: g-group, d-dataset, a-attribute, G-group with 'colnames' attribute
	value_id integer references value	-- value associated with dataset or attribute.
		-- NULL if group or if value is not saved (e.g., numeric arrays not part of a table)
);


create index node_name_id_idx on node(name_id);  -- not sure if this helps.  YES it does!
create index value_id_idx on node(value_id);  -- not sure if this helps
create index parent_id_idx on node(parent_id); -- not sure if this helps.  Yes, makes huge difference!


create table value (			-- value of dataset or attribute
	id integer primary key,
	type char(1) not null CHECK( type IN ('i','f','s','I','J','F','G','S','c','M','B') ),
		-- either: i-integer, f-float, s-string, I-integer array, F-float array,
		--		   S-string array, c-compound or 2-d
		--         M-string array part of table (type 'I', 'F' and 'c' also part of table)
		--         'J', 'G', 'B' are int, float and string arrays part of table *with* index values
	nval numeric,		-- contains value of number, if type 'i' or 'f'.  Otherwise, NULL.
	sval text			-- stores values of type s, I, F, S, c as comma seperated values otherwise NULL
		-- If type 'c' has list of columns names with column type char at end of each name, then lists
		-- of column values.  Each list element separated by ',' and lists seperated by ';'.
		-- For all table types ('I', 'F', 'c') values in associated _index dataset (if present) stored
		-- after column values, separated by ";i;"  
);

create index nval_idx on value(nval) where nval is not NULL;  -- Help speedup searches for scalars
create index sval_idx on value(sval) where type = 's';
''';


class Cache:
	# cache map of value to id
	# used to speedup creation of name and path table
	def __init__(self, table_name, value_name):
		# maps values to id
		self.map = {}
		self.table_name = table_name
		self.value_name = value_name
		self.load_map()

	def get_id(self, value):
		# get id corresponding to value (which must be a string). Will add value to map if not present
		assert isinstance(value, str)
		if value in self.map:
			key = self.map[value]  # key is the id
		else:
			key = len(self.map) + 1
			cur.execute("insert into %s (id, %s) values (?, ?)" % (self.table_name, self.value_name), (key, value))
			self.map[value] = key  # save indicator if record is new
		return key

	def load_map(self):
		# load values from table.  Needed if updating database
		global con, cur
		assert len(self.map) == 0, "load_map for table '%s' called, but map not empty" % self.table_name
		result = cur.execute("select id, %s from %s order by %s" % (self.value_name, self.table_name, self.value_name))
		for row in result:
			key, value = row
			self.map[value] = key  # save indicator that record is already in database

class Value_mirror:
	# used for quick lookups of values in value table when building index
	def __init__(self):
		# maps values to id
		self.mirror = []  # mirror of value table, elements are: (id, type, nval, sval)
		self.nval2id = {} # maps numeric values to id (id column in value table)
		self.sval2id = {} # maps string values to id
		self.load_mirror()

	def load_mirror(self):
		# load values from table.  Needed if updating database
		global con, cur
		assert len(self.mirror) == 0, "load_mirror for table 'value' called, but mirror not empty"
		result = cur.execute("select id, type, nval, sval from value order by id")
		for row in result:
			vid, vtype, nval, sval = row
			self.mirror.append( (vid, vtype, nval, sval) )
			assert vid == len(self.mirror), "column id in table value expected to be sequential, but is not"
			if vtype == 'i' or vtype == 'f':
				self.nval2id[nval] = vid
			else:
				assert isinstance(sval, str), "Should have str type sval if type not 'n'"
				# save type in key to make sure all components match (value and type of value)
				key = sval + vtype
				self.sval2id[key] = vid
		self.original_length = len(self.mirror)  # save original length of table (so will know what is new)

	def get_id(self, vtype, nval, sval):
		global cur
		assert vtype in ('i','f','I','J','F','G','s','S','c','M','B'), 'value vtype invalid: "%s"' % vtype
		if vtype == 'i':
			assert (isinstance(nval, int) or nval == "nan") and sval is None, (
				"value type 'i' not consistent, nval=%s, type=%s, sval=%s, type=%s" %
				(nval, type(nval),sval, type(sval)))
			vid = self.get_numeric_id(nval, vtype)
		elif vtype == 'f':
			assert (isinstance(nval, float) or nval == "nan") and sval is None, (
				"value type 'f' not consistent, nval=%s, type=%s, sval=%s, type=%s" %
				(nval, type(nval),sval, type(sval)))
			vid = self.get_numeric_id(nval, vtype)
		else:
			assert isinstance(sval, str) and nval is None, ( 
				"value type 's' not consisitent, sval='%s', type=%s, nval=%s" % (sval, type(sval), nval))
			key = sval + vtype
			if key in self.sval2id:
				vid = self.sval2id[key]
				saved_row = self.mirror[vid - 1]
				assert saved_row[1] == vtype and saved_row[3] == sval, (
					"value_mirror get_id saved_type '%s' != new vtype '%s' OR saved_value '%s' != new_value '%s'" % (
					(saved_row[1], vtype, saved_row[3], sval)))
				assert saved_row[0] == vid and saved_row[2] is None, "value mirror ids should match and nval == None"
			else:
				vid = len(self.mirror) + 1
				self.mirror.append ( (vid, vtype, nval, sval) )
				cur.execute("insert into value (id, type, nval, sval) values (?, ?, ?, ?)" , (
					vid, vtype, nval, sval) )
				self.sval2id[key] = vid
		return vid

	def get_numeric_id(self, nval, vtype):
		# private method used by get_id
		if nval in self.nval2id:
			vid = self.nval2id[nval]
		else:
			sval = None
			vid = len(self.mirror) + 1
			self.mirror.append ( (vid, vtype, nval, sval) )
			self.nval2id[nval] = vid
			cur.execute("insert into value (id, type, nval, sval) values (?, ?, ?, ?)" , (
				vid, vtype, nval, sval) )
		return vid


# save id's (node.id) of groups that have the column names attribute.  This used to determine if values
# should be saved, for NWB 2.x tables with aligned columns or compound tables.
# maps the node id to the list of columns obtained from the "colnames" attribute.
groups_with_colnames_attribute = {}

def open_database(db_path):
	global schema
	global con, cur
	# for testing
	# if os.path.isfile(dbname):
	# 	print("removing previous database %s" % dbname)
	# 	os.remove(dbname)
	if not os.path.isfile(db_path):
		print("Creating database '%s'" % db_path)
		con = sqlite3.connect(db_path)
		cur = con.cursor()
		cur.executescript(schema);
		con.commit()
	else:
		print("Opening existing database: %s" % db_path)
		con = sqlite3.connect(db_path)
		cur = con.cursor()

def initialize_caches():
	global value_mirror, name_cache, path_cache
	name_cache = Cache("name", "name")
	path_cache = Cache("path", "path")
	value_mirror = Value_mirror()

def get_name_id(name):
	global name_cache
	return name_cache.get_id(name)

def get_path_id(path):
	global path_cache
	# remove leading slash in path
	return path_cache.get_id(path.lstrip('/'))

def find_file_id(location):
	# return file_id if have file in database, otherwise None
	global con, cur
	cur.execute("select id from file where location = ?", (location,))
	row = cur.fetchone()
	if row is None:
		file_id = None
	else:
		file_id = row[0]
	return file_id

def get_file_id(location):
	# always return file_id, making a new entry in file table if necessary
	global con, cur
	file_id = find_file_id(location)
	if file_id is None:
		cur.execute("insert into file (location) values (?)", (location,))
		file_id = cur.lastrowid
	return file_id

def save_group(node, parent_id):
	global con, cur, file_id, groups_with_colnames_attribute
	base_name = node.name.split('/')[-1]
	name_id = get_name_id(base_name)
	# only get path_id if this group has children (e.g. could be a parent in searches)
	path_id = get_path_id(node.name) if len(node.attrs) > 0 or len(node.keys()) > 0 else None
	node_type = 'G' if "colnames" in node.attrs else 'g'
	value_id = None
	cur.execute("insert into node (file_id, parent_id, name_id, path_id, node_type, value_id)" +
		" values (?, ?, ?, ?, ?, ?)", 
			(file_id, parent_id, name_id, path_id, node_type, value_id))
	group_id = cur.lastrowid
	# if this group has the 'colnames' attribute (used in NWB 2 tables), save referenced column names
	if node_type == "G":
		value = node.attrs["colnames"]
		if not isinstance(value, np.ndarray) or not isinstance(value[0], bytes):
			print("expecting column name to be types bytes, found %s" % (type(value[0]),))
			import pdb; pdb.set_trace()
		groups_with_colnames_attribute[group_id] = [ v.decode("utf-8") for v in value]
	# save attributes
	save_node_attributes(node, group_id)
	return group_id

def save_node_attributes(node, node_id):
	# save attributes for group or dataset
	for key in sorted(node.attrs):
		value = node.attrs[key]
		save_attribute(node_id, key, value, node.name + "-" + key)

def save_dataset(node, parent_id, parent_node):
	global con, cur, file_id
	base_name = node.name.split('/')[-1]
	name_id = get_name_id(base_name)
	# only get path_id if this dataset has children (e.g. could be a parent in searches)
	path_id = get_path_id(node.name) if len(node.attrs) > 0 else None	
	value_id = get_value_id_from_dataset(node, base_name, parent_id, parent_node)
	node_type = "d"  # dataset
	cur.execute("insert into node (file_id, parent_id, name_id, path_id, node_type, value_id)" +
		" values (?, ?, ?, ?, ?, ?)", 
			(file_id, parent_id, name_id, path_id, node_type, value_id))
	dataset_id = cur.lastrowid
	# save attributes
	save_node_attributes(node, dataset_id)
	return dataset_id

def save_attribute(parent_id, key, value, attribute_path):
	global con, cur, file_id
	name_id = get_name_id(key)
	path_id = None	# attributes have not children, don't save path to them (they cannot be the parent)
	value_id = get_value_id_from_attribute(value, attribute_path)
	node_type = "a"		# indicates attribute
	cur.execute("insert into node (file_id, parent_id, name_id, path_id, node_type, value_id)" +
		" values (?, ?, ?, ?, ?, ?)",
		(file_id, parent_id, name_id, path_id, node_type, value_id))

def get_node_id(node, parent_id, parent_node):
	if isinstance(node,h5py.Group):
		node_id = save_group(node, parent_id)
	elif isinstance(node,h5py.Dataset):
		# check if this is an "_index" dataset, used with NWB 2.  If so, don't save it here since
		# values will be appended to column(s) in the associated (target) dataset
		if parent_id in groups_with_colnames_attribute:
			base_name = node.name.split('/')[-1]
			if base_name.endswith("_index"):
				assert base_name[:-len("_index")] in groups_with_colnames_attribute[parent_id], (
					"Apperent nwb 2 _index dataset does not have associated target: %s" % node.name)
				# found _index dataset with associated target dataset.  Don't save values here
				return None
		node_id = save_dataset(node, parent_id, parent_node)
	else:
		sys.exit("Unknown node type in get_node_id: %s" % node)
	return node_id

def get_value_id_from_attribute(value, attribute_path):
	global fp, value_mirror
	global MAX_STRING_ARRAY_LENGTH
	if isinstance(value, np.ndarray):
		if len(value.shape) > 1:
			# don't save multidimensional arrays
			return None
		if len(value) == 0:
			return None	# don't save zero length values
		if np.issubdtype(value.dtype, np.number) or np.issubdtype(value.dtype, np.dtype(bool).type):
			if len(value) > 1:
				# don't save values of numeric arrays, only scalars
				return None
			nval = value[0].item()	# get numeric value
			if math.isnan(nval):
				nval="nan"
			sval = None
			assert (np.issubdtype(value.dtype, np.integer)
				or np.issubdtype(value.dtype, np.dtype(bool).type)
				or np.issubdtype(value.dtype, np.float)), (
				"type is: %s" % value.dtype)
			vtype = 'f' if isinstance(value.dtype, np.float) else 'i'
		elif np.issubdtype(value.dtype, np.character) or isinstance(value.dtype, object):
			# found array of strings
			assert isinstance(value[0], bytes), "expecting string value bytes, found %s (%s) at %s " % (
			value, type(value), attribute_path)
			nval = None
			if len(value) == 1:
				sval = value[0].decode("utf-8")
				vtype = 's'	# single string
			else:
				if len(value) > MAX_STRING_ARRAY_LENGTH:
					print("Warning, not saving string in attribute because it is longer " 
						"than %i elements: %s (length = %i)" % (MAX_STRING_ARRAY_LENGTH, attribute_path,
							len(value)))
					# don't save string arrays longer than 20 elements
					return None
				sval, vtype = pack_values.pack([value, ], node_path=attribute_path)
				# sval = (b"'" + b"','".join(value) + b"'").decode("utf-8")	# join bytes, seperate by ','
				assert vtype == "S" # string array
		elif isinstance(value[0], h5py.h5r.Reference):
			# print ("found object reference in attribute at %s" % attribute_path)
			nval = None
			value = [fp[n].name for n in value]
			if len(value) > 1:
				sval, vtype = pack_values.pack([value,], node_path=attribute_path)
				# sval = "'" + "','".join(value) + "'"
				assert vtype == "S"
			else:
				sval = value[0]
				vtype = 's'
		else:
			print("unknown type %s value %s at %s" % (type(value[0]), value[0], attribute_path))
			import pdb; pdb.set_trace()
			return None
	elif isinstance(value, np.generic):
		assert len(value.shape) == 0, "expecting np.generic shape to be zero, found %i at %s" % (
			value.shape, attribute_path)
		if np.issubdtype(value.dtype, np.character):
			assert isinstance(value, bytes), "expecting value.dtype character to be bytes, found %s at %s" % (
				value, type(value), attribute_path)
			sval = value.decode("utf-8")
			nval = None
			vtype = 's'
		elif np.issubdtype(value.dtype, np.number):
			nval = value.item()	# get numeric value
			if math.isnan(nval):
				nval="nan"
			else:
				assert (np.issubdtype(value.dtype, np.integer) or
					np.issubdtype(value.dtype, np.floating)), "value.dtype is %s" % value.dtype
				# was using np.dtype(float).type
			vtype = 'i' if np.issubdtype(value.dtype, np.integer) else 'f'
			sval = None
			# vtype = 'n'
		else:
			print("unknown generic type %s, value=%s at %s" % (type(value), value, attribute_path))
			import pdb; pdb.set_trace()
			return None
	elif isinstance(value, (bytes, str)):
		vtype = "s"	# s - single string
		sval = value
		nval = None
		if isinstance(sval, bytes):
			sval = sval.decode("utf-8")
	elif isinstance(value, (int, float)):
		vtype = "i"	if isinstance(value, int) else 'f'
		sval = None
		nval = value
		if math.isnan(nval):
			nval="nan"
	elif isinstance(value, h5py.h5r.Reference):
		 #print ("found object reference in attribute at %s" % attribute_path)
		nval = None
		sval = fp[value].name
		vtype = "s"
	else:
		print("unknown type %s value %s at %s" % type(value), value, attribute_path)
		import pdb; pdb.set_trace()
		return None
	value_id = value_mirror.get_id(vtype, nval, sval)
	return value_id


def get_value_id_from_dataset(node, base_name, parent_id, parent_node):
	global fp, value_mirror, groups_with_colnames_attribute
	global MAX_STRING_LENGTH, MAX_STRING_ARRAY_LENGTH, MAX_PACKED_STRING_LENGTH
	global MAX_NWB2_TABLE_SIZE, MAX_NWB2_PACKED_STRING_LENGTH, MAX_NWB2_TABLE_NUMBER_OF_COLUMNS
	if node.size == 0:
		# don't save anything if dataset is empty or too large
		return None
	scalar = len(node.shape) == 0
	if parent_id in groups_with_colnames_attribute:
		if not (base_name == "id"
			or base_name in groups_with_colnames_attribute[parent_id]):
			# this should probably never happen
			print ("dataset inside group with colnames not listed in colnames: %s" % node.name)
			import pdb; pdb.set_trace()
		# this dataset is part of a table, save it even if numeric
		assert not scalar, "Found scalar value where table value expected, %s" % node.name
		# check for "_index" dataset that is associated with this dataset
		# "_index" dataset should not be saved directly here, or listed in colnames
		assert not base_name.endswith("_index"), "dataset ends with _index, should not happen: %s" % node.name
		index_name = base_name + "_index"
		if index_name in parent_node:
			index_dataset = parent_node[index_name]
			assert np.issubdtype(index_dataset.dtype, np.integer) or np.issubdtype(index_dataset.dtype, np.float), ( 
				"_index dataset is not integer or float (%s): %s") % (index_dataset.dtype, index_dataset.name)
			assert len(index_dataset.shape) == 1, "_index dataset should be 1-d: %s" % index_dataset.name
			# will create string for storing index values, separated from other values by 'i'
			index_values = index_dataset[()]  # was dataset.value which is depreciated
		else:
			# index_values = ""
			index_values = None
		# done getting _index values (if present), now get value for node
		if len(node.shape) > 1:
			# found dataset with more than one dimension
			if (node.size > MAX_NWB2_TABLE_SIZE or len(node.shape) > 2
				or node.shape[1] > MAX_NWB2_TABLE_NUMBER_OF_COLUMNS):
				# Don't store if too big, e.g. image mask table
				# or if is more then 2 dimensions or if too many columns
				return None
			# have 2-d array, all elements of same type.  Append type code to each column name anyway
			colnames = [str(i) for i in range(node.shape[1])] # subscript names are column numbers
			# colnames = []
			coldata = [ node[:,i] for i in range(node.shape[1]) ]
			# in_table = True
			sval, vtype = pack_values.pack(coldata, index_vals=index_values,
				 col_names=colnames, in_table=True, node_path=node.name, fp=fp)
			assert vtype == 'c'
			nval = None
		elif len(node.dtype) > 1:
			# found compound type
			if node.size * len(node.dtype) > MAX_NWB2_TABLE_SIZE:
				print('Warning: not indexing compound type because too big (size=%i, limit=%i), at %s'
					% (node.size * len(node.dtype), MAX_NWB2_TABLE_SIZE, node.name))
				# don't save compound type if is too big
				return None
			colnames = []
			coldata = []
			# in_table = True
			for cn in node.dtype.names:
				colnames.append(cn)
				coldata.append(node[cn])
			sval, vtype = pack_values.pack(coldata, index_vals=index_values,
				 col_names=colnames, in_table=True, node_path=node.name, fp=fp)
			nval = None
			assert vtype == 'c'
		elif np.issubdtype(node.dtype, np.number) or np.issubdtype(node.dtype, np.dtype(bool).type):
			# found numeric dataset
			if node.size > MAX_NWB2_TABLE_SIZE:
				# don't save if larger than a threshold
				print('Warning: not indexing numeric array because too big (size=%i, limit=%i), at %s' %
				 (node.size, MAX_NWB2_TABLE_SIZE, node.name))
				return None
			sval, vtype = pack_values.pack([node[()],], index_vals=index_values,
				 in_table=True, node_path=node.name, fp=fp)
			assert vtype in ("I", "F", "J", "G")
			nval =  None
		elif np.issubdtype(node.dtype, np.character) or isinstance(node[0], h5py.Reference):
			# found string dataset or object references (replaced by path to node)
			sval, vtype = pack_values.pack([node[()],], index_vals=index_values,
				 in_table=True, node_path=node.name, fp=fp)
			if len(sval) > MAX_NWB2_PACKED_STRING_LENGTH:
				print("Warning: not indexing string array because too large "
					"(packed size = %i, limit = %i), at '%s'" % (len(sval),
						MAX_NWB2_PACKED_STRING_LENGTH, node.name))
				return None	
			nval = None
			assert vtype in ("M", "B")
		else:
			vlenType = h5py.check_dtype(vlen=node.dtype)
			if vlenType in (bytes, str):
				sval, vtype = pack_values.pack([node[()].tolist(),], index_vals=index_values,
				 in_table=True, node_path=node.name, fp=fp)
				assert vtype in ("M", "B")
				nval = None
				if len(sval) > MAX_NWB2_PACKED_STRING_LENGTH:
					print("Warning: not indexing vlen string array because too large "
					"(packed size = %i, limit = %i), at '%s'" % (len(sval),
						MAX_NWB2_PACKED_STRING_LENGTH, node.name))
					# don't save if total length of string longer than a specific length
					return None
				nval = None
				# vtype = "M"
			else:
				print ("unable to determine type of dataset value at: %s" % node.name)
				import pdb; pdb.set_trace()
				return None
	# not part of table
	elif np.issubdtype(node.dtype, np.number) or np.issubdtype(node.dtype, np.dtype(bool).type):
		# found numeric dataset
		if node.size == 1:
			if np.issubdtype(node.dtype, np.integer) or np.issubdtype(node.dtype, np.dtype(bool).type):
				nval = int(node[()]) if scalar else int(node[()][0])
				vtype = "i"
			else:
				nval = float(node[()]) if scalar else float(node[()][0])
				vtype = "f"
			if math.isnan(nval):
				nval="nan"
			sval = None
		else:
			return None		# don't save numeric arrays with more than one element
	elif np.issubdtype(node.dtype, np.character):
		# found string dataset
		if scalar:
			sval = node[()]
			if len(sval) > MAX_STRING_LENGTH:
				# don't save strings longer than a specific length
				return None
			if isinstance(sval, bytes):
				sval = sval.decode("utf-8")  # store as string, not bytes
			nval = None
			vtype = "s"
		elif node.len() > MAX_STRING_ARRAY_LENGTH:
			# don't save if more than 20 elements in string array
			return None
		else:
			sval, vtype = pack_values.pack([node[()].tolist(),], node_path=node.name, fp=fp)
			if len(sval) > MAX_PACKED_STRING_LENGTH:
				# don't save if total length of string longer than a specific length
				return None
			nval = None
			assert vtype == "S"
	else:
		vlenType = h5py.check_dtype(vlen=node.dtype)
		if vlenType in (bytes, str):
			# found variable length string
			if scalar:
				# simple string in object.  Get value by node[()]
				sval = node[()]
				if isinstance(sval, bytes):
					sval = sval.decode("utf-8")  # store as string, not bytes
				if len(sval) > MAX_STRING_LENGTH:
					return None
				vtype = "s"	# s - single (scalar) string
				nval = None
			else:
				if node.len() > MAX_STRING_ARRAY_LENGTH:
					return None
				sval, vtype = pack_values.pack([node[()].tolist(),], node_path=node.name, fp=fp)
				nval = None
				if len(sval) > MAX_PACKED_STRING_LENGTH:
					# don't save if total length of string longer than a specific length
					return None
				nval = None
				assert vtype == "S"
		elif scalar and isinstance(node[()], h5py.Reference):
			# print ("found scalar object reference in dataset at %s" % node.name)
			sval = fp[node[()]].name
			nval = None
			vtype = "s"
		elif not scalar and isinstance(node[0], h5py.Reference):
			# print ("found dataset array object reference in dataset at %s" % node.name)
			nval = None
			value = [fp[n].name for n in node[()]]
			if len(value) > 1:
				sval, vtype = pack_values.pack([ value, ], node_path=node.name, fp=fp)
				if len(sval) > MAX_PACKED_STRING_LENGTH:
					# don't save if total length of string longer than a specific length
					return None
				assert vtype == "S"
			else:
				sval = value[0]
				vtype = 's'
		else:
			print ("unable to determine type of dataset value at: %s" % node.name)
			import pdb; pdb.set_trace()
			return None
	# if makes is here, should be able to get value_id
	value_id = value_mirror.get_id(vtype, nval, sval)
	return value_id

def visit_nodes(fp):
	# visit all nodes (groups and datasets) in file
	# fp is the h5py File object
	# to_visit is a list of all nodes that need to visit
	# each element is a tuple (node, parent_id, parent_node).  Start with root 
	to_visit = [ (fp, None, None) ]
	while to_visit:
		node, parent_id, parent_node = to_visit.pop(0)
		node_id = get_node_id(node, parent_id, parent_node)
		if isinstance(node,h5py.Group):
			for child in sorted(node):
				try:
					cn = node[child]
				except:
					# unable to access this node.  Perhaps a broken external link.  Ignore
					continue
				to_visit.append( (cn, node_id, node))

def scan_file(path):
	global file_id, con, fp
	con.execute("begin")  # begin transaction
	file_id = find_file_id(path)
	if file_id is not None:
		print("Skipping (already indexed) %i. %s" % (file_id, path))
		con.commit()
		return
	fp = h5py.File(path, "r")
	if not fp:
		sys.exit("Unable to open %s" % path)
	file_id = get_file_id(path)
	print ("Scanning file %i: %s" % (file_id, path))
	visit_nodes(fp)
	con.commit()
	fp.close()

def scan_directory(dir):
	for root, dirs, files in os.walk(dir, followlinks=True):
		dirs.sort()
		for file in sorted(files, key=str.casefold):
			if file.endswith("nwb"):
				scan_file(os.path.join(root, file))

def main():
	global con, value_mirror, default_dbname
	num_parameters = len(sys.argv)
	if num_parameters < 2 or num_parameters > 3:
		print('Usage: %s <nwb_directory> [ <index_path> ]' % sys.argv[0])
		print("Where:")
		print('    <nwb_directory> - name of directory to scan for NWB files (extension ".nwb")')
		print("    <index_path> - path to index file:")
		print("         If nothing is specified, uses '%s' in the current directory." % default_dbname)
		print("         If only a directory is specified, uses '%s' in the specified directory." % default_dbname)
		sys.exit()
	if not os.path.isdir(sys.argv[1]):
		sys.exit('ERROR: directory %s was not found!' % sys.argv[1])
	dir = sys.argv[1]
	if num_parameters == 3:
		if os.path.isdir(sys.argv[2]):
			# directory specified, use default_dbname inside directory
			db_path = os.path.join(sys.argv[2], default_dbname)
		else:
			# file specified, use as dbname
			db_path = sys.argv[2]
	else:
		db_path = default_dbname
	open_database(db_path)
	initialize_caches()
	print ("scanning directory %s" % dir)
	scan_directory(dir)
	con.close()

if __name__ == "__main__":
	main()

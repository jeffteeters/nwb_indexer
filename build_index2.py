import sys
import os
import h5py
import sqlite3
import numpy as np
import math

dbname="nwb_idx2.db"
con = None     # database connection
file_id = None # id of current file (row inf h5file table)
cur = None       # cursor


# sqlite3 database schema
schema='''
create table prenom (		-- all names (file names and path parts; 'prenom' is french for given name)
	id integer primary key, -- (The main reason this table is not named "name" is there is another table
	name text not null 		-- "node" which starts with "n".  For aliases it's nice to have table names
							-- start with different letters).
);
-- create index name_idx on prenom(name);  -- not sure if this helps

create table file (				-- hdf5 files
	id integer primary key,
	prenom_id integer not null references prenom  -- prenom contains full path to file 
);

create table node (  -- stores groups, dataseta AND attributes
	id integer primary key,
	file_id integer not null references file,
	parent_id integer references node, -- parent group (if group or dataset) or parent group or dataset (if attribute)
	prenom_id integer not null references prenom, -- name of this node (last component of full path)
	node_type char(1) not null,	-- either: g-group, d-dataset, a-attribute
	value_id integer references value	-- value associated with dataset or attribute.
		-- NULL if group or if value is not saved (dataset or attribute with multiple dimensions)
);

create table value (			-- value of dataset or attribute
	id integer primary key,
	type char(1) not null,		-- either: n-number, s-string, N-number array, S-string array, c-compound
	-- compound_cols text,		-- comma seperated list of columns names if compound type, otherwise NULL
	nval real,					-- contains value of number, if type 'n'.  Otherwise, NULL
	sval text					-- stores values of type s, N, S, c as comma seperated values otherwise NULL
		-- if type 'c', has list of columns names first, then lists of column values, lists seperated by ';'
);

create index nval_idx on value(nval) where nval is not NULL;  -- Help speedup searches for scalars
create index sval_idx on value(sval) where type = 's';
''';

# create table value (			-- value of dataset or attribute
# 	id integer primary key,
# 	type char(1) not null,		-- either: n-number, s-string, N-number array, S-string array
# 								-- u - unknown (value not stored, might be too large)
# 	nval real,					-- contains value of number, if type 'n'.  Otherwise, NULL
# 	string_id integer			-- index of value in array string (if stored there), otherwise NULL
# );

# create table string (			-- stores all values (type s, N, S) as comma seperated values
# 	id integer primary key,
# 	value text not null
# );


# class Path_id:
# 	path_map = {}


# FOLLOWING NOT USED BECAUSE: table string not used anymore.  Table prenom stored directly without map
# because prenom names must be referenced by entries in node table
# class Vmap:
# 	# maps value to id
# 	# used for prenom and string table
# 	def __init__(self, table_name, value_name):
# 		# maps values to id
# 		self.map = {}
# 		self.table_name = table_name
# 		self.value_name = value_name
# 		self.load_map()

# 	def get_id(self, value):
# 		# get id corresponding to value (which must be a string). Will add value to map if not present
# 		assert isinstance(value, str)
# 		if v in self.map:
# 			key = self.map[v][0]  # key is the id
# 		else:
# 			key = len(self.map) + 1
# 			self.vmap[value] = (key, 'new')  # save indicator if record is new

# 	def load_map(self):
# 		# load values from table.  Needed if updating database
# 		global con, cur
# 		assert len(self.map) == 0, "load_map for table '%s' called, but map not empty" % self.table_name
# 		result = cur.execute("select id, %s from %s order by %s" % (self.value_name, self.table_name, self.value_name))
# 		for row in result:
# 			key, value = row
# 			self.map[value] = (key, 'old')  # save indicator that record is already in database

# 	def save_map(self, table_name, value_name):
# 		# saves map in the database
# 		global con, cur
# 		# execute insert statements
# 		for key, vt in sorted(self.map.items(), key = lambda kv:(kv[1], kv[0])):
# 			if vt[1] == 'new':  # only save new records
# 				cur.execute("insert into %s (id, %s) values (?, ?)" % (self.table_name, self.value_name), (key, vt[0]))

# New strategy: have cache for prenom, to enable quick lookup of prenom_id

class Prenom_cache:
	# cache values for prenom to allow quick lookup of prenom_id
	# used for prenom and string table
	def __init__(self):
		# maps values to id
		self.cache = {}
		self.load_cache()

	def get_id(self, pname):
		global cur
		# get id corresponding to value (which must be a string). Will add value to map if not present
		assert isinstance(pname, str)
		if pname in self.cache:
			pid = self.cache[pname]  # prenom id, 'p' stands for prenome
		else:
			pid = len(self.cache) + 1
			self.cache[pname] = pid  # save indicator if record is new
			cur.execute("insert into prenom (id, name) values (?, ?)", (pid, pname))
		return pid

	def load_cache(self):
		# load prenom values from table.  Needed if updating database
		global cur
		assert len(self.cache) == 0, "Prenom_cache load_cache called, but cache not empty"
		result = cur.execute("select id, name from prenom order by id")
		for row in result:
			pid, pname = row
			self.cache[pname] = pid


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
			if vtype == 'n':
				self.nval2id[nval] = id
			elif sval is not None:
				self.sval2id[sval] = id
		self.original_length = len(self.mirror)  # save original length of table (so will know what is new)

	def get_id(self, vtype, nval, sval):
		global cur
		assert vtype in ('n', 'N', 's', 'S', 'c'), 'value vtype invalid: "%s"' % vtype
		if vtype == 'n':
			assert (isinstance(nval, int) or isinstance(nval, float) or nval == "nan") and sval is None, (
				"value type 'n' not consistent, nval=%s, type=%s, sval=%s, type=%s" %
				(nval, type(nval),sval, type(sval)))
			if nval in self.nval2id:
				vid = self.nval2id[nval]
			else:
				vid = len(self.mirror) + 1
				self.mirror.append ( (vid, vtype, nval, sval) )
				self.nval2id[nval] = vid
				cur.execute("insert into value (id, type, nval, sval) values (?, ?, ?, ?)" , (
					vid, vtype, nval, sval) )
		else:
			assert isinstance(sval, str) and nval is None, ( 
				"value type 's' not consisitent, sval='%s', type=%s, nval=%s" % (sval, type(sval), nval))
			if sval in self.sval2id:
				vid = self.sval2id[sval]
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
				self.sval2id[sval] = vid
		return vid

	# def save_mirror(self):
	# 	# saves value table mirror in the database
	# 	global con, cur
	# 	# execute insert statements
	# 	for i in range(self.original_length, len(self.mirror)):
	# 		# only save new entries (specified by original_length)
	# 		cur.execute("insert into value (id, type, nval, sval) values (?, ?, ?, ?)" % self.mirror[i])

# save id's (node.id) of groups that have the column names attribute.  This used to determine if values
# should be saved, for NWB 2.x tables with aligned columns or compound tables.
groups_with_colnames_attribute = []


def open_database():
	global dbname, schema
	global con, cur
	# for testing
	if os.path.isfile(dbname):
		print("removing previous database %s" % dbname)
		os.remove(dbname)
	if not os.path.isfile(dbname):
		print("Creating database '%s'" % dbname)
		con = sqlite3.connect(dbname)
		cur = con.cursor()
		cur.executescript(schema);
		con.commit()
	else:
		print("Opening existing database: %s" % dbname)
		con = sqlite3.connect(dbname)
		cur = con.cursor()

def initialize_caches():
	global value_mirror, prenom_cache
	prenom_cache = Prenom_cache()
	value_mirror = Value_mirror()


# def get_path_id(name):
# 	global con, cur
# 	cur.execute("select id from path where name=?", (name,))
# 	row = cur.fetchone()
# 	if row is None:
# 		cur.execute("insert into path (name) values (?)", (name,))
# 		con.commit()
# 		path_id = cur.lastrowid
# 	else:
# 		# name was already stored
# 		path_id = row[0]
# 	return path_id

def get_prenom_id(name):
	global prenom_cache
	return prenom_cache.get_id(name)


# def get_prenom_id_not_used(name):
# 	global con, cur
# 	cur.execute("select id from prenom where name=?", (name,))
# 	row = cur.fetchone()
# 	if row is None:
# 		cur.execute("insert into prenom (name) values (?)", (name,))
# #		con.commit()
# 		prenom_id = cur.lastrowid
# 	else:
# 		# name was already stored
# 		prenom_id = row[0]
# 	return prenom_id

# def get_prenom_id(name):
# 	global prenom_map
# 	return prenom_map.get_id(name)


def find_file_id(name):
	# return file_id if have file in database, otherwise None
	global con, cur
	# path_id = get_path_id(name)
	# cur.execute("select id from file where path_id = ?", (path_id,))
	prenom_id = get_prenom_id(name)
	cur.execute("select id from file where prenom_id = ?", (prenom_id,))
	row = cur.fetchone()
	if row is None:
		file_id = None
	else:
		file_id = row[0]
	return file_id

def get_file_id(name):
	global con, cur
	file_id = find_file_id(name)
	if file_id is None:
		# path_id = get_path_id(name)
		# cur.execute("insert into file (path_id) values (?)", (path_id,))
		prenom_id = get_prenom_id(name)
		cur.execute("insert into file (prenom_id) values (?)", (prenom_id,))
#		con.commit()
		file_id = cur.lastrowid
	print("file_id is %i" % file_id)
	return file_id

# def get_parent_id_not_used(name):
# 	global con, cur, file_id
# 	if name == "":
# 		parent_id = None  # root has no parent
# 	else:
# 		return 1  # for testing speed
# 		# Must generate sql query to get parent id.  parent is the node with path
# 		# equal to the path parts, except for the last component
# 		path_parts = name.split('/')[0:-1]
# 		parent_depth = len(path_parts)  # depth of parent, 0 depth is root
# 		select_start = "select n%i.id " % parent_depth
# 		from_clause = ["\nfrom node n0"]
# 		where_clause = ["\nwhere n0.parent_id is NULL", "n0.file_id = %i" % file_id]
# 		depth = 0
# 		for path in path_parts:
# 			depth += 1
# 			from_clause.append( "node n%i, prenom p%i" % (depth, depth))
# 			where_clause.append( "n%i.parent_id = n%i.id and n%i.prenom_id = p%i.id and p%i.name = ?" %
# 				(depth, depth-1, depth, depth, depth ))
# 		sql = select_start + ", ".join(from_clause) + " and ".join(where_clause)
# 		result = cur.execute(sql, path_parts)
# 		rows=result.fetchall()
# 		assert len(rows) == 1, "expected to find 1 node for parent of: %s, but found %i, sql=\n%s,\npath_parts=%s" % (
# 			name, len(rows), sql, path_parts)
# 		parent_id = rows[0][0]
# 	return parent_id


# def get_parent_id_old(name):
# 	global con, cur, file_id
# 	if name == "":
# 		parent_id = None  # root has no parent
# 	else:
# 		parent_name, name2 = os.path.split(name)
# 		path_id = get_path_id(parent_name)
# 		cur.execute("select id from node where file_id = ? and path_id = ?", (file_id, path_id,))
# 		row = cur.fetchone()
# 		if row is not None:
# 			parent_id = row[0]
# 		else:
# 			sys.exit("Unable to find parent for: '%s'" % name)
# 	return parent_id

def save_group(node, parent_id):
	global con, cur, file_id, groups_with_colnames_attribute
	# full_name = node.name
	base_name = node.name.split('/')[-1]
	prenom_id = get_prenom_id(base_name)
	node_type = "g"		# indicates group
	value_id = None
	cur.execute("insert into node (file_id, parent_id, prenom_id, node_type, value_id) values (?, ?, ?, ?, ?)", 
			(file_id, parent_id, prenom_id, node_type, value_id))
#	con.commit()
	group_id = cur.lastrowid
	# save attributes
	for key in node.attrs:
		if key == "colnames":
			groups_with_colnames_attribute.append(group_id)
		value = node.attrs[key]
		save_attribute(group_id, key, value, node.name + "-" + key)
	return group_id

def save_dataset(node, parent_id):
	global con, cur, file_id
	# full_name = node.name
	base_name = node.name.split('/')[-1]
	prenom_id = get_prenom_id(base_name)
	value_id = get_value_id_from_dataset(node, parent_id)
	node_type = "d"  # dataset
	cur.execute("insert into node (file_id, parent_id, prenom_id, node_type, value_id) values (?, ?, ?, ?, ?)", 
			(file_id, parent_id, prenom_id, node_type, value_id))
#	con.commit()
	dataset_id = cur.lastrowid
	# save attributes
	for key in node.attrs:
		value = node.attrs[key]
		save_attribute(dataset_id, key, value, node.name + "-" + key)
	return dataset_id

def save_attribute(parent_id, key, value, attribute_path):
	global con, cur, file_id
	prenom_id = get_prenom_id(key)
	value_id = get_value_id_from_attribute(value, attribute_path)
	node_type = "a"		# indicates attribute
	cur.execute("insert into node (file_id, parent_id, prenom_id, node_type, value_id) values (?, ?, ?, ?, ?)",
		(file_id, parent_id, prenom_id, node_type, value_id))
#	con.commit()

# count = 0;
# def save_node(name, node):
# 	global count
# 	if isinstance(node,h5py.Group):
# 		save_group(name, node)
# 	elif isinstance(node,h5py.Dataset):
# 		save_dataset(name, node)
# 	else:
# 		sys.exit("Unknown node type in save_node: %s" % node)
# 	count += 1
# 	# if count > 10:
# 	# 	count = 0
# 	# 	return 1
# 	return None

def get_node_id(node, parent_id):
	if isinstance(node,h5py.Group):
		node_id = save_group(node, parent_id)
	elif isinstance(node,h5py.Dataset):
		node_id = save_dataset(node, parent_id)
	else:
		sys.exit("Unknown node type in get_node_id: %s" % node)
	return node_id

# save inventory of value types, each key is the type of the value, the value of the dict is a tuple
# of count and first 5 locations
value_types = { "attribute": { }, "dataset": {}}

# global variable for saving count of unknown types
unknown_types = {}

def clear_unknown_types():
	global unknown_types
	unknown_types = {}

def count_unknown_type(utype):
	global unknown_types
	if utype in unknown_types:
		unknown_types[utype] += 1
	else:
		unknown_types[utype] = 1

def show_unknown_types():
	global unknown_types
	if len(unknown_types) > 0:
		print ("Count of unknown types found:")
		for utype in sorted(unknown_types.keys()):
			print("%s\t%i" % (utype, unknown_types[utype]))


def show_unknown_types():
	global unknown_types
	if len(unknown_types) > 0:
		print ("Count of unknown types found:")
		for utype in sorted(unknown_types.keys()):
			print("%s\t%i" % (utype, unknown_types[utype]))

# from: https://stackoverflow.com/questions/39502461/truly-recursive-tolist-for-numpy-structured-arrays
def array_to_list(array):
    if isinstance(array, np.ndarray):
        return array_to_list(array.tolist())
    elif isinstance(array, list):
        return [array_to_list(item) for item in array]
    elif isinstance(array, tuple):
        return tuple(array_to_list(item) for item in array)
    else:
        return array

def convert_to_list(cloc_vals):
	if isinstance(cloc_vals, np.ndarray):
		list_vals = array_to_list(cloc_vals) # convert numpy ndarray to list
	else:
		list_vals = [cloc_vals, ]  # convert scalar to list with one element
	return list_vals


def get_value_id_from_attribute(value, attribute_path):
	global fp, value_mirror
	if isinstance(value, np.ndarray):
		if len(value.shape) > 1:
			# for dataset, would need to check for 2-d table
			return None
		if len(value) == 0:
			return None	# don't save zero length values
		if np.issubdtype(value.dtype, np.number):
			if len(value) > 1:
				# don't save values of numeric arrays, only scalars
				return None
			nval = value[0].item()	# get numeric value
			if math.isnan(nval):
				nval="nan"
			sval = None
			vtype = 'n'
		elif np.issubdtype(value.dtype, np.character):
			# found array of strings
			assert isinstance(value[0], bytes), "expecting string value bytes, found %s (%s) at %s " % (
			value, type(value), attribute_path)
			nval = None
			if len(value) == 1:
				sval = value[0].decode("utf-8")
				vtype = 's'	# single string
			else:
				if len(value) > 20:
					# don't save string arrays longer than 20 elements
					return None
				sval = (b"'" + b"','".join(value) + b"'").decode("utf-8")	# join bytes, seperate by ','
				vtype = "S" # string array
		elif isinstance(value[0], h5py.h5r.Reference):
			print ("found object reference in attribute at %s" % attribute_path)
			nval = None
			value = [fp[n].name for n in value]
			if len(value) > 1:
				sval = "'" + "','".join(value) + "'"
				vtype = "S"
			else:
				sval = value[0]
				vtype = 's'
		else:
			print("unknown type %s value %s at %s" % type(value[0]), value[0], attribute_path)
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
			sval = None
			vtype = 'n'
		else:
			print("unknown generic type %s, value=%s at %s" % (type(value), value, attribute_path))
			return None
	elif isinstance(value, (bytes, str)):
		vtype = "s"	# s - single string
		sval = value
		nval = None
		if isinstance(sval, bytes):
			sval = sval.decode("utf-8")
	elif isinstance(value, (int, float)):
		vtype = "n"	# s - single string
		sval = None
		nval = value
		if math.isnan(nval):
			nval="nan"
	elif isinstance(value, h5py.h5r.Reference):
		print ("found object reference in attribute at %s" % attribute_path)
		nval = None
		sval = fp[value].name
		vtype = "s"
	else:
		print("unknown type %s value %s at %s" % type(value), value, attribute_path)
		return None
	value_id = value_mirror.get_id(vtype, nval, sval)
	return value_id

def get_value_id_from_dataset(node, parent_id):
	global fp, value_mirror, groups_with_colnames_attribute
	if node.size == 0:
		# don't save anything if dataset is empty or too large
		return None
	scalar = len(node.shape) == 0
	if len(node.shape) > 1:
		# found dataset with more than one dimension
		if (parent_id not in groups_with_colnames_attribute or node.size > 10000 or
			len(node.shape) > 2 or node.shape[1] > 10):
			# don't store values of multidimensional arrays unless in table group
			# also, don't store if too big, e.g. image mask table
			# or if is more then 2 dimensions or if more than 10 columns (arbituary cutoff)
			return None
		# print("found dataset with shape > 1, inside table group: %s" % node.name)
		colnames = ','.join([ "%i" % i for i in range(node.shape[1]) ])
		coldata = ';'.join(format_column(node[:,i], node) for i in range(node.shape[1]))
		sval = colnames + '%' + coldata
		nval = None
		vtype = 'c'
	elif len(node.dtype) > 1:
		# found compound type
		if parent_id not in groups_with_colnames_attribute or (node.size * len(node.dtype)) > 10000:
			# don't save compound type if not in table group or if is too big
			return None
		assert not scalar, "scalar compound type not supported. found at %s" % node.name
		colnames = ','.join(node.dtype.names)
		coldata = ';'.join(format_column(node[cn], node) for cn in node.dtype.names)
		sval = colnames + '%' + coldata
		nval = None
		vtype = 'c'	
	elif np.issubdtype(node.dtype, np.number):
		# found numeric dataset
		if node.size == 1:
			vtype = "n"	# n - single number
			nval = float(node[()]) if scalar else float(node.value[0])
			if math.isnan(nval):
				nval="nan"
			sval = None
		else:
			return None		# don't save numeric arrays with more than one element
	elif np.issubdtype(node.dtype, np.character):
		# found string dataset
		if scalar:
			sval = node[()]
			if len(sval) > 10000:
				# don't save strings longer than a specific length
				return None
			if isinstance(sval, bytes):
				sval = sval.decode("utf-8")  # store as string, not bytes
			nval = None
			vtype = "s"
		elif node.len() > 20:
			# don't save if more than 20 elements in string array
			return None
		else:
			vlist = node.value.tolist()
			if isinstance(vlist[0], bytes):
				sval = b"'" + b"','".join(vlist) + b"'"	# join bytes
				sval = sval.decode("utf-8")
			else:
				sval = "'" + "','".join(vlist) + "'"	# join string
			if len(sval) > 10000:
				# don't save if total length of string longer than a specific length
				return None
			nval = None
			vtype = "S"
	else:
		vlenType = h5py.check_dtype(vlen=node.dtype)
		if vlenType in (bytes, str):
			# found variable length string
			if scalar:
				# simple string in object.  Get value by node[()]
				sval = node[()]
				if isinstance(sval, bytes):
					sval = sval.decode("utf-8")  # store as string, not bytes
				if len(sval) > 10000:
					return None
				vtype = "s"	# s - single (scalar) string
				nval = None
			else:
				if node.len() > 20:
					return None
				vlist = node.value.tolist()
				if isinstance(vlist[0], bytes):
					sval = b"'" + b"','".join(vlist) + b"'"	# join bytes
					sval = sval.decode("utf-8")
				else:
					sval = "'" + "','".join(vlist) + "'"	# join string
				if len(sval) > 10000:
					# don't save if total length of string longer than a specific length
					return None
				nval = None
				vtype = "S"
		elif scalar and isinstance(node[()], h5py.Reference):
			print ("found scalar object reference in dataset at %s" % node.name)
			sval = fp[node[()]].name
			nval = None
			vtype = "s"
		elif not scalar and isinstance(node[0], h5py.Reference):
			print ("found dataset array object reference in dataset at %s" % node.name)
			nval = None
			value = [fp[n].name for n in node.value]
			if len(value) > 1:
				sval = "'" + "','".join(value) + "'"
				vtype = "S"
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

def format_column(col, node):
	global fp
	assert len(col) > 0, "attempt to format empty column at %s" % node.name
	if isinstance(col[0], bytes):
		fmt = (b"'" + b"','".join(col) + b"'").decode("utf-8")
	elif isinstance(col[0], str):
		fmt = "'" + "','".join(col) + "'"
	elif isinstance(col[0], (int, float)):
		fmt = ",".join(["%s" % x for x in col])
	elif isinstance(col[0], np.number):
		fmt = ",".join(["%s" % x.item() for x in col])  # convert to python type
	elif isinstance(col[0], h5py.h5r.Reference):
		fmt = "'" + "','".join([fp[x].name for x in col]) + "'"  # convert reference to name of target
	else:
		sys.exit("unknown type (%s) when formatting column at %s" % (type(col[0]), node.name))
	return fmt


	# format an 1-d array of values as a comma separated string


	# 	else:
	# 		value = [v.item() for v in value ]  # convert to python type
	# 	if 
	# if not isinstance(value, np.ndarray):
	# 	print ("type is %s at %s" % (type(value), attribute_path))
	# 	import pdb; pdb.set_trace()
	# value = convert_to_list(value)  # if nympy ndarray, convert to python type
	# if len(value) > 0 and isinstance(value[0], h5py.h5r.Reference):
	# 	print ("found object reference")
	# 	import pdb; pdb.set_trace
	# 	# assume array of object references.  Convert to strings (names of objects)
	# 	value = [fp[n].name for n in value]
	# if len(value) > 0:
	# 	save_value_type(value[0], attribute_path)
	# else:
	# 	return None	# if nothing stored, don't save it
	# return None  # for testing
	# if isinstance(value, (np.ndarray, np.generic)):
	# 	value_id = get_value_id_from_numpy_array(value)
	# else:
	# 	value_id = get_value_id_from_normal_python_type(value)
	# return value_id

def get_value_id_from_numpy_array(value):
	global value_mirror
	nval = None		# default values for number and string index
	sval = None
	size = value.size
	is_numeric = np.issubdtype(value.dtype, np.number)
	is_string = np.issubdtype(value.dtype, np.character) or isinstance(value, object)
	if is_numeric:
		if size == 1:
			vtype = "n"	# n - single number
			nval = float(value)
			if math.isnan(nval):
				nval="nan"
		else:
			vtype = "N"	# N - array.  For now, these are not saved. May need to be if compound
			return None
	elif is_string:
		if size <= 1:
			vtype = "s"	# s - single string
			sval = value
			if not isinstance(value, np.bytes_):
				import pdb; pdb.set_trace()
			if isinstance(sval, bytes):
				sval = sval.decode("utf-8")
		elif size < 20:
			vtype = "S"	# S - array
			vlist = value.tolist()
			if len(vlist) == 0:
				print("found zero length list")
				import pdb; pdb.set_trace()
			if isinstance(vlist[0], bytes):
				sval = b"'" + b"'".join(vlist) + b"'"	# join bytes
				sval = sval.decode("utf-8")
			else:
				sval = "'" + "'".join(vlist) + "'"	# join characters
		else:
			vtype = "T"	# Too big string array, don't save value
			return None
	value_id = value_mirror.get_id(vtype, nval, sval)
	return value_id

# def get_value_id_from_normal_python_type(value, attribute_path):
# 	global value_mirror, fp
# 	# node is not dataset or numpy type, must be regular python type
# 	if isinstance(value, (bytes, str)):
# 		vtype = "s"	# s - single string
# 		sval = value
# 		nval = None
# 		if isinstance(sval, bytes):
# 			sval = sval.decode("utf-8")
# 	elif isinstance(value, (int, float)):
# 		vtype = "n"	# s - single string
# 		sval = None
# 		nval = value
# 	elif isinstance(value, h5py.h5r.Reference):
# 		print ("found object reference in attribute at %s" % attribute_path)
# 		nval = None
# 		sval = fp[value].name
# 		vtype = "s"
# 	elif isinstance(value, (list, tuple)):
# 		if len(value) == 0:
# 			# don't save value if empty array
# 			return None
# 		if instance(value[0], (int, float)):
# 			if len(value) > 1:
# 				# don't save numeric arrays longer than 1 element (scalars)
# 				return None
# 			nval = value[0]
# 			sval = None
# 			vtype = 'n'	
# 		elif isinstance(value[0], (bytes, str)):
# 			if len(value) > 20:
# 				# don't save list of strings longer than 20 elements
# 				return None
# 			nval = None
# 			if len(value) == 1:
# 				vtype = "s"
# 				sval = value[0]
# 				if isinstance(sval, bytes):
# 					sval = sval.decode("utf-8")
# 			else:
# 				vtype = "S"	# indicates string array
# 				if isinstance(value[0], bytes):
# 					sval = (b"'" + b"','".join(value) + b"'").decode("utf-8")	# join bytes and decode
# 				else:
# 					sval = "'" + "','".join(vlist) + "'"	# join characters
# 		elif isinstance(value[0], h5py.h5r.Reference):
# 			print ("found object reference in attribute array at %s" % attribute_path)
# 			nval = None
# 			value = [fp[n].name for n in value]
# 			if len(value) > 1:
# 				sval = "'" + "','".join(value) + "'"
# 				vtype = "S"
# 			else:
# 				sval = value[0]
# 				vtype = 's'
# 		else:
# 			print("unknown type %s value %s at %s" % type(value[0]), value[0], attribute_path)
# 			return None

# 			vtype = "T"	# too big string array
# 			return None
# 		else:
# 			if isinstance(node[0], (int, float)):
# 				vtype = "N"	# numeric array, don't save
# 				return None
# 			else:
# 				type_code = "U"	# unkown contents of array
# 				count_unknown_type(str(type(node[0])) + "-" + type_code)
# 				# print("Unknown type (%s) in array, saving %s", (type(node), node))
# 				# import pdb; pdb.set_trace()
# 				return None
# 	elif isinstance(node, (int, float)):
# 		nval = float(node)
# 		if math.isnan(nval):
# 			nval="nan"
# 		vtype = "n"
# 	else:
# 		vtype = "u"	# unknown single value
# 		count_unknown_type(str(type(node)) + "-" + type_code)
# 	value_id = value_mirror.get_id(vtype, nval, sval)
# 	return value_id


def save_value_type(value, attribute_path):
	global value_types
	# get value id from value that is from an attribute
	val_type = "%s" % type(value)
	if val_type in value_types["attribute"]:
		value_types["attribute"][val_type][0]+= 1
		if len(value_types["attribute"][val_type]) < 6:
			value_types["attribute"][val_type].append(attribute_path)
	else:
		value_types["attribute"][val_type]= [1, attribute_path]	

def show_value_types():
	global value_types
	print ("types of values found:")
	for utype in sorted(value_types["attribute"].keys()):
		print("%s\t%i\t%s" % (utype, value_types["attribute"][utype][0],
			value_types["attribute"][utype][1:]))


def get_value_id(node):
	global con, cur, file_id
	return None   # dummy value_id, for testing
	nval = 0		# default values for number and string index
	str_id = 0
	if isinstance(node,h5py.Dataset):
		# if "file_create_date" in node.name:
		#	import pdb; pdb.set_trace()
		# if "general/specifications" in node.name:
		# 	import pdb; pdb.set_trace();
		size = node.size
		if np.issubdtype(node.dtype, np.number):
			vtype = "numeric"
		elif np.issubdtype(node.dtype, np.character):
			vtype = "string"
		else:
			try:
				vlenType = h5py.check_dtype(vlen=node.dtype)
			except:
				vlenType = None
			if vlenType in (bytes, str):
				if node.shape == ():
					# simple string in object.  Get value by node[()]
					vtype = "string"
				else:
					# sting in array in object.  Get value by node[0]
					vtype = "vstring"
				# try:
				# 	node0 = node[0]
				# except:
				# 	print ("unable to get first element from vstring")
				# 	import pdb; pdb.set_trace()
			elif size > 0 and isinstance(node[0], h5py.Reference):
				# found array of object references
				vtype = "reference"
			elif size > 0 and isinstance(node[0], np.void):
				vtype = "reference"  # example: node[0] = (2, 2, <HDF5 object reference>)
			else:
				print ("unable to determine type of dataset value")
				import pdb; pdb.set_trace()
		if vtype == "numeric":
			if size == 1:
				type_code = "n"	# n - single number
				nval = float(node[()])
				if math.isnan(nval):
					nval="nan"
			else:
				type_code = "N"	# N - array
		elif vtype == "string" or vtype == "vstring":
			if size <= 1:
				sval = node[()] if vtype == "string" else node[0]
				if isinstance(sval, bytes):
					sval = sval.decode("utf-8")  # store as string, not bytes
				if len(sval) < 10000:
					type_code = "s"	# s - single string
					str_id = get_string_id(sval)
				else:
					type_code = "W"	# flag single string too long
			elif size < 20:
				vlist = node.value.tolist()
				if isinstance(vlist[0], bytes):
					sval = b"'" + b"'".join(vlist) + b"'"	# join bytes
					sval = sval.decode("utf-8")
					if len(sval) < 10000:
						type_code = "S"	# S - array
						str_id = get_string_id(sval)
					else:
						type_code = "U" # flag array string too long
				elif isinstance(vlist[0], str):
					sval = "'" + "'".join(vlist) + "'"	# join characters
					if len(sval) < 10000:
						type_code = "S"	# S - array
						str_id = get_string_id(sval)
					else:
						type_code = "U" # flag array string too long
				else:
					type_code = "V"	# unknown type in vlist
					count_unknown_type(str(type(vlist[0])) + "-" + type_code)
			else:
				type_code = "T"	# T - Too big string array
		elif vtype == "reference":
			type_code = "R"  # R - array of object references
		else:
			import pdb; pdb.set_trace()
			sys.exit("%s, unknown value type: %s" % (node.name, node.dtype))
	elif isinstance(node, (np.ndarray, np.generic)):
		size = node.size
		is_numeric = np.issubdtype(node.dtype, np.number)
		is_string = np.issubdtype(node.dtype, np.character) or isinstance(node, object)
		if is_numeric:
			if size == 1:
				type_code = "n"	# n - single number
				nval = float(node)
				if math.isnan(nval):
					nval="nan"
			else:
				type_code = "N"	# N - array
		elif is_string:
			if size <= 1:
				type_code = "s"	# s - single string
				sval = node
				if isinstance(sval, bytes):
					sval = sval.decode("utf-8")
				str_id = get_string_id(sval)
			elif size < 20:
				type_code = "S"	# S - array
				vlist = node.tolist()
				if len(vlist) == 0:
					print("found zero length list")
					import pdb; pdb.set_trace()
				if isinstance(vlist[0], bytes):
					sval = b"'" + b"'".join(vlist) + b"'"	# join bytes
					sval = sval.decode("utf-8")
				else:
					sval = "'" + "'".join(vlist) + "'"	# join characters
				str_id = get_string_id(sval)
			else:
				type_code = "T"	# Too big string array
	else:
		# node is not dataset or numpy type, must be regular python type
		if isinstance(node, (bytes, str)):
			type_code = "s"	# s - single string
			sval = node
			if isinstance(sval, bytes):
				sval = sval.decode("utf-8")
			str_id = get_string_id(sval)
		elif isinstance(node, (list, tuple)):
			if len(node) > 0:
				if isinstance(node[0], (bytes, str)):
					if len(node) < 20:
						type_code = "S"	# S - array
						if isinstance(vlist[0], bytes):
							sval = b"'" + b"'".join(vlist) + b"'"	# join bytes
							sval = sval.decode("utf-8")
						else:
							sval = "'" + "'".join(vlist) + "'"	# join characters
						str_id = get_string_id(sval)
					else:
						type_code = "T"	# too big string array
				else:
					if isinstance(node[0], (int, float)):
						type_code = "N"	# numeric array, don't save
					else:
						type_code = "U"	# unkown contents of array
						count_unknown_type(str(type(node[0])) + "-" + type_code)
						# print("Unknown type (%s) in array, saving %s", (type(node), node))
						# import pdb; pdb.set_trace()
		elif isinstance(node, (int, float)):
			nval = float(node)
			if math.isnan(nval):
				nval="nan"
			type_code = "n"
		else:
			type_code = "u"	# unknown single value
			count_unknown_type(str(type(node)) + "-" + type_code)
			# print("Unknown node type (%s) when saving value of: %s" % (type(node), node))
			# import pdb; pdb.set_trace()
	cur.execute("select id from value where type=? and nval=? and str_id=?", (type_code, nval, str_id))
	row = cur.fetchone()
	if row is None:
		try:
			cur.execute("insert into value (type, nval, str_id) values (?, ?, ?)", (type_code, nval, str_id))
			con.commit()
		except:
			import pdb; pdb.set_trace()
		value_id = cur.lastrowid
	else:
		value_id = row[0]
	return value_id

def get_string_id(sval):
	global con, cur
	cur.execute("select id from string where value=?", (sval,))
	row = cur.fetchone()
	if row is None:
		cur.execute("insert into string (value) values (?)", (sval,))
# 		con.commit()
		string_id = cur.lastrowid
	else:
		# file name was already in file
		string_id = row[0]
	return string_id

def visit_nodes(fp):
	# visit all nodes (groups and datasets) in file
	# fp is the h5py File object
	# to_visit is a list of all nodes that need to visit
	# each element is a tuple (node, parent_id).  Start with root 
	to_visit = [ (fp, None) ]
	while to_visit:
		node, parent_id = to_visit.pop(0)
		node_id = get_node_id(node, parent_id)
		if isinstance(node,h5py.Group):
			for child in node:
				try:
					cn = node[child]
				except:
					# unable to access this node.  Perhaps a broken external link.  Ignore
					continue
				to_visit.append( (cn, node_id))
				# to_visit.append( (node[child], node_id))

def scan_file(path):
	global file_id, con, fp
	con.execute("begin")  # begin transaction
	file_id = find_file_id(path)
	if file_id is not None:
		print("Skipping (already indexed): %i. %s" % (file_id, path))
		con.commit()
		return
	print ("Scanning %s" % path)
	clear_unknown_types()
	fp = h5py.File(path, "r")
	if not fp:
		sys.exit("Unable to open %s" % path)
	print("opened %s" % path)
	file_id = get_file_id(path)
	visit_nodes(fp)
	# save_node("", fp)  # save root node
	# fp.visititems(save_node)
	con.commit()
	fp.close()
	show_unknown_types()
	show_value_types()

def scan_directory(dir):
	for root, dirs, files in os.walk(dir):
		for file in files:
			if file.endswith("nwb"):
				scan_file(os.path.join(root, file))

def main():
	global con, value_mirror
	if len(sys.argv) < 2:
		sys.exit('Usage: %s <directory_name>' % sys.argv[0])
	if not os.path.isdir(sys.argv[1]):
		sys.exit('ERROR: directory %s was not found!' % sys.argv[1])
	dir = sys.argv[1]
	open_database()
	initialize_caches()
	print ("scanning directory %s" % dir)
	scan_directory(dir)
	con.close()


if __name__ == "__main__":
    main()
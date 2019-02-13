import sys
import os
import h5py
import sqlite3
import numpy as np
import math

dbname="nwb_index.db"
con = None     # database connection
file_id = None # id of current file (row inf h5file table)
cur = None       # cursor


# sqlite3 database schema
schema='''
create table path (				-- All paths / names
	id integer primary key,
	name text not null
);

create table file (				-- hdf5 files
	id integer primary key,
	path_id integer not null
);

create table node (  -- stores groups, dataseta AND attributes
	id integer primary key,
	file_id integer not null,
	parent_id integer not null, -- parent group (if group or dataset) or parent group or dataset (if attribute)
	path_id integer not null,	-- path to this node (group, dataset or attribute)
	node_type char(1) not null,	-- either: g-group, d-dataset, a-attribute
	value_id integer not null	-- value associated with dataset or attribute
);

create table value (			-- value of dataset or attribute
	id integer primary key,
	type char(1) not null,  -- either: n-number, s-string, N-number array, S-string array
	nval real not null,     -- contains value of number, if number
	str_id integer not null -- index to string id if string, or string array; otherwise 0
);

create table string (
	id integer primary key,
	value text
);
''';

def open_database():
	global dbname, schema
	global con, cur
	if not os.path.isfile(dbname):
		print("Creating database '%s'" % dbname)
		con = sqlite3.connect(dbname)
		cur = con.cursor()
		cur.executescript(schema);
	else:
		print("Opening existing database: %s" % dbname)
		con = sqlite3.connect(dbname)
		cur = con.cursor()

def get_path_id(name):
	global con, cur
	cur.execute("select id from path where name=?", (name,))
	row = cur.fetchone()
	if row is None:
		cur.execute("insert into path (name) values (?)", (name,))
		con.commit()
		path_id = cur.lastrowid
	else:
		# name was already stored
		path_id = row[0]
	return path_id

def find_file_id(name):
	# return file_id if have file in database, otherwise None
	global con, cur
	path_id = get_path_id(name)
	cur.execute("select id from file where path_id = ?", (path_id,))
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
		path_id = get_path_id(name)
		cur.execute("insert into file (path_id) values (?)", (path_id,))
		con.commit()
		file_id = cur.lastrowid
	print("file_id is %i" % file_id)
	return file_id

def get_parent_id(name):
	global con, cur, file_id
	if name == "":
		parent_id = 0  # root has no parent
	else:
		parent_name, name2 = os.path.split(name)
		path_id = get_path_id(parent_name)
		cur.execute("select id from node where file_id = ? and path_id = ?", (file_id, path_id,))
		row = cur.fetchone()
		if row is not None:
			parent_id = row[0]
		else:
			sys.exit("Unable to find parent for: '%s'" % name)
	return parent_id

def save_group(name, node):
	global con, cur, file_id
	# full_name = node.name
	parent_id = get_parent_id(name)
	path_id = get_path_id(name)
	node_type = "g"		# indicates group
	value_id = 0
	cur.execute("insert into node (file_id, parent_id, path_id, node_type, value_id) values (?, ?, ?, ?, ?)", 
			(file_id, parent_id, path_id, node_type, value_id))
	con.commit()
	group_id = cur.lastrowid
	# save attributes
	for key in node.attrs:
		value = node.attrs[key]
		full_path = name + "/" + key
		save_attribute(group_id, full_path, value)
	return group_id

def save_dataset(name, node):
	global con, cur, file_id
	# full_name = node.name
	parent_id = get_parent_id(name)  # id of parent group
	# parent_name, ds_name = os.path.split(name)
	path_id = get_path_id(name)
	value_id = get_value_id(node)
	node_type = "d"  # dataset
	cur.execute("insert into node (file_id, parent_id, path_id, node_type, value_id) values (?, ?, ?, ?, ?)", 
			(file_id, parent_id, path_id, node_type, value_id))
	con.commit()
	dataset_id = cur.lastrowid
	# save attributes
	for key in node.attrs:
		value = node.attrs[key]
		full_path = name + "/" + key
		save_attribute(dataset_id, full_path, value)
	return dataset_id

def save_attribute(parent_id, attribute_path, value):
	global con, cur, file_id
	path_id = get_path_id(attribute_path)
	value_id = get_value_id(value)
	node_type = "a"		# indicates attribute
	cur.execute("insert into node (file_id, parent_id, path_id, node_type, value_id) values (?, ?, ?, ?, ?)",
		(file_id, parent_id, path_id, node_type, value_id))
	con.commit()

count = 0;
def save_node(name, node):
	global count
	if isinstance(node,h5py.Group):
		save_group(name, node)
	elif isinstance(node,h5py.Dataset):
		save_dataset(name, node)
	else:
		sys.exit("Unknown node type in save_node: %s" % node)
	count += 1
	# if count > 10:
	# 	count = 0
	# 	return 1
	return None

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


def get_value_id(node):
	global con, cur, file_id
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
		con.commit()
		string_id = cur.lastrowid
	else:
		# file name was already in file
		string_id = row[0]
	return string_id

def scan_file(path):
	global file_id
	file_id = find_file_id(path)
	if file_id is not None:
		print("Skipping (already indexed): %i. %s" % (file_id, path))
		return
	print ("Scanning %s" % path)
	clear_unknown_types()
	fp = h5py.File(path, "r")
	if not fp:
		sys.exit("Unable to open %s" % path)
	print("opened %s" % path)
	file_id = get_file_id(path)
	save_node("", fp)  # save root node
	fp.visititems(save_node)
	fp.close()
	show_unknown_types()

def scan_directory(dir):
	for root, dirs, files in os.walk(dir):
		for file in files:
			if file.endswith("nwb"):
				scan_file(os.path.join(root, file))
def main():
	global con
	if len(sys.argv) < 2:
		sys.exit('Usage: %s <directory_name>' % sys.argv[0])
	if not os.path.isdir(sys.argv[1]):
		sys.exit('ERROR: directory %s was not found!' % sys.argv[1])
	dir = sys.argv[1]
	open_database()
	print ("scanning directory %s" % dir)
	scan_directory(dir)
	con.close()


if __name__ == "__main__":
    main()
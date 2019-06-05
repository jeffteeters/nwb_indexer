import sys
import os
import h5py
import sqlite3
import pprint as pp
import pprint

pp = pprint.PrettyPrinter(indent=4)

dbname="cf.db"
con = None     # database connection
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
	type char(1) not null,     -- either: n-number, s-string, N-number array, S-string array
	nval real not null,        -- contains value of number, if number.  Otherwise, 0
	idx integer not null       -- index to string table which holds all string and array values
	-- start_idx integer not null, -- index of starting element (all types)
	-- end_idx integer not null   -- index of one past ending element if type N or S.  Otherwise 0
);

create table number (
	id integer primary key,
	value text
);

create table string (
	id integer primary key,
	value text
);
''';

# add custom specification for for svoboda data 
cf_schema='''
insert into path (id, name) values
   (1, "nwb1_example.nwb"),
   (2, "nwb2_example.nwb"),
   (3, ""),
   (4, "epochs"),
   (5, "epochs/start_time"),
   (6, "intervals"),
   (7, "intervals/colnames"),
   (8, "intervals/start_time"),
   (9, "intervals/id")
;

insert into file (id, path_id) values
   (1, 1),
   (2, 2)
;

insert into node (id, file_id, parent_id, path_id, node_type, value_id) values
   (1, 1, 0, 3, "g", 0),  -- ""  (root node)
   (2, 1, 1, 4, "g", 0),  -- "epochs"
   (3, 1, 2, 5, "d", 1),  -- "start_time"
   (4, 2, 0, 3, "g", 0),  -- ""  (root node of nwb2_example.nwb)
   (5, 2, 4, 6, "g", 0),  -- "intervals"
   (6, 2, 5, 7, "a", 2),  -- "intervals/colnames"
   (7, 2, 5, 8, "d", 3),  -- "intervals/start_time"
   (8, 2, 5, 9, "d", 4)   -- "intervals/id"
;

insert into value (id, type, nval, idx) values
   (1, 'n', 150, 0),   -- value 150 for start_time
   (2, 's', 0, 1),     -- interval/colnames value is "start_time"
   (3, 'N', 0, 2),     -- intervals/start_time value is "100,150,200"
   (4, 'N', 0, 3)      -- intervals/id, value is "1,2,3"
;

insert into string (id, value) values
   (1, "start_timeC"),
   (2, "100,150,200"),
   (3, "1,2,3")
;

-- insert into number (id, value) values
--    (1, 100),
--    (2, 150),
--    (3, 200)
;
''';

def show_align(v1, v2):
    print("show_align, v1=%s, v2=%s" % (v1, v2))
    return 0


def show_vals(*args):
    for val in args:
        print(val)

def add_function():
	global con
	con.create_function("cust", 2, show_vals)

query ='''
select
    cust(s_st.value, s_id.value)
from
    string s_st,
    string s_id
where
    s_st.id = 2 and
    s_id.id = 3
;
'''

query ='''
select
    p_f1.name,  -- file 1 path
    p1_e.name,
    p_st1.name, -- start_time 1 path
    -- n1_st.parent_id, n1_e.parent_id,
    v_st1.nval  -- start_time 1 value (150)
from
    path p_f1,
    path p_st1,
    path p1_e,   -- path for epochs group
    path p2_colnames,
    -- value v2_colnames,
    -- string s2_colnames,
    node n2_colnames,
    value v_st1,
    file f1,
    node n1_e,  -- epochs group
    node n1_st,  -- start_time 1 dataset
    string s2_st
where
	p_f1.id = f1.path_id and
	f1.id = n1_e.file_id and
	n1_e.path_id = p1_e.id and
	n1_st.parent_id = n1_e.id and
	v_st1.id = n1_st.value_id and
	p_st1.id = n1_st.path_id and
	p_st1.name LIKE "%start_time" and
	case
	    when
	      n2_colnames.parent_id = n1_e.id and
	      n2_colnames.path_id = p2_colnames.id and
	      n2_colnames.node_type = "a" and
	      p2_colnames.name LIKE "%/colnames" and
	      v_st1.type = "N" and
		  v_st1.idx =  s2_st.id
	   then
	      cust(s2_st.value, "test constant")
	   else
	      v_st1.type = "n" and
	      s2_st.id = 1 and -- constrain to one row even though not used
	      n2_colnames.id = 1 and -- constrain to one row even though not used
	      p2_colnames.id = 1 -- constrain to one row even though not used
	end

--
--    cust(s_st.value, s_id.value)
--	n2_colnames.value_id = v2_colnames.id and
--	v2_colnames.idx= s2_colnames.id and
--	s2_colnames.value = "start_timeC"
'''

def run_query():
	global cur, query
	cur.execute(query)
	# print (cur.fetchone()[0])
	pp.pprint (cur.fetchall())

def open_database():
	global dbname, schema, cf_schema
	global con, cur
	if os.path.isfile(dbname):
		print("removing previous database %s" % dbname)
		os.remove(dbname)
	print("Creating database '%s'" % dbname)
	con = sqlite3.connect(dbname)
	cur = con.cursor()
	cur.executescript(schema);
	cur.executescript(cf_schema);
	# else:
	# 	print("Opening existing database: %s" % dbname)
	# 	con = sqlite3.connect(dbname)
	# 	cur = con.cursor()

def main():
	global con
	open_database();
	add_function()
	run_query()
	con.close()

if __name__ == "__main__":
    main()
    print("all done")



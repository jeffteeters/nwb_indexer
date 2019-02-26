import sys
import os
import h5py
import sqlite3
import readline
import re

dbname="paired_ds.db"
con = None     # database connection
cur = None       # cursor


# sqlite3 database schema
schema='''

create table grp (
	id integer primary key,
	path text not null
);

create table dataset (
	id integer primary key,
	parent_id integer not null,
	name text not null,
	value_id integer not null
);

create table value (			-- value of dataset or attribute
	id integer primary key,
	type char(1) not null,  -- either: n-number, s-string, N-number array, S-string array
	start_index integer not null,     -- starting index of array value
	end_index integer not null		-- ending index of array value
);

create table number (	-- numeric array values
	id integer primary key,
	entry float not null  -- value of element of array
);

create table string (	-- string array values
	id integer primary key,
	entry text not null  -- value of element of array
);

insert into grp (id, path) values (1, '/intervals/epochs');

insert into dataset (id, parent_id, name, value_id) values (1, 1, "trial_id", 1);
insert into dataset (id, parent_id, name, value_id) values (2, 1, "start_time", 2);
insert into dataset (id, parent_id, name, value_id) values (3, 1, "stop_time", 3);

insert into value (id, type, start_index, end_index) values (1, 'S', 1, 5);	-- trial_id
insert into string (entry) values ('trial_1'), ('trial_2'), ('trial_3'), ('trial_4');

insert into value (id, type, start_index, end_index) values (2, 'N', 1, 5);  -- start_time
insert into number (entry) values (1.1), (2.1), (3.1), (4.1);

insert into value (id, type, start_index, end_index) values (3, 'N', 5, 9);  -- stop_time
insert into number (entry) values (1.8), (2.8), (3.8), (4.8);

-- tag_index dataset
insert into dataset (id, parent_id, name, value_id) values (4, 1, "tag_index", 4);
insert into value (id, type, start_index, end_index) values (4, 'N', 9, 13);
insert into number (entry) values (3), (3), (4), (6);  -- index to element beyond tag

-- tags dataset
insert into dataset (id, parent_id, name, value_id) values (5, 1, "tags", 5);
insert into value (id, type, start_index, end_index) values (5, 'S', 5, 11);
insert into string (entry) values
	('good'), ('left'), ('strong'), -- trial_1 tags
	('bad'),						-- trial_3 tag; are no trial_2 tags
	('left'), ('bad');				-- trial_4 tags
''';

def open_database():
	global dbname, schema
	global con, cur
	if os.path.isfile(dbname):  # for testing always remove
		print ("Removing existing %s" % dbname)
		os.remove(dbname);
	if not os.path.isfile(dbname):
		print("Creating database '%s'" % dbname)
		con = sqlite3.connect(dbname)
		cur = con.cursor()
		cur.executescript(schema);
	else:
		print("Opening existing database: %s" % dbname)
		con = sqlite3.connect(dbname)
		cur = con.cursor()

def run_tag_query(tag):
	print("running tag query, '%s'" % tag)
	query = '''
select
	g.path,
	ds1.name,  -- trial_id
	s1.entry,  -- trial_1
	ds2.name,  -- start_time
	n2.entry,  -- 2.2
	ds3.name,  -- stop_time
	n3.entry,  -- 2.8
	ds4.name,  -- tag_index
	CASE WHEN s1.id - v1.start_index = 0
		THEN v6.start_index
		ELSE n4.entry + v6.start_index
	END AS ti_min,
	-- n4.entry as 'ti_min',	-- tag index minimum
	n5.entry + v6.start_index as 'ti_max'	-- tag index maximum
from
	grp g,
	dataset ds1,	-- trial_id
	value v1,
	string s1,
	dataset ds2,	-- start_time
	value v2,
	number n2,
	dataset ds3,	-- stop_time
	value v3,
	number n3,
	dataset ds4,	-- tag_index
	value v4,
	number n4,	-- ti_min
	number n5,		-- ti_max
	dataset ds6,	-- tags
	value v6,
	string s6
where
	ds1.parent_id = g.id and
	ds2.parent_id = g.id and
	ds3.parent_id = g.id and
	ds4.parent_id = g.id and
	ds6.parent_id = g.id and
	ds1.value_id = v1.id and
	ds2.value_id = v2.id and
	ds3.value_id = v3.id and
	ds4.value_id = v4.id and
	ds6.value_id = v6.id and	
	ds1.name = 'trial_id' and
	ds2.name = 'start_time' and
	ds3.name = 'stop_time' and
	ds4.name = "tag_index" and
	ds6.name = "tags" and
	v1.type == 'S' and
	v2.type == 'N' and
	v3.type == 'N' and
	v4.type == 'N' and
	v6.type == 'S' and
	s1.id - v1.start_index = n2.id - v2.start_index and
	s1.id - v1.start_index = n3.id - v3.start_index and
	s1.id - v1.start_index - 1 = n4.id - v4.start_index and
	s1.id - v1.start_index = n5.id - v4.start_index and
	CASE WHEN s1.id - v1.start_index = 0
		THEN v6.start_index
		ELSE n4.entry + v6.start_index
	END <= s6.id and
	s6.id < (n5.entry + v6.start_index) and
	s6.entry == ?
'''
	result = cur.execute(query, (tag,));
	show_results(result);


def run_start_stop_query(start_time, stop_time):
	print ("running interval query, start_time=%f, stop_time=%f" % (start_time, stop_time))
	query = '''
select
	g.path,
	ds1.name,
	s1.entry,
	ds2.name,
	n2.entry,
	ds3.name,
	n3.entry
from
	grp g,
	dataset ds1,
	value v1,
	string s1,
	dataset ds2,
	value v2,
	number n2,
	dataset ds3,
	value v3,
	number n3
where
	ds1.parent_id = g.id and
	ds2.parent_id = g.id and
	ds3.parent_id = g.id and
	ds1.value_id = v1.id and
	ds2.value_id = v2.id and
	ds3.value_id = v3.id and
	ds1.name = 'trial_id' and
	ds2.name = 'start_time' and
	ds3.name = 'stop_time' and
	v1.type == 'S' and
	v1.start_index <= s1.id and
	v1.end_index > s1.id and
	v2.start_index <= n2.id and
	v2.end_index > n2.id and
	v3.start_index <= n3.id and
	v3.end_index > n3.id and
	s1.id - v1.start_index = n2.id - v2.start_index and
	s1.id - v1.start_index = n3.id - v3.start_index and
	n2.entry >= ? and
	n3.entry <= ?
''';
	result = cur.execute(query, (start_time, stop_time));
	show_results(result);


def show_results(result):
	rows=result.fetchall()
	num_rows = len(rows)
	print("Found %i:" % num_rows)
	n = 0
	for row in rows:
		n += 1
		print("%i. %s" % (n, row))


def get_and_run_queries():
	print("Enter start_time, stop_time or tag; control-d to quit")
	print("Tags-trials are: 'good'-1; 'left'-1&4, 'strong'-1, 'bad'-3&4]")
	while True:
		try:
			line=input("> ")
		except EOFError:
			break;
		if re.match("^[a-z]+$", line):
			# assume tag
			run_tag_query(line);
		else:
			start_time, stop_time = [float(x) for x in line.split()]
			run_start_stop_query(start_time, stop_time);
	print("\nDone processing all queries")


def main():
	global con
	open_database()
	get_and_run_queries()
	con.close()


if __name__ == "__main__":
    main()

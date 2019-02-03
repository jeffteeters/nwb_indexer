import sys
import os
import sqlite3
import re
import parse


default_dbname="nwb_index.db"
dbname=default_dbname
con = None     # database connection
cur = None       # cursor


def open_database():
	global dbname, con, cur
	# this for development so don't have to manually delete database between every run
	print("Opening '%s'" % dbname)
	con = sqlite3.connect(dbname)
	cur = con.cursor()

def show_available_files():
	global con, cur
	result=cur.execute("select p.name from path p, file f where f.path_id = p.id order by p.name")
	rows=result.fetchall()
	num_rows = len(rows)
	print("Searching %i files:" % num_rows)
	n = 0
	for row in rows:
		n += 1
		print("%i. %s" % (n, row))

def run_query(sql):
	global con, cur
	result=cur.execute(sql)
	rows=result.fetchall()
	num_rows = len(rows)
	print("Found %i:" % num_rows)
	n = 0
	for row in rows:
		n += 1
		print("%i. %s" % (n, row))

def get_and_run_queries():
	print("Enter query, control-d to quit")
	while True:
		try:
			query=input("> ")
		except EOFError:
			break;
		# pq = parse_query(query)
		# if pq:
		# 	run_query(pq)
		ti = parse.parse(query)
		sql = parse.make_sql(ti)
		print ("sql=\n%s" % sql)
		run_query(sql)
	print("\nDone processing all queries")


def main():
	global con, dbname
	if len(sys.argv) > 2:
		sys.exit('Usage: %s [ <db.sqlite3> ]' % sys.argv[0])
	if len(sys.argv) == 1:
		print("Database not specified; using '%s'" % dbname)
	else:
		dbname=sys.argv[1]
	if not os.path.isfile(dbname):
		sys.exit("ERROR: database '%s' was not found!" % dbname)
	open_database()
	show_available_files()
	get_and_run_queries()
	# print ("scanning directory %s" % dir)
	# scan_directory(dir)
	con.close()

if __name__ == "__main__":
    main()
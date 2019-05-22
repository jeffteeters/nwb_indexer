import sys
import os
import h5py
import sqlite3
import pprint as pp
import pprint
# from timeit import Timer
import time


pp = pprint.PrettyPrinter(indent=4)

dbname="family.db"
con = None     # database connection
cur = None       # cursor

# sqlite3 database schema


schema='''
create table file (       -- hdf5 files
  id integer primary key,
  prenom_id integer not null references prenom  -- prenom contains full path to file 
);

create table prenom (   -- all names (file names and path parts; 'prenom' is french for given name)
  id integer primary key, -- (The main reason this table is not named "name" is there is another table
  name text not null    -- "node" which starts with "n".  For aliases it's nice to have table name
              -- start with different letters).
);

create table path (  -- paths listed explicitly
  id integer primary key,
  name text not null  -- full path, without leading '/'
);

create table node (  -- stores groups, dataseta AND attributes
  id integer primary key,
  file_id integer references file,
  parent_id integer references node, -- parent group (if group or dataset) or parent group or dataset (if attribute)
  prenom_id integer not null references prenom, -- name of this node (last component of full path)
  path_id integer not null references path  -- full path to this node, without leading '/'
);

''';


class Vmap:
  # maps value to id
  # used for prenom and string table
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
      key = self.map[value][0]  # key is the id
    else:
      key = len(self.map) + 1
      self.map[value] = (key, 'new')  # save indicator if record is new
    return key

  def load_map(self):
    # load values from table.  Needed if updating database
    global con, cur
    assert len(self.map) == 0, "load_map for table '%s' called, but map not empty" % self.table_name
    result = cur.execute("select id, %s from %s order by %s" % (self.value_name, self.table_name, self.value_name))
    for row in result:
      key, value = row
      self.map[value] = (key, 'old')  # save indicator that record is already in database

  def save_map(self):
    # saves map in the database
    global con, cur
    # execute insert statements
    print("saving %s, %i rows" % (self.table_name, len(self.map) ))
    for key, vt in sorted(self.map.items(), key = lambda kv:(kv[0], kv[1])):
      # print("%i, %s" % (vt[0], key))
      if vt[1] == 'new':  # only save new records
        cur.execute("insert into %s (id, %s) values (?, ?)" % (self.table_name, self.value_name), (vt[0], key))


def fill_db():
  global con, cur
  # fill database with fake nodes for testing
  # for getting node names
  prenom_map = Vmap('prenom', 'name')
  path_map = Vmap('path', 'name')
  # a queue of nodes to add, each element is tuple with (file_id, parent_id, name, depth)
  # depth is 0 for root
  # add in root node
  num_files = 100
  to_add = []
  for file_id in range(1, num_files + 1):
    file_name = "file%02i" % file_id
    prenom_id = prenom_map.get_id(file_name)
    cur.execute("insert into file (id, prenom_id) values (?, ?)", (file_id, prenom_id))
    to_add.append( (file_id, None, '', 0, '') )  # last one is path, gives full path
  while to_add:
    file_id, parent_id, name, depth, path = to_add.pop(0)
    prenom_id = prenom_map.get_id(name)
    path_id = path_map.get_id(path)
    cur.execute("insert into node (file_id, parent_id, prenom_id, path_id) values (?, ?, ?, ?)", (
      file_id, parent_id, prenom_id, path_id))
    # con.commit()
    node_id = cur.lastrowid
    if depth < 4:
      # add children of this node to the queue
      for i in range(4):
        child_name = "d%ic%s" % (depth, i)
        child_path = child_name if path == "" else path + "/" + child_name
        to_add.append( (file_id, node_id, child_name, depth + 1, child_path) )
  # done adding all nodes, now save the names
  prenom_map.save_map()
  path_map.save_map()
  con.commit()


query = '''
WITH RECURSIVE
  tree(node_id, name,level) AS (
    VALUES(1, '/', 0)
    UNION ALL
    SELECT n.id, p.name, tree.level+1
      FROM node n, prenom p
      JOIN tree ON n.parent_id=tree.node_id
      where p.id = n.prenom_id
     ORDER BY 3 desc
  )
SELECT substr('..........',1,level*3) || name FROM tree;
''';

query = '''
WITH RECURSIVE
  tree(node_id, name,level, full_path) AS (
    VALUES(1, '/', 0, '')
    UNION ALL
    SELECT n.id, p.name, tree.level+1, tree.full_path || '/' || p.name
      FROM node n, prenom p
      JOIN tree ON n.parent_id=tree.node_id
      where p.id = n.prenom_id
     ORDER BY 3 desc
  )
-- SELECT substr('..........',1,level*3) || name FROM tree;
select full_path, node_id from tree
where full_path like "/d0c2/d1c1/d2c2"
''';

query = '''
WITH RECURSIVE
  tree(node_id, name, level, full_path) AS (
    VALUES(1, '/', 0, '')
    UNION ALL
    SELECT n.id, p.name, tree.level+1, tree.full_path || '/' || p.name
      FROM node n, prenom p
      JOIN tree ON n.parent_id=tree.node_id
      where p.id = n.prenom_id
     ORDER BY 3 desc
  )
-- SELECT substr('..........',1,level*3) || name FROM tree;
select full_path, node_id from tree
where full_path like "/d0c2/d1c1/d2c2"
''';

# find path from node to root
query = '''
    WITH RECURSIVE tree(node_id, parent_id, node_path) AS (
        SELECT n.id, n.parent_id, p.name
        FROM node n, prenom p
        WHERE n.id=24 and n.prenom_id = p.id
      UNION ALL
        SELECT n.id, n.parent_id, p.name || '/' || tree.node_path
        FROM node n, prenom p
        JOIN tree ON n.id = tree.parent_id
        WHERE n.prenom_id = p.id
    ) SELECT node_path FROM tree where parent_id is NULL
''';

# Following does not work.  No way to specify node to start query with
query = '''
    select tr.node_path, ban.id
    from
    node as ban,   -- parent node
    node as ba1n,  -- first child node
    prenom as ba1p, -- first child node prenom
    ( WITH RECURSIVE tree(node_id, parent_id, node_path) AS (
        SELECT n.id, n.parent_id, p.name
        FROM node n, prenom p
        WHERE n.id=ba1n.id and  -- was 24
        n.prenom_id = p.id
      UNION ALL
        SELECT n.id, n.parent_id, p.name || '/' || tree.node_path
        FROM node n, prenom p
        JOIN tree ON n.id = tree.parent_id
        WHERE n.prenom_id = p.id
    ) SELECT node_path FROM tree where parent_id is NULL
    ) as tr
    where
    -- ba1n.id = 24 and
    ba1n.parent_id = ban.id and
    ba1n.prenom_id = ba1p.id
    and ba1p.name = "d2c1"  -- look for parents with this as the child name
    and tr.node_path like "/d0c1/%"
''';



# find node_id  given path to root, naive method - get all of them, then filter by path 
query = '''
    SELECT fp.name, tr.node_path || '/' || ba1p.name, ban.id, ban.parent_id, ban.file_id
    from
    file as f,
    prenom as fp,
    node as ban,   -- parent node
    node as ba1n,  -- first child node
    prenom as ba1p, -- first child node prenom
    ( WITH RECURSIVE tree(file_id, node_id, node_path) AS (
    SELECT
        n.file_id, n.id, ''  -- select all root nodes
        from node n
        where n.parent_id is NULL
    UNION ALL
        SELECT n.file_id, n.id, tree.node_path || '/' || p.name
        FROM node n, prenom p
        JOIN tree on tree.node_id = n.parent_id
        WHERE n.prenom_id= p.id
    ) select file_id, node_id, node_path from tree) as tr
    where
      tr.file_id = f.id
      and f.prenom_id = fp.id
      and tr.node_path like '/d0c1/%' -- "/d0c1%"
      and tr.node_id = ban.id
      and ba1n.parent_id = ban.id
      and ba1n.prenom_id = ba1p.id
      and ba1p.name = "d2c1"  -- look for parents with this as the child name
''';


path_query = '''
    SELECT fp.name, ba1p.name, ban.id, ban.parent_id, ban.file_id
    from
    file as f,
    prenom as fp,
    node as ban,   -- parent node
    node as ba1n,  -- first child node
    -- prenom as ba1p, -- first child node prenom
    path as ba1p
/*
    ( WITH RECURSIVE tree(file_id, node_id, node_path) AS (
    SELECT
        n.file_id, n.id, ''  -- select all root nodes
        from node n
        where n.parent_id is NULL
    UNION ALL
        SELECT n.file_id, n.id, tree.node_path || '/' || p.name
        FROM node n, prenom p
        JOIN tree on tree.node_id = n.parent_id
        WHERE n.prenom_id= p.id
    ) select file_id, node_id, node_path from tree) as tr
*/
    where
      -- tr.file_id = f.id
      f.prenom_id = fp.id
      and ban.file_id = f.id
      and ba1p.name like "d0c1/%/d2c1"
      and ba1p.id = ba1n.path_id
      and ba1n.parent_id = ban.id
      -- and ba1n.prenom_id = ba1p.id
      -- and ba1p.name = "d2c1"  -- look for parents with this as the child name
''';

schema_family='''
# sqlite3 database schema


CREATE TABLE family(
  name TEXT PRIMARY KEY,
  mom TEXT REFERENCES family,
  dad TEXT REFERENCES family,
  born DATETIME,
  died DATETIME -- NULL if still alive
  -- other content
);
insert into family (name, mom, dad, born, died) values
  ('Jeff', 'kathryn', 'Joseph', '1959-06-27', Null),
  ('sue', 'Alice', 'thom', '1960-09-20', Null),
  ('Alice','Sue', 'Jeff', '1934-02-03', Null),
  ('Mary','Alice', 'mdad', '1922-02-03', Null)
  ;
-- The "family" table is similar to the earlier "org" table except that now there are two parents to each member. We want to know all living ancestors of Alice, from oldest to youngest. An ordinary common table expression, "parent_of", is defined first. That ordinary CTE is a view that can be used to find all parents of any individual. That ordinary CTE is then used in the "ancestor_of_alice" recursive CTE. The recursive CTE is then used in the final query:
'''

query_family = '''
WITH RECURSIVE
  parent_of(name, parent) AS
    (SELECT name, mom FROM family UNION SELECT name, dad FROM family),
  ancestor_of_alice(name) AS
    (SELECT parent FROM parent_of WHERE name='Alice'
     UNION ALL
     SELECT parent FROM parent_of JOIN ancestor_of_alice USING(name))
SELECT family.name FROM ancestor_of_alice, family
 WHERE ancestor_of_alice.name=family.name
   AND died IS NULL
 ORDER BY born;
 ''';


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
  else:
    print("Opening existing database: %s" % dbname)
    con = sqlite3.connect(dbname)
    cur = con.cursor()

def run_query():
  global query, path_query
  global con, cur
  q = path_query
  # q = query
  print("query is\n%s" % q)
  # results showed that using recursive query (with clause) is much slower when there are 100
  # files.  Times:
  # time required= 0.001362 - path query
  # time required= 0.210992 - recursive query
  # ratio 0.210992 / 0.001362 = x154
  # (path query is 150x faster)
  t0 = time.process_time()
  # qc = "result = cur.execute(query)"
  # t = Timer(qc, "from __main__ import cur, query, result")
  # timeRequired = t.timeit(number=1000)
  # result = cur.execute(path_query)
  result = cur.execute(q)
  t1 = time.process_time()
  timeRequired = t1 - t0
  rows=result.fetchall()
  num_rows = len(rows)
  print("Found %i ancestors:" % num_rows)
  # n = 0
  # for row in rows:
  #   n += 1
  #   print("%02i. %s" % (n, row))
  print("time required= %f" % timeRequired)


def main():
  global con
  open_database()
  fill_db()
  run_query()
  con.close()


if __name__ == "__main__":
    main()

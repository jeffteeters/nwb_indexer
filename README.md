# nwbindexer
Creates an sqlite index of metadata in a collection of NWB (HDF5) files files.  Also allows searching the
files using a query syntax similar to that used in the NWB Query Engine.
These tools were developed for searching within NWB files.

## Requirements:
Python 3.6
(Tested with anaconda Python 3.6; might work with other versions too).

## Usage:

### 1) Build the index.

First, build the index by running:

`python build_index.py <directory>`

where:
`<directory>` is a directory containing nwb files (extension ".nwb).

This should scan all the nwb files in the directory and save the
information about the small datasets and attributes in an SQLite3 database.
Name of the database file will be "nwb_index.db".


### 2) Running queries.

Queries can be run by running:

`python run_query.py  [ <index_file> ]`

Where the optional `<index_file>` is the name of a SQLite3 databaes created in
step 1.  (Default is "nwb_index.db").


Queries are entered using the format described in the NWB Query Engine paper, except that:
* ":" is used instead of "=", and the parentheses are not required.  (This specifies the "parent location").
* The parent location and ":" can be left off, which is the same as parent location == "*" (search entire tree).
* String constants must always be enclosed in either single or doulble quotes.
* Any string constant used with LIKE must have wildcards ("%" or "_") explicitly included (if no wildcards are included, the query does an exact match).
* The expression on the right must always have a relational operator.  Just giving the child location (e.g. `epochs:(start_time)`) is currently not allowed.

* Currently the queries only work for dataset values, not for any attributes (of groups or datasets).
The database schema (given in file "build_index.py" might need to be changed to have queries search 
both groups and datasets.  Or there might need to be a way to specify explicitly whether the
child value being searched for is a group attribute, dataset attribute or dataset value.

#### Example queries:
(Using same datasets at the NWB Query Engine test site: http://eeg.kiv.zcu.cz:8080/nwb-query-engine-web/)

`/:session_start_time LIKE "%Jun __ 2013%"`

Output:
```Found 6:
1. ('../sample_data/data_structure_ANM210862_20130627.nwb', '', 'session_start_time', 'Thu Jun 27 2013 10:36:32')
2. ('../sample_data/data_structure_ANM210862_20130626.nwb', '', 'session_start_time', 'Wed Jun 26 2013 10:44:32')
3. ('../sample_data/data_structure_ANM210863_20130626.nwb', '', 'session_start_time', 'Wed Jun 26 2013 12:23:37')
4. ('../sample_data/data_structure_ANM210863_20130627.nwb', '', 'session_start_time', 'Thu Jun 27 2013 12:15:14')
5. ('../sample_data/data_structure_ANM210863_20130628.nwb', '', 'session_start_time', 'Fri Jun 28 2013 16:24:15')
6. ('../sample_data/data_structure_ANM210862_20130628.nwb', '', 'session_start_time', 'Fri Jun 28 2013 14:58:30')
```

`epochs:(start_time>200 & stop_time<210)`

Output:
```Found 2:
1. ('../sample_data/data_structure_ANM214429_20130807.nwb', 'epochs/trial_015', 'start_time', 200.719654, 'stop_time', 208.157124)
2. ('../sample_data/data_structure_ANM214429_20130806.nwb', 'epochs/trial_268', 'start_time', 3317.152814, 'stop_time', 2.683177)```

`/:file_create_date LIKE "%"`

Output:
```Found 16:
1. ('../sample_data/data_structure_ANM210861_20130701.nwb', '', 'file_create_date', '2017-04-24T11:32:54.281831')
2. ('../sample_data/data_structure_ANM210861_20130702.nwb', '', 'file_create_date', '2017-04-24T11:32:54.225763')
...
16. ('../sample_data/data_structure_ANM214429_20130805.nwb', '', 'file_create_date', '2017-04-24T11:32:55.174861')
```

`/general/subject/: (age LIKE "%3 months 16 days%" & species LIKE "%Mus musculu%") & /:file_create_date LIKE "%2017-04%" & /epochs : start_time < 150`

Output:
```
Found 2:
1. ('../sample_data/data_structure_ANM210862_20130627.nwb', 'general/subject', 'age', '3 months 16 days  weeks', 'species', 'Mus musculus', '', 'file_create_date', '2017-04-24T11:32:54.215883', 'epochs/trial_001', 'start_time', 2.284463)
2. ('../sample_data/data_structure_ANM210863_20130627.nwb', 'general/subject', 'age', '3 months 16 days  weeks', 'species', 'Mus musculus', '', 'file_create_date', '2017-04-24T11:32:54.076284', 'epochs/trial_001', 'start_time', 2.222392)
```

`/general/subject/: (age LIKE "3 months 16 days%" & species LIKE "Mus musculus") & /:session_start_time < "Thu Jun 27 2013 12" & /epochs : start_time < 250`

Output:
```Found 1:
1. ('../sample_data/data_structure_ANM210862_20130627.nwb', 'general/subject', 'age', '3 months 16 days  weeks', 'species', 'Mus musculus', '', 'session_start_time', 'Thu Jun 27 2013 10:36:32', 'epochs/trial_001', 'start_time', 2.284463)
```








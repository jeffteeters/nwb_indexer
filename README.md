# nwbindexer
Create an sqlite index of metadata in a collection of NWB (HDF5) files files.  Developed for searching within NWB files.

Requirements:
Python 3.6
(Tested with anaconda Python 3.6; might work with other versions too).

Usage:

1) Build the index.

First, build the index by running:

python build_index.py <directory>

where:
<directory> is a directory containing nwb files (extension ".nwb).

This should scan all the nwb files in the directory and save the
information about the small datasets and metadata in an SQLite3 database.
Name of the database file will be "nwb_index.db".


2) Running queries.

Queries can be run by running:

python run_query.py  [ <index_file> ]

Where the optional <index_file> is the name of a SQLite3 databaes created in
step 1.  (Default is "nwb_index.db").


Queries are entered using the format described in the NWB Query Engine paper,
except that ":" is used instead of "=", and the parentheses are not required,
and string constants must always be enclosed in either single or doulble
quotes.  Also, the parent location and ":" can be left off, which is the
same as parent location == "*" (search entire tree).

Example queries:

/:session_start_time LIKE "%Jun __ 2013%"

epochs:(start_time>200 & stop_time<220)

/:file_create_date LIKE "%"

/general/subject/: (age LIKE "%3 months 16 days%" & species LIKE "%Mus musculu%") & /:file_create_date LIKE "%2017-04%" & /epochs : start_time < 150

(Above should return two results, on sample files used in nwb query engine:

Found 2:
1. ('../sample_data/data_structure_ANM210862_20130627.nwb', 'general/subject', 'age', '3 months 16 days  weeks', 'species', 'Mus musculus', '', 'file_create_date', '2017-04-24T11:32:54.215883', 'epochs/trial_001', 'start_time', 2.284463)
2. ('../sample_data/data_structure_ANM210863_20130627.nwb', 'general/subject', 'age', '3 months 16 days  weeks', 'species', 'Mus musculus', '', 'file_create_date', '2017-04-24T11:32:54.076284', 'epochs/trial_001', 'start_time', 2.222392)


/general/subject/: (age LIKE "3 months 16 days%" & species LIKE "Mus musculus") & /:session_start_time < "Thu Jun 27 2013 12" & /epochs : start_time < 250

Should return one result:
Found 1:
1. ('../sample_data/data_structure_ANM210862_20130627.nwb', 'general/subject', 'age', '3 months 16 days  weeks', 'species', 'Mus musculus', '', 'session_start_time', 'Thu Jun 27 2013 10:36:32', 'epochs/trial_001', 'start_time', 2.284463)



Limitation:
Currently the queries only work for dataset values, not for any attributes (groups or datasets).
The schema might need to be changed to have queries search both groups and datasets.  Or there might need to be a way to specify explicitly
whether the child value being searched for is a group attribute, dataset attribute or dataset value.






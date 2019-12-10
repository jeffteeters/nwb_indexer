==========================
 nwbindexer and search_nwb
==========================

This repository contains two tools for searching within NWB (HDF5) files:

* **nwbindexer** - builds an SQLite database (also called the 'index') containing metadata in
  a collection of NWB files and and allows searching the metadata in the database.
* **search_nwb.py** - searches within one or more NWB files directly (without building an index).

A related third tool is the **NWB Query Engine**.  It is at:
https://github.com/jezekp/NwbQueryEngine.  The two tools in this repository
use a query syntax similar to the one used in the NWB
Query Engine.


1. Requirements
===============

1. Python 3.7
   (Tested with anaconda Python 3.7; might also work with Python > 3.7.  However, it will *not* work with Python < 3.7).

2. parsimonious parser. Described at:
   https://pypi.org/project/parsimonious/
   Can be installed using:

   ``pip install parsimonious``


3. pytest (only required for running tests).  Can be installed using:

   ``pip install pytest``


2. Installation
===============

1. Download the repository using:

   ``git clone https://github.com/jeffteeters/nwbindexer.git``


2. cd into the created directory:

   ``cd nwbindexer``

3. Optional: if parsimonious and pytest are installed, tests can be run on the downloaded package
   (before installing) by running pytest with no arguments:

   ``pytest``

   Output should indicate all tests (5) passed.

4. To install, make sure you are in the directory 'nwbindexer' containing file "setup.py".  Then type:

   ``pip install .``

5. To test the installation (separately from the files downloaded), cd to a dirctory that does not contain
   the nwbindexer directory, then type:

   ``pytest --pyargs nwbindexer``

   Output should indicate all all tests (5) passed. 


3. nwbindexer usage
=================== 

Searching using nwbindexer requires two steps: 1. building the index (a SQLite database) and 2. searching the index. 

3.1 Build the index
-------------------

The index is built by the ``build_index.py`` program which can be run by entering
either:

``build_nwbindex <nwb_directory> [ <index_path> ]``

or

``python -m nwbindexer.build_index <nwb_directory> [ <index_path> ]``


The first form (``build_nwbindex``) uses a command-line utility installed by the nwbindexer package.  The
second runs the command by specifying the python module directly.  If no arguments are entered, the usage
informatio is displayed.  The arguments are:::

    <nwb_directory> - Name of directory to scan for nwb files (extension ".nwb")
    <index_path>    - Path to index file.
                      If nothing is specified, uses 'nwb_index.db' in the current directory
                      If only a directory specifed, uses 'nwb_index.db' in the specified directory


The command scans all the nwb files in <nwb_directory> (and subdirectories) and saves the
information about small datasets and attributes in the index file (a SQLite3 database) specified by
<index_path>.  The program can be run multiple times with a different <nwb_directory>
and the same <index_path> to add information about additional NWB files to the specified index.


3.2 Running queries
-------------------

Once the index file is built, queries can be run by running either:

``query_nwbindex <index_path> [ <query> ]``

or

``python -m nwbindexer.query_index.py <index_path> [ <query> ]``

Where:::

    <index_path> -  Path to sqlite3 database file or a directory or '-' for the default database (nwb_index.db)
                    If is path to a directory, then use default database (nwb_index.db) in that directory.
    <query>      -  Query to execute (optional).  If present, must be quoted.  If not present, interactive
                    mode is used which allows entering queries interactively.


3.3 Query Format
----------------

Queries are specified using the following format (BNF Grammar):::


    ⟨query⟩ ::= ⟨subquery⟩ ( ⟨andor⟩ ⟨subquery⟩ )*
    ⟨subquery⟩ ::= ⟨parent⟩ ‘:’ ( <rhs> | '(' <rhs> ')' )
    <rhs> ::= ( <child_list> <expression> | <child_list> | <expression> )
    <child_list> ::= <child> ( [ ',' ] <child> )* [ ',' ]
    <expression> ::= ⟨expression⟩ ⟨andor⟩ ⟨expression⟩ | ‘(’ ⟨expression⟩ ‘)’
                     | ⟨child⟩ ⟨relop⟩ ⟨constant⟩
                     | ⟨child⟩ 'LIKE' ⟨string⟩ | ⟨child⟩
    ⟨relop⟩ ::= ‘==’ | ‘<=’ | ‘<’ | ‘>=’ | ‘>’ | ‘!=’
    ⟨constant⟩ ::= ⟨string⟩ | ⟨number⟩
    ⟨andor⟩ ::= ‘&’ | ‘|’


In the grammar: square brakets `[ ]` indicate optional contents, `( )*` indicates zero or more, `( x | y )` indicates `x` or `y` and:

`<parent>`
     is a path to an HDF5 group or dataset. The path can contain asterisk (*) characters which match
     zero or more charaters (e.g. '*' functions as a wildcard). 

`<string>`
     is a string constant enclosed in single or double quotes (with a backslash used to escape quotes).
     Any string constant used with LIKE must have wildcards ("%" or "_") explicitly included (if no wildcards are
     included, the query does an exact match).

`<number>`
     is a numeric constant. 

`<child>`
     is the name of an HDF5 attribute or dataset within the parent.

`<string>`
     is a string constant enclosed in single or double quotes with a backslash used to escape the strings.

`<number>`
     is a numeric constant.


Some example queries:

.. csv-table::
   :header: "Query", "Description"
   :widths: 35, 25

   "/general/subject: (species == ""Mus musculus"")",   "Selects all files with the specified species"
   "/general:(virus)",                                  "Selects all records with a virus dataset"
   "/general:(virus LIKE ""%infectionLocation: M2%"")", "Selects all datasets virus with infectionLocation: M2"
   "\*:(neurodata_type == ""RoiResponseSeries"")",      "Select all TimeSeries containing Calcium imaging data"
   "\*/data: (unit == ""unknown"")",                    "Selects all datasetes data which unit is unknown"
   "\*/epochs/\*: (start_time > 500 & start_time < 550 & tags LIKE ""%HitL%"" & tags LIKE ""%LickEarly%"")", "Select all epochs with the matching start_time and tags"
   "/general/subject: (subject_id == ""anm00210863"") & \*/epochs/\*: (start_time > 500 & start_time < 550 & tags LIKE ""%LickEarly%"")", "Select files with the specified subject_id and epochs"
   "/units: id, location == ""CA3"" & quality > 0.8)",   "Select unit id where location is CA3 and quality > 0.8"



3.4 Example output
------------------

The output generated in this sections is generated using the three sample NWB files included in the package in the "test" directory.
(The commands were run inside directory "nwbindexer/test").

**Building the index**

``$ python -m nwbindexer.build_index ./``::

    Creating database 'nwb_index.db'
    scanning directory ./
    Scanning file 1: ./basic_example.nwb
    Scanning file 2: ./ecephys_example.nwb
    Scanning file 3: ./ophys_example.nwb

(results in creating file ``nwb_index.db``).


**Output from different queries:**


``$ python -m nwbindexer.query_index - "general/optophysiology/*: excitation_lambda == 600.0"``::


    Using index_path: 'nwb_index.db'
    Opening 'nwb_index.db'
    Found 1 matching files:
    [   {   'file': './ophys_example.nwb',
            'subqueries': [   [   {   'node': '/general/optophysiology/my_imgpln',
                                      'vind': {'excitation_lambda': 600.0},
                                      'vtbl': {}}]]}]

``$ python -m nwbindexer.query_index - "general/extracellular_ephys/tetrode1: location LIKE '%hippocampus'"``::

    Using index_path: 'nwb_index.db'
    Opening 'nwb_index.db'
    Found 1 matching files:
    [   {   'file': './ecephys_example.nwb',
            'subqueries': [   [   {   'node': '/general/extracellular_ephys/tetrode1',
                                      'vind': {   'location': 'somewhere in the '
                                                              'hippocampus'},
                                      'vtbl': {}}]]}]

``$ python -m nwbindexer.query_index - "units: id, location == 'CA3' & quality > 0.8"``::

    Using index_path: 'nwb_index.db'
    Opening 'nwb_index.db'
    Found 1 matching files:
    [   {   'file': './basic_example.nwb',
            'subqueries': [   [   {   'node': '/units',
                                      'vind': {},
                                      'vtbl': {   'child_names': [   'id',
                                                                     'location',
                                                                     'quality'],
                                                  'combined': [   {   'id': 2,
                                                                      'location': 'CA3',
                                                                      'quality': 0.85}],
                                                  'row_values': [   (   2,
                                                                        'CA3',
                                                                        0.85)]}}]]}]

3.5 Format of query output
--------------------------

The output of the ``query_index.py`` utility (and also the ``search_nwb.py`` utility described in the next section) is in JSON with the
following structure:

    ``[ <file 1 results>, <file 2 results>, ... ]``

Where each ``file N result`` is a JSON object (equilivant to a python dictionary)
with keys ``file`` and ``subqueries``.

The value associate with the ``File`` key is the full path to the NWB file.  The value of the ``subqueries`` key is an
xarray of subquery results:

    ``[ <subquery 1 result>, <subquery 2 result>, ... ]``

Each ``<subquery N result>`` is a list of ``<node results>`` for that subquery:

    ``[ <node 1 result>, <node 2 result>, ... ]``

Each ``<node N result>`` is a dictionary giving information about the node (location in the HDF5 / NWB file, and the child nodes that are
referenced in the subquery.  The dictionary has keys:
``node`` - the path to the node (group or dataset) withing the HDF5 file
``vind`` - values for 'individual' children of the node, that is, children that are not part of a dynamic table.
``vtbl`` - values for children that are part of a dynamic table.

 
 
 






``/general/subject: (age LIKE "%3 months 16 days%" & species LIKE "%Mus musculu%") & /:file_create_date LIKE "%2017-04%" & /epochs/\* : start_time < 150``


``intervals/trials: id, visual_stimulus_time, visual_stimulus_left_contrast == 0.25 & visual_stimulus_right_contrast == 0.25``



(Using same datasets at the NWB Query Engine test site: http://eeg.kiv.zcu.cz:8080/nwb-query-engine-web/)

``/general/subject: (age LIKE "%3 months 16 days%" & species LIKE "%Mus musculu%") & /:file_create_date LIKE "%2017-04%" & /epochs/\* : start_time < 150``

Output:::

  Opening 'nwb_index.db'
  Found 2 matching files:
  [   {   'file': '../sample_data/data_structure_ANM210862_20130627.nwb',
          'subqueries': [   [   {   'node': '/general/subject',
                                    'vind': {   'age': [   '3 months 16 days  '
                                                           'weeks'],
                                                'species': ['Mus musculus']},
                                    'vtbl': {}}],
                            [   {   'node': '/',
                                    'vind': {   'file_create_date': [   '2017-04-24T11:32:54.21588']},
                                    'vtbl': {}}],
                            [   {   'node': '/epochs/trial_001',
                                    'vind': {'start_time': [2.284463]},
                                    'vtbl': {}}]]},
      {   'file': '../sample_data/data_structure_ANM210863_20130627.nwb',
          'subqueries': [   [   {   'node': '/general/subject',
                                    'vind': {   'age': [   '3 months 16 days  '
                                                           'weeks'],
                                                'species': ['Mus musculus']},
                                    'vtbl': {}}],
                            [   {   'node': '/',
                                    'vind': {   'file_create_date': [   '2017-04-24T11:32:54.07628']},
                                    'vtbl': {}}],
                            [   {   'node': '/epochs/trial_001',
                                    'vind': {'start_time': [2.222392]},
                                    'vtbl': {}}]]}]


**Example query (NWB 2.x files):**


``python query_index.py - '/units: id, location, quality > 0.93'``

Output:::


   Opening 'nwb_index.db'
   Found 1 matching files:
   [   {   'file': '../pynwb_examples/tutorials_python/general/basic_example.nwb',
           'subqueries': [   [   {   'node': '/units',
                                     'vind': {},
                                     'vtbl': {   'child_names': [   'id',
                                                                    'location',
                                                                    'quality'],
                                                 'row_values': [   (   1,
                                                                       'CA1',
                                                                       0.95)]}}]]}]



4. search_nwb.py usage
======================

The search_nwb.py utility operates like the NWB Query Engine, searching either all nwb files in a directory or a specific NWB file.

It is run using either:

``search_nwb <data_path> [ <query> ]``

or

``python -m nwbindexer.search_nwb <data_path> [ <query> ]``

Where:

   <data_path>:
       Path to NWB file or directory

    <query>:
       Query to execute (optional).  If present, must be quoted.



4.1 Example query (NWB 1.x files)
---------------------------------


``python search_nwb.py ../sample_data/ '/general/subject: (age LIKE "%3 months 16 days%" & species LIKE "%Mus musculu%") & /:file_create_date LIKE "%2017-04%" & /epochs/* : start_time < 150``

Output:::

   Found 2 matching files:
   [   {   'file': '../sample_data/data_structure_ANM210862_20130627.nwb',
           'subqueries': [   [   {   'node': '/general/subject',
                                     'vind': {   'age': [   b'3 months 16 days  weeks'],
                                                 'species': [b'Mus musculus']},
                                     'vtbl': {}}],
                             [   {   'node': '/',
                                     'vind': {   'file_create_date': [   b'2017'
                                                                         b'-04-'
                                                                         b'24T1'
                                                                         b'1:32'
                                                                         b':54.'
                                                                         b'2158'
                                                                         b'83']},
                                     'vtbl': {}}],
                             [   {   'node': '/epochs/trial_001',
                                     'vind': {'start_time': [2.284463]},
                                     'vtbl': {}}]]},
       {   'file': '../sample_data/data_structure_ANM210863_20130627.nwb',
           'subqueries': [   [   {   'node': '/general/subject',
                                     'vind': {   'age': [   b'3 months 16 days  weeks'],
                                                 'species': [b'Mus musculus']},
                                     'vtbl': {}}],
                             [   {   'node': '/',
                                     'vind': {   'file_create_date': [   b'2017'
                                                                         b'-04-'
                                                                         b'24T1'
                                                                         b'1:32'
                                                                         b':54.'
                                                                         b'0762'
                                                                         b'84']},
                                     'vtbl': {}}],
                             [   {   'node': '/epochs/trial_001',
                                     'vind': {'start_time': [2.222392]},
                                     'vtbl': {}}]]}]


The output is the same as for query_index.py, except strings displayed as bytes instead of python strings.  This is because
the strings are stored as bytes in the NWB (HDF5) file but as strings in the sqlite3 database.  TODO: Need to
explain this better.  The time for the query is much longer (15 seconds vs less than 1 second for the query_index.py tool).



4.2 Example query (NWB 2.x files)
---------------------------------


``time python search_nwb.py ../pynwb_examples/ '/units: id, location, quality > 0.93``

Output:::

   Found 1 matching files:
   [   {   'file': '../pynwb_examples/tutorials_python/general/basic_example.nwb',
           'subqueries': [   [   {   'node': '/units',
                                     'vind': {},
                                     'vtbl': {   'child_names': [   'id',
                                                                    'location',
                                                                    'quality'],
                                                 'row_values': [   (   1,
                                                                       'CA1',
                                                                       0.95)]}}]]}]

   real								    0m1.245s
   user								    0m0.383s
   sys								    0m0.208s




Version History
===============

0.1.0 - Initial version.  Works on a variety of files tested.

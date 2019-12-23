.. index::
   single: Example output

Example output
==============

The output presented in this sections was generated using the three
sample NWB files included in the nwbindexer package in the "test" directory.
(The commands were run inside directory *nwbindexer/test* which contains
three nwb files).

Building the index
------------------

Command entered:

``python -m nwbindexer.build_index ./``

Output is:

.. code:: none

    Creating database 'nwb_index.db'
    scanning directory ./
    Scanning file 1: ./basic_example.nwb
    Scanning file 2: ./ecephys_example.nwb
    Scanning file 3: ./ophys_example.nwb

(results in creating file *nwb_index.db*).


Output from queries
-------------------

Query entered:

``python -m nwbindexer.query_index - "general/optophysiology/*: excitation_lambda == 600.0"``


Output:

.. code:: none

    Using index_path: 'nwb_index.db'
    Opening 'nwb_index.db'
    Found 1 matching files:
    [   {   'file': './ophys_example.nwb',
            'subqueries': [   [   {   'node': '/general/optophysiology/my_imgpln',
                                      'vind': {'excitation_lambda': 600.0},
                                      'vtbl': {}}]]}]

Query:

``python -m nwbindexer.query_index - "general/extracellular_ephys/tetrode1: location LIKE '%hippocampus'"``

Output:

.. code:: none

    Using index_path: 'nwb_index.db'
    Opening 'nwb_index.db'
    Found 1 matching files:
    [   {   'file': './ecephys_example.nwb',
            'subqueries': [   [   {   'node': '/general/extracellular_ephys/tetrode1',
                                      'vind': {   'location': 'somewhere in the '
                                                              'hippocampus'},
                                      'vtbl': {}}]]}]

Query:

``python -m nwbindexer.query_index - "units: id, location == 'CA3' & quality > 0.8"``

Output:

.. code:: none

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

.. index:: Query output format

.. _format_of_query_output:


Format of query output
----------------------

The output of the *query_index.py* utility (and also the *search_nwb.py* utility described in the
next section) is in JSON (https://www.json.org/) with the following structure:

   [ *<file 1 results>*, *<file 2 results>*, ... ]

Where each *<file N results>* is a JSON object (similar to a python dictionary)
with keys *file* and *subqueries*.

The value associate with the *file* key is the full path to the NWB file.  The value of the *subqueries* key is an
array of subquery results:

    [ *<subquery 1 result>*, *<subquery 2 result>*, ... ]

Each *<subquery N result>* is a list of *<node results>* for that subquery:

    [ *<node 1 result>*, *<node 2 result>*, ... ]

Each *<node N result>* is a dictionary giving information about the parent node (location in the HDF5 / NWB file,
and child nodes (groups, attributes or datasets directly within the parent) that are referenced in the subquery.  The dictionary has keys:

node
    The path to the parent node (group or dataset) withing the HDF5 file.

vind
    Values for 'individual' children of the node, that is, children that are not part of a NWB DynamicTable (described below).
    The values are provided in a JSON object (Python dictionary) where the keys are the name of each child and the
    values are the values stored in the child.

vtbl
    Values for children that are part of a NWB DynamicTable.  An NWB DynamicTable is a method used within the NWB format
    to store tabular data that are aligned along the rows, like a spreadsheet.  It is described at:
    https://nwb-schema.readthedocs.io/en/latest/format.html#sec-dynamictable.  The value of *vtbl* is described
    in the next section.


The value of *vtbl* is a JSON Object (Python dictionary) with keys: *child_names*, *row_values* and *combined*.
They have the following meaning:

child_names
    A tuple listing all of the children.  This is equivalent to the header row in a spreadsheet which lists in order,
    the columns in the spreadsheet.

row_values
    Contains a list of tuples, each tuple contains aligned values associated with the names in *child_names*.
    In other words, each tuple has vaues for one row of the spreadsheet in order of the header *child_names*.

combined
    Contains a list of JSON Objects (Python dictionaries), where each dictionary has data for one row in the returned
    results.  That is, in each dictionary, the keys are the *child_names* (spredsheet header column names) and
    the value for each key is the value of that child in the row.  This is another way of represening the data
    that are in *child_names* and *row_values*.

.. index::
   single: nwbindexer usage
   single: build_nwbindex
   single: build_index
   single: query_nwbindex
   single: query_index
   pair: index file; nwb_index.db

.. _nwbindexer_usage:


nwbindexer usage
================ 

Searching using nwbindexer requires two steps: 1. building the index (a SQLite database) and 2. searching the index. 

Build the index
---------------

The index is built by the ``build_index.py`` program which can be run by entering
either:

``build_nwbindex <nwb_directory> [ <index_path> ]``

or

``python -m nwbindexer.build_index <nwb_directory> [ <index_path> ]``


The first form (``build_nwbindex``) uses a command-line utility installed by the nwbindexer package.  The
second runs the command by specifying the python module directly.  If no arguments are entered, the usage
information is displayed.  The arguments are: ::

    <nwb_directory> - Name of directory to scan for nwb files (extension ".nwb")
    <index_path>    - Path to index file.
                      If nothing is specified, uses 'nwb_index.db' in the current directory
                      If only a directory specifed, uses 'nwb_index.db' in the specified directory


The command scans all the nwb files in <nwb_directory> (and subdirectories) and saves the
information about small datasets and attributes in the index file (a SQLite3 database) specified by
<index_path>.  The default name of the index file is ``nwb_index.db``.
The program can be run multiple times with a different <nwb_directory>
and the same <index_path> to add information about additional NWB files to the specified index.

.. index::
   pair: nwbindexer usage; Running queries

Running queries
---------------

Once the index file is built, queries can be run by running either:

``query_nwbindex <index_path> [ <query> ]``

or

``python -m nwbindexer.query_index.py <index_path> [ <query> ]``

Where:::

    <index_path> -  Path to sqlite3 database file or a directory or '-' for the default database (nwb_index.db)
                    If is path to a directory, then use default database (nwb_index.db) in that directory.
    <query>      -  Query to execute (optional).  If present, must be quoted.  If not present, interactive
                    mode is used which allows entering queries interactively.

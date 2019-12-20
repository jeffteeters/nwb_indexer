.. nwbindexer documentation master file, created by
   sphinx-quickstart on Thu Dec 19 15:23:56 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to nwbindexer's documentation!
======================================

*nwbindexer* is a python package that contains two tools for searching within NWB (HDF5) files:

* **nwbindexer** - builds an SQLite database (also called the 'index') containing metadata in
  a collection of NWB files and and allows searching the metadata in the database.
* **search_nwb.py** - searches within one or more NWB files directly (without building an index).

The source repository for nwbindexer is: https://github.com/jeffteeters/nwbindexer.
A related third tool is the **NWB Query Engine**.  It is at:
https://github.com/jezekp/NwbQueryEngine.  The two tools in nwbindexer
use a query syntax similar to the one used in the NWB Query Engine.


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   requirements
   installation
   query_format
   nwbindexer_usage
   example_output
   search_nwb_usage
   multiple_subqueries
   speed_check
   nwb_files_used


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

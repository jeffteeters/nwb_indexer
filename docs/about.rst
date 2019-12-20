About nwbindexer
================

*nwbindexer* is a python package that contains two tools for searching within NWB (HDF5) files:

* **nwbindexer** - builds an SQLite database (also called the 'index') containing metadata in
  a collection of NWB files and and allows searching the metadata in the database.
* **search_nwb.py** - searches within one or more NWB files directly (without building an index).

The source repository for nwbindexer is: https://github.com/jeffteeters/nwbindexer.
A related third tool is the **NWB Query Engine**.  It is at:
https://github.com/jezekp/NwbQueryEngine.  The two tools in nwbindexer
use a query syntax similar to the one used in the NWB Query Engine.

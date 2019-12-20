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

Documentation for nwbindexer is at: https://nwbindexer.readthedocs.io


Installation & Usage
====================

Instructions for installation and usage are at:
https://nwbindexer.readthedocs.io

License
=======

License terms are in file ``license.txt`` (reproduced below).


.. include:: license.txt


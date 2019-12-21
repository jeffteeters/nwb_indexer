About nwbindexer
================

.. index::
   single: nwbindexer
   single: NWB Query Engine
   single: search_nwb.py

*nwbindexer* is a python package that contains two tools for searching within
*Neurodata Without Borders* files (abbreviation **NWB**, described at: https://nwb-schema.readthedocs.io/en/latest/)
that are stored using the HDF5 (https://portal.hdfgroup.org/display/HDF5/HDF5) format.
The two tools are:



* :ref:`nwbindexer <nwbindexer_usage>` - builds an SQLite database (also called the 'index') containing metadata in
  a collection of NWB files and and allows searching the metadata in the database.

* :ref:`search_nwb.py <search_nwb_usage>` - searches within one or more NWB files directly (without building an index).

The source repository for nwbindexer is: https://github.com/jeffteeters/nwbindexer.
A related third tool is the **NWB Query Engine**.  It is at:
https://github.com/jezekp/NwbQueryEngine.  The two tools in nwbindexer
use a :ref:`query format <query_format>` similar to the one used in the NWB Query Engine.
A webpage allowing example searches using all three tools is at:
http://eeg.kiv.zcu.cz:8080/nwb-query-engine-web/.




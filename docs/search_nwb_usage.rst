search_nwb.py usage
===================


The search_nwb.py tool searches directly within NWB files for data matching a query.  It does not use an index file
(unlike the nwbindexer tool).

The search_nwb tool is run using either:

``search_nwb <path> [ <query> ]``

or

``python -m nwbindexer.search_nwb.pr <path> [ <query> ]``

The first form (search_nwb) uses a command-line utility installed by the nwbindexer package.
The second runs the command by specifying the python module directly. If no arguments are entered,
the usage information is displayed. The arguments are:

``<path>``
    path to an NWB file or a directory containing nwb files.

``<query>``
    query to execute (optional).  If present, must be quoted.


The ``<query>`` is described in Section :ref:`query_format`.
The output format of ``search_nwb.py`` is described in :ref:`format_of_query_output`.  Is the same as for ``query_index.py``
described in :ref:`nwbindexer_usage`.

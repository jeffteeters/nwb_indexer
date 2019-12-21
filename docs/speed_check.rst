.. index::
   single: speed_check.py


speed_check.py
==============

Also included in the package is a program named ``speed_check.py``, which can be used to compare the speed
of different queries performed using the two tools in this package (``query_index.py`` and ``search_nwb.py``)
and also the Java tool (the NWB Query Engine, available at: https://github.com/jezekp/NwbQueryEngine).

Running ``speed_check.py`` without any command-line arguments displays the instructions:

``python -m nwbindexer.speed_check``

Output is:::

   Usage: /.../speed_check.py ( i | - | <query> ) [ <data_dir> [ <java_tool_dir> ] ]
    First parameter required:
       Either one characer: 'i' - interactive mode, '-' use stored default queries
       *OR* a single query to execute; must be quoted.
    After the first parameter, optionally specify:
       <data_dir> - directory containing nwb files AND index file ('nwb_index.db' built by build_index.py)
       <java_tool_dir> - directory containing NWB Query Engine (java tool)
       If <data_dir> not specified, uses: ../sample_data
       If <java_tool_dir> not specified, uses: /Users/jt/crcns/projects/petr_nwbqe_paper/NwbQueryEngine4


The source of the script (file ``speed_check.py``) can be edited to change the default directory for the <java_tool_dir>.


An example run of the tool and the final output is shown below.


$ python -m nwbindexer.speed_check - ../../sample_data

Output::
   
   # A
   
   ------- query A -------
   epochs*:(start_time>200 & stop_time<400 | stop_time>1600)
   Starting: ** java ** with: epochs*:(start_time>200 & stop_time<400 | stop_time>1600)
   dir:/Users/jt/crcns/projects/petr_nwbqe_paper/NwbQueryEngine4
   cmd:java -Djava.library.path=src/main/resources/ -jar target/nwbqueryengine-1.0-SNAPSHOT-jar-with-dependencies.jar /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data 'epochs*:(start_time>200 & stop_time<400 | stop_time>1600)'
   Dataset: epochs/trial_011/stop_time, Value: 223.430533, DataStorageName: /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data/nwb1/data_structure_ANM210861_20130701.nwb
   Dataset: epochs/trial_010/stop_time, Value: 214.274403, DataStorageName: /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data/nwb1/data_structure_ANM210861_20130701.nwb
   Dataset: epochs/trial_018/start_time, Value: 312.970341, DataStorageName: /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data/nwb1/data_structure_ANM210861_20130701.nwb
   
   ...
   
   Time, user=12.9647, sys=1.2751, total=14.2398
   Starting: ** search_nwb ** with: epochs*:(start_time>200 & stop_time<400 | stop_time>1600)
   dir:/Users/jt/crcns/projects/petr_nwbqe_paper/NwbQueryEngine4
   cmd:python -m nwbindexer.search_nwb /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data 'epochs*:(start_time>200 & stop_time<400 | stop_time>1600)'
   Found 16 matching files:
   [   {   'file': '/Users/jt/crcns/projects/petr_nwbqe_paper/sample_data/nwb1/data_structure_ANM210861_20130701.nwb',
           'subqueries': [   [   {   'node': '/epochs/trial_010',
                                     'vind': {   'start_time': 202.908281,
                                                 'stop_time': 214.274403},
                                     'vtbl': {}},
                                 {   'node': '/epochs/trial_011',
                                     'vind': {   'start_time': 214.274403,
                                                 'stop_time': 223.430533},
                                     'vtbl': {}},
                                 {   'node': '/epochs/trial_012',
                                     'vind': {   'start_time': 223.430533,
                                                 'stop_time': 243.704452},
                                     'vtbl': {}},
      
   ...
   
   Time, user=22.2331, sys=1.4197, total=23.6527
   Starting: ** query_index ** with: epochs*:(start_time>200 & stop_time<400 | stop_time>1600)
   dir:/Users/jt/crcns/projects/petr_nwbqe_paper/NwbQueryEngine4
   cmd:python -m nwbindexer.query_index /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data/nwb_index.db 'epochs*:(start_time>200 & stop_time<400 | stop_time>1600)'
   Opening '/Users/jt/crcns/projects/petr_nwbqe_paper/sample_data/nwb_index.db'
   Found 16 matching files:
   [   {   'file': './nwb1/data_structure_ANM210861_20130701.nwb',
           'subqueries': [   [   {   'node': '/epochs/trial_010',
                                     'vind': {   'start_time': 202.908281,
                                                 'stop_time': 214.274403},
                                     'vtbl': {}},
                                 {   'node': '/epochs/trial_011',
                                     'vind': {   'start_time': 214.274403,
                                                 'stop_time': 223.430533},
                                     'vtbl': {}},
                                 {   'node': '/epochs/trial_012',
                                     'vind': {   'start_time': 223.430533,
                                                 'stop_time': 243.704452},
                                     'vtbl': {}},
   ...
   
   Time, user=1.9567, sys=0.2405, total=2.1972
   # B
   
   ------- query B -------
   */data: (unit == "unknown")
   Starting: ** java ** with: */data: (unit == "unknown")
   dir:/Users/jt/crcns/projects/petr_nwbqe_paper/NwbQueryEngine4
   cmd:java -Djava.library.path=src/main/resources/ -jar target/nwbqueryengine-1.0-SNAPSHOT-jar-with-dependencies.jar /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data '*/data: (unit == "unknown")'
   Dataset: acquisition/timeseries/lick_trace/data/unit, Value: unknown, DataStorageName: /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data/nwb1/data_structure_ANM210861_20130701.nwb
   Dataset: stimulus/presentation/pole_in/data/unit, Value: unknown, DataStorageName: /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data/nwb1/data_structure_ANM210861_20130701.nwb
   
   ...
   
   
   Time, user=0.3968, sys=0.0924, total=0.4892
   # G
   # Don't include this because there are so many groups found in the Churchland dataset
   # *:(neurodata_type == "RoiResponseSeries")
   
   Queries in test:
   A. epochs*:(start_time>200 & stop_time<400 | stop_time>1600)
   B. */data: (unit == "unknown")
   C. general/subject: (subject_id == "anm00210863") & epochs/*: (start_time > 500 & start_time < 550 & tags LIKE "%LickEarly%")
   D. units: (id > -1 & location == "CA3" & quality > 0.8)
   E. general:(virus LIKE "%infectionLocation: M2%")
   F. general/optophysiology/*: (excitation_lambda)
   timing results are:
   qid	java	search_nwb	query_index
   A	14.2398	23.6527	2.1972
   B	50.8242	74.5105	1.0670
   C	16.8795	27.2111	0.5328
   D	2.2005	0.5240	0.4821
   E	1.8188	0.5704	0.4783
   F	1.7239	0.6262	0.4892
   

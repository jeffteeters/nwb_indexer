.. index::
   single: speed_check.py

.. _speed_check:

speed_check.py
==============

Also included in the package is a program named *speed_check.py*, which can be used to compare the speed
of different queries performed using the two query tools in this package (the nwbindexer
:ref:`query_index.py <query_the_index>` and :ref:`search_nwb.py <search_nwb_usage>`)
and also the Java tool (the *NWB Query Engine*, available at: https://github.com/jezekp/NwbQueryEngine).

Running *speed_check.py* without any command-line arguments displays the instructions:

$ ``python -m nwbindexer.speed_check``

Output is:

.. code-block:: none

   Usage: speed_check.py ( i | - | <query> ) [ <data_dir> [ <java_tool_dir> ] ]
    First parameter required:
       Either one character: 'i' - interactive mode, '-' use stored default queries
       *OR* a single query to execute; must be quoted.
    After the first parameter, optionally specify:
       <data_dir> - directory containing NWB files AND index file ('nwb_index.db' built by build_index.py)
       <java_tool_dir> - directory containing NWB Query Engine (Java tool)
       If <data_dir> not specified, uses: ../sample_data
       If <java_tool_dir> not specified, uses: /Users/jt/crcns/projects/petr_nwbqe_paper/NwbQueryEngine4


The source of the script (file *speed_check.py*) can be edited to change the defaults 
for *<data_dir>* and *<java_tool_dir>*.

An example run of the tool and the final output is shown below.  A line with three dots ( ... )
indicates lines that were removed from the output to reduce the length.  The actual output is over
41,000 lines because some of the queries return lots of results.  The times shown in the results
can vary between runs due to variations in the system operation (threads running, memory usage)
during each run. 


$ ``python -m nwbindexer.speed_check - ../../sample_data``

Output:

.. code-block:: none
   
   # A
   
   ------- query A -------
   epochs*:(start_time>200 & stop_time<400 | stop_time>1600)
   Starting: ** java ** with: epochs*:(start_time>200 & stop_time<400 | stop_time>1600)
   dir:/Users/jt/crcns/projects/petr_nwbqe_paper/NwbQueryEngine4
   cmd:java -Djava.library.path=src/main/resources/ -jar target/nwbqueryengine-1.0-SNAPSHOT-jar-with-dependencies.jar /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019 'epochs*:(start_time>200 & stop_time<400 | stop_time>1600)'
   Dataset: epochs/trial_014/stop_time, Value: 284.13879, DataStorageName: /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/alm-1/data_structure_ANM210861_20130701.nwb
   Dataset: epochs/trial_015/stop_time, Value: 293.936084, DataStorageName: /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/alm-1/data_structure_ANM210861_20130701.nwb
   Dataset: epochs/trial_014/start_time, Value: 273.647165, DataStorageName: /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/alm-1/data_structure_ANM210861_20130701.nwb
   
   ...
   
   Time, user=12.2728, sys=1.3091, total=13.5819
   Starting: ** search_nwb ** with: epochs*:(start_time>200 & stop_time<400 | stop_time>1600)
   dir:/Users/jt/crcns/projects/petr_nwbqe_paper/NwbQueryEngine4
   cmd:python -m nwbindexer.search_nwb /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019 'epochs*:(start_time>200 & stop_time<400 | stop_time>1600)'
   Found 16 matching files:
   [   {   'file': '/Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/alm-1/data_structure_ANM210861_20130701.nwb',
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
   
   Time, user=18.2934, sys=0.6842, total=18.9776
   Starting: ** query_index ** with: epochs*:(start_time>200 & stop_time<400 | stop_time>1600)
   dir:/Users/jt/crcns/projects/petr_nwbqe_paper/NwbQueryEngine4
   cmd:python -m nwbindexer.query_index /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/nwb_index.db 'epochs*:(start_time>200 & stop_time<400 | stop_time>1600)'
   Opening '/Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/nwb_index.db'
   Found 16 matching files:
   [   {   'file': './alm-1/data_structure_ANM210861_20130701.nwb',
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
   
   Time, user=1.4893, sys=0.1334, total=1.6227
   # B
   
   ------- query B -------
   */data: (unit == "unknown")
   Starting: ** java ** with: */data: (unit == "unknown")
   dir:/Users/jt/crcns/projects/petr_nwbqe_paper/NwbQueryEngine4
   cmd:java -Djava.library.path=src/main/resources/ -jar target/nwbqueryengine-1.0-SNAPSHOT-jar-with-dependencies.jar /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019 '*/data: (unit == "unknown")'
   Dataset: acquisition/timeseries/lick_trace/data/unit, Value: unknown, DataStorageName: /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/alm-1/data_structure_ANM210861_20130701.nwb
   Dataset: stimulus/presentation/pole_in/data/unit, Value: unknown, DataStorageName: /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/alm-1/data_structure_ANM210861_20130701.nwb
   Dataset: stimulus/presentation/pole_out/data/unit, Value: unknown, DataStorageName: /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/alm-1/data_structure_ANM210861_20130701.nwb
   
   ...
   
   Time, user=35.2372, sys=7.9713, total=43.2085
   Starting: ** search_nwb ** with: */data: (unit == "unknown")
   dir:/Users/jt/crcns/projects/petr_nwbqe_paper/NwbQueryEngine4
   cmd:python -m nwbindexer.search_nwb /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019 '*/data: (unit == "unknown")'
   Found 16 matching files:
   [   {   'file': '/Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/alm-1/data_structure_ANM210861_20130701.nwb',
           'subqueries': [   [   {   'node': '/acquisition/timeseries/lick_trace/data',
                                     'vind': {'unit': 'unknown'},
                                     'vtbl': {}},
                                 {   'node': '/stimulus/presentation/pole_in/data',
                                     'vind': {'unit': 'unknown'},
                                     'vtbl': {}},
                                 {   'node': '/stimulus/presentation/pole_out/data',
                                     'vind': {'unit': 'unknown'},
                                     'vtbl': {}}]]},
       {   'file': '/Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/alm-1/data_structure_ANM210861_20130702.nwb',
           'subqueries': [   [   {   'node': '/acquisition/timeseries/lick_trace/data',
                                     'vind': {'unit': 'unknown'},
                                     'vtbl': {}},
   ...
   
   Time, user=53.5027, sys=6.2422, total=59.7449
   Starting: ** query_index ** with: */data: (unit == "unknown")
   dir:/Users/jt/crcns/projects/petr_nwbqe_paper/NwbQueryEngine4
   cmd:python -m nwbindexer.query_index /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/nwb_index.db '*/data: (unit == "unknown")'
   Opening '/Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/nwb_index.db'
   Found 16 matching files:
   [   {   'file': './alm-1/data_structure_ANM210861_20130701.nwb',
           'subqueries': [   [   {   'node': '/acquisition/timeseries/lick_trace/data',
                                     'vind': {'unit': 'unknown'},
                                     'vtbl': {}},
                                 {   'node': '/stimulus/presentation/pole_in/data',
                                     'vind': {'unit': 'unknown'},
                                     'vtbl': {}},
                                 {   'node': '/stimulus/presentation/pole_out/data',
                                     'vind': {'unit': 'unknown'},
                                     'vtbl': {}}]]},
       {   'file': './alm-1/data_structure_ANM210861_20130702.nwb',
           'subqueries': [   [   {   'node': '/acquisition/timeseries/lick_trace/data',
                                     'vind': {'unit': 'unknown'},
                                     'vtbl': {}},
   ...
   
   Time, user=0.6256, sys=0.3118, total=0.9373
   # C
   
   ------- query C -------
   general/subject: (subject_id == "anm00210863") & epochs/*: (start_time > 500 & start_time < 550 & tags LIKE "%LickEarly%")
   Starting: ** java ** with: general/subject: (subject_id == "anm00210863") & epochs/*: (start_time > 500 & start_time < 550 & tags LIKE "%LickEarly%")
   dir:/Users/jt/crcns/projects/petr_nwbqe_paper/NwbQueryEngine4
   cmd:java -Djava.library.path=src/main/resources/ -jar target/nwbqueryengine-1.0-SNAPSHOT-jar-with-dependencies.jar /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019 'general/subject: (subject_id == "anm00210863") & epochs/*: (start_time > 500 & start_time < 550 & tags LIKE "%LickEarly%")'
   Dataset: epochs/trial_042/start_time, Value: 508.403336, DataStorageName: /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/alm-1/data_structure_ANM210863_20130628.nwb
   Dataset: epochs/trial_042/tags, Value: LickEarly, DataStorageName: /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/alm-1/data_structure_ANM210863_20130628.nwb
   Dataset: epochs/trial_044/tags, Value: LickEarly, DataStorageName: /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/alm-1/data_structure_ANM210863_20130628.nwb
   Dataset: general/subject/subject_id, Value: anm00210863, DataStorageName: /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/alm-1/data_structure_ANM210863_20130628.nwb
   Dataset: epochs/trial_044/start_time, Value: 527.017762, DataStorageName: /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/alm-1/data_structure_ANM210863_20130628.nwb
   
   Time, user=12.9052, sys=1.0476, total=13.9528
   Starting: ** search_nwb ** with: general/subject: (subject_id == "anm00210863") & epochs/*: (start_time > 500 & start_time < 550 & tags LIKE "%LickEarly%")
   dir:/Users/jt/crcns/projects/petr_nwbqe_paper/NwbQueryEngine4
   cmd:python -m nwbindexer.search_nwb /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019 'general/subject: (subject_id == "anm00210863") & epochs/*: (start_time > 500 & start_time < 550 & tags LIKE "%LickEarly%")'
   Found 1 matching files:
   [   {   'file': '/Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/alm-1/data_structure_ANM210863_20130628.nwb',
           'subqueries': [   [   {   'node': '/general/subject',
                                     'vind': {'subject_id': 'anm00210863'},
                                     'vtbl': {}}],
                             [   {   'node': '/epochs/trial_042',
                                     'vind': {   'start_time': 508.403336,
                                                 'tags': 'LickEarly'},
                                     'vtbl': {}},
                                 {   'node': '/epochs/trial_044',
                                     'vind': {   'start_time': 527.017762,
                                                 'tags': 'LickEarly'},
                                     'vtbl': {}}]]}]
   
   Time, user=18.6881, sys=0.6488, total=19.3369
   Starting: ** query_index ** with: general/subject: (subject_id == "anm00210863") & epochs/*: (start_time > 500 & start_time < 550 & tags LIKE "%LickEarly%")
   dir:/Users/jt/crcns/projects/petr_nwbqe_paper/NwbQueryEngine4
   cmd:python -m nwbindexer.query_index /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/nwb_index.db 'general/subject: (subject_id == "anm00210863") & epochs/*: (start_time > 500 & start_time < 550 & tags LIKE "%LickEarly%")'
   Opening '/Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/nwb_index.db'
   Found 1 matching files:
   [   {   'file': './alm-1/data_structure_ANM210863_20130628.nwb',
           'subqueries': [   [   {   'node': '/general/subject',
                                     'vind': {'subject_id': 'anm00210863'},
                                     'vtbl': {}}],
                             [   {   'node': '/epochs/trial_042',
                                     'vind': {   'start_time': 508.403336,
                                                 'tags': 'LickEarly'},
                                     'vtbl': {}},
                                 {   'node': '/epochs/trial_044',
                                     'vind': {   'start_time': 527.017762,
                                                 'tags': 'LickEarly'},
                                     'vtbl': {}}]]}]
   
   Time, user=0.3300, sys=0.0903, total=0.4202
   # D
   
   ------- query D -------
   units: (id > -1 & location == "CA3" & quality > 0.8)
   Starting: ** java ** with: units: (id > -1 & location == "CA3" & quality > 0.8)
   dir:/Users/jt/crcns/projects/petr_nwbqe_paper/NwbQueryEngine4
   cmd:java -Djava.library.path=src/main/resources/ -jar target/nwbqueryengine-1.0-SNAPSHOT-jar-with-dependencies.jar /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019 'units: (id > -1 & location == "CA3" & quality > 0.8)'
   Dataset: units/quality, Value: 0.95, DataStorageName: /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/tutorials/general/example_file_path.nwb
   Dataset: units/quality, Value: 0.85, DataStorageName: /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/tutorials/general/example_file_path.nwb
   Dataset: units/id, Value: 3, DataStorageName: /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/tutorials/general/example_file_path.nwb
   Dataset: units/object_id, Value: 7eed28e5-b006-4b7d-85c2-456e3faed827, DataStorageName: /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/tutorials/general/example_file_path.nwb
   Dataset: units/quality, Value: 0.9, DataStorageName: /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/tutorials/general/example_file_path.nwb
   Dataset: units/id, Value: 1, DataStorageName: /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/tutorials/general/example_file_path.nwb
   Dataset: units/id, Value: 2, DataStorageName: /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/tutorials/general/example_file_path.nwb
   Dataset: units/location, Value: CA3, DataStorageName: /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/tutorials/general/example_file_path.nwb
   
   Time, user=1.6262, sys=0.1597, total=1.7858
   Starting: ** search_nwb ** with: units: (id > -1 & location == "CA3" & quality > 0.8)
   dir:/Users/jt/crcns/projects/petr_nwbqe_paper/NwbQueryEngine4
   cmd:python -m nwbindexer.search_nwb /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019 'units: (id > -1 & location == "CA3" & quality > 0.8)'
   Found 1 matching files:
   [   {   'file': '/Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/tutorials/general/example_file_path.nwb',
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
   
   Time, user=0.3486, sys=0.0784, total=0.4270
   Starting: ** query_index ** with: units: (id > -1 & location == "CA3" & quality > 0.8)
   dir:/Users/jt/crcns/projects/petr_nwbqe_paper/NwbQueryEngine4
   cmd:python -m nwbindexer.query_index /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/nwb_index.db 'units: (id > -1 & location == "CA3" & quality > 0.8)'
   Opening '/Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/nwb_index.db'
   Found 1 matching files:
   [   {   'file': './tutorials/general/example_file_path.nwb',
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
   
   Time, user=0.3183, sys=0.0751, total=0.3934
   # E
   
   ------- query E -------
   general:(virus LIKE "%infectionLocation: M2%")
   Starting: ** java ** with: general:(virus LIKE "%infectionLocation: M2%")
   dir:/Users/jt/crcns/projects/petr_nwbqe_paper/NwbQueryEngine4
   cmd:java -Djava.library.path=src/main/resources/ -jar target/nwbqueryengine-1.0-SNAPSHOT-jar-with-dependencies.jar /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019 'general:(virus LIKE "%infectionLocation: M2%")'
   Dataset: general/virus, Value:        infectionCoordinates: [2.5, -1.5, 0.5],[2.5, -1.5, 0.85]         infectionLocation: M2         injectionDate: 20130523         injectionVolume: 30,30         virusID: Addgene41015         virusLotNumber:          virusSource: Janelia core         virusTiter: untitered  , DataStorageName: /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/alm-1/data_structure_ANM210861_20130701.nwb
   Dataset: general/virus, Value:        infectionCoordinates: [2.5, -1.5, 0.5],[2.5, -1.5, 0.85]         infectionLocation: M2         injectionDate: 20130523         injectionVolume: 30,30         virusID: Addgene41015         virusLotNumber:          virusSource: Janelia core         virusTiter: untitered  , DataStorageName: /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/alm-1/data_structure_ANM210861_20130702.nwb
   Dataset: general/virus, Value:        infectionCoordinates: [2.5, -1.5, 0.5],[2.5, -1.5, 0.85]         infectionLocation: M2         injectionDate: 20130523         injectionVolume: 30,30         virusID: Addgene41015         virusLotNumber:          virusSource: Janelia core         virusTiter: untitered  , DataStorageName: /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/alm-1/data_structure_ANM210861_20130703.nwb
   
   ...
   
   Time, user=1.4199, sys=0.1367, total=1.5565
   Starting: ** search_nwb ** with: general:(virus LIKE "%infectionLocation: M2%")
   dir:/Users/jt/crcns/projects/petr_nwbqe_paper/NwbQueryEngine4
   cmd:python -m nwbindexer.search_nwb /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019 'general:(virus LIKE "%infectionLocation: M2%")'
   Found 16 matching files:
   [   {   'file': '/Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/alm-1/data_structure_ANM210861_20130701.nwb',
           'subqueries': [   [   {   'node': '/general',
                                     'vind': {   'virus': '       '
                                                          'infectionCoordinates: '
                                                          '[2.5, -1.5, 0.5],[2.5, '
                                                          '-1.5, 0.85]\n'
                                                          '        '
                                                          'infectionLocation: M2\n'
                                                          '        injectionDate: '
                                                          '20130523\n'
                                                          '        '
                                                          'injectionVolume: '
                                                          '30,30\n'
                                                          '        virusID: '
                                                          'Addgene41015\n'
                                                          '        '
                                                          'virusLotNumber: \n'
                                                          '        virusSource: '
                                                          'Janelia core\n'
                                                          '        virusTiter: '
                                                          'untitered\n'
                                                          ' '},
                                     'vtbl': {}}]]},
       {   'file': '/Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/alm-1/data_structure_ANM210861_20130702.nwb',
           'subqueries': [   [   {   'node': '/general',
                                     'vind': {   'virus': '       '
                                                          'infectionCoordinates: '
                                                          '[2.5, -1.5, 0.5],[2.5, '
                                                          '-1.5, 0.85]\n'
                                                          '        '
   ...
   
   Time, user=0.3663, sys=0.0816, total=0.4479
   Starting: ** query_index ** with: general:(virus LIKE "%infectionLocation: M2%")
   dir:/Users/jt/crcns/projects/petr_nwbqe_paper/NwbQueryEngine4
   cmd:python -m nwbindexer.query_index /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/nwb_index.db 'general:(virus LIKE "%infectionLocation: M2%")'
   Opening '/Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/nwb_index.db'
   Found 16 matching files:
   [   {   'file': './alm-1/data_structure_ANM210861_20130701.nwb',
           'subqueries': [   [   {   'node': '/general',
                                     'vind': {   'virus': '       '
                                                          'infectionCoordinates: '
                                                          '[2.5, -1.5, 0.5],[2.5, '
                                                          '-1.5, 0.85]\n'
                                                          '        '
                                                          'infectionLocation: M2\n'
                                                          '        injectionDate: '
                                                          '20130523\n'
                                                          '        '
                                                          'injectionVolume: '
                                                          '30,30\n'
                                                          '        virusID: '
                                                          'Addgene41015\n'
                                                          '        '
                                                          'virusLotNumber: \n'
                                                          '        virusSource: '
                                                          'Janelia core\n'
                                                          '        virusTiter: '
                                                          'untitered\n'
                                                          ' '},
                                     'vtbl': {}}]]},
       {   'file': './alm-1/data_structure_ANM210861_20130702.nwb',
           'subqueries': [   [   {   'node': '/general',
                                     'vind': {   'virus': '       '
                                                          'infectionCoordinates: '
                                                          '[2.5, -1.5, 0.5],[2.5, '
                                                          '-1.5, 0.85]\n'
                                                          '        '
   ...
   
   Time, user=0.3245, sys=0.0770, total=0.4015
   # F
   
   ------- query F -------
   general/optophysiology/*: (excitation_lambda)
   Starting: ** java ** with: general/optophysiology/*: (excitation_lambda)
   dir:/Users/jt/crcns/projects/petr_nwbqe_paper/NwbQueryEngine4
   cmd:java -Djava.library.path=src/main/resources/ -jar target/nwbqueryengine-1.0-SNAPSHOT-jar-with-dependencies.jar /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019 'general/optophysiology/*: (excitation_lambda)'
   Dataset: general/optophysiology/img_pln/excitation_lambda, Value: 930.0, DataStorageName: /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/churchland/mouse1_fni16_150825_001-002-003_ch2-PnevPanResults-170814-191401.nwb
   Dataset: general/optophysiology/img_pln/excitation_lambda, Value: 930.0, DataStorageName: /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/churchland/mouse1_fni16_150826_001_ch2-PnevPanResults-170808-002053.nwb
   Dataset: general/optophysiology/img_pln/excitation_lambda, Value: 930.0, DataStorageName: /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/churchland/mouse1_fni16_150819_001_ch2-PnevPanResults-170815-163235.nwb
   
   ...
   
   Time, user=1.3557, sys=0.1453, total=1.5011
   Starting: ** search_nwb ** with: general/optophysiology/*: (excitation_lambda)
   dir:/Users/jt/crcns/projects/petr_nwbqe_paper/NwbQueryEngine4
   cmd:python -m nwbindexer.search_nwb /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019 'general/optophysiology/*: (excitation_lambda)'
   Found 30 matching files:
   [   {   'file': '/Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/churchland/mouse1_fni16_150817_001_ch2-PnevPanResults-170808-190057.nwb',
           'subqueries': [   [   {   'node': '/general/optophysiology/img_pln',
                                     'vind': {'excitation_lambda': 930.0},
                                     'vtbl': {}}]]},
       {   'file': '/Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/churchland/mouse1_fni16_150818_001_ch2-PnevPanResults-170808-180842.nwb',
           'subqueries': [   [   {   'node': '/general/optophysiology/img_pln',
                                     'vind': {'excitation_lambda': 930.0},
                                     'vtbl': {}}]]},
       {   'file': '/Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/churchland/mouse1_fni16_150819_001_ch2-PnevPanResults-170815-163235.nwb',
           'subqueries': [   [   {   'node': '/general/optophysiology/img_pln',
                                     'vind': {'excitation_lambda': 930.0},
                                     'vtbl': {}}]]},
   ...
   
   Time, user=0.4250, sys=0.0832, total=0.5082
   Starting: ** query_index ** with: general/optophysiology/*: (excitation_lambda)
   dir:/Users/jt/crcns/projects/petr_nwbqe_paper/NwbQueryEngine4
   cmd:python -m nwbindexer.query_index /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/nwb_index.db 'general/optophysiology/*: (excitation_lambda)'
   Opening '/Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/nwb_index.db'
   Found 30 matching files:
   [   {   'file': './churchland/mouse1_fni16_150817_001_ch2-PnevPanResults-170808-190057.nwb',
           'subqueries': [   [   {   'node': '/general/optophysiology/img_pln',
                                     'vind': {'excitation_lambda': 930.0},
                                     'vtbl': {}}]]},
       {   'file': './churchland/mouse1_fni16_150818_001_ch2-PnevPanResults-170808-180842.nwb',
           'subqueries': [   [   {   'node': '/general/optophysiology/img_pln',
                                     'vind': {'excitation_lambda': 930.0},
                                     'vtbl': {}}]]},
       {   'file': './churchland/mouse1_fni16_150819_001_ch2-PnevPanResults-170815-163235.nwb',
           'subqueries': [   [   {   'node': '/general/optophysiology/img_pln',
                                     'vind': {'excitation_lambda': 930.0},
                                     'vtbl': {}}]]},
   
   ...                                  'vtbl': {}}]]}]
   
   Time, user=0.3190, sys=0.0755, total=0.3945
   
   Queries in test:
   A. epochs*:(start_time>200 & stop_time<400 | stop_time>1600)
   B. */data: (unit == "unknown")
   C. general/subject: (subject_id == "anm00210863") & epochs/*: (start_time > 500 & start_time < 550 & tags LIKE "%LickEarly%")
   D. units: (id > -1 & location == "CA3" & quality > 0.8)
   E. general:(virus LIKE "%infectionLocation: M2%")
   F. general/optophysiology/*: (excitation_lambda)
   timing results are:
   qid	java	search_nwb	query_index
   A	13.5819	18.9776	1.6227
   B	43.2085	59.7449	0.9373
   C	13.9528	19.3369	0.4202
   D	1.7858	0.4270	0.3934
   E	1.5565	0.4479	0.4015
   F	1.5011	0.5082	0.3945
   

Final output from another run (demonstrating variations in time required):

.. code-block:: none

   
   qid	java	search_nwb	query_index
   A	12.7872	18.2436		1.5393
   B	30.8791	44.3139		0.5819
   C	13.3315	18.8072		0.3936
   D	1.7891	0.4112		0.3791
   E	1.5198	0.4383		0.3832
   F	1.4483	0.4915		0.3914
   

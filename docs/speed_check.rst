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
   
   Usage: ../nwbindexer/speed_check.py ( i | <ndq> | <query> ) [ <data_dir> [ <java_tool_dir> ] ]
    First parameter required, either:
       'i' - interactive mode (user enters queries interactively).
       <ndq> - an integer that specifies number of times to run default queries.  Times for runs are averaged.
               It's good to use a multiple of six so all possible orders of the three tools are used.
       <query> - a single query to execute; must be quoted.
    After the first parameter, optionally specify:
       <data_dir> - directory containing NWB files AND index file ('nwb_index.db' built by build_index.py)
       <java_tool_dir> - directory containing NWB Query Engine (Java tool)
       If <data_dir> not specified, uses: ../sample_data
       If <java_tool_dir> not specified, uses: /Users/jt/crcns/projects/petr_nwbqe_paper/NwbQueryEngine5
   

The source of the script (file *speed_check.py*) can be edited to change the defaults 
for *<data_dir>* and *<java_tool_dir>*.

An example run of the tool using the <ndq> option and output is shown below.

$ ``time python -m nwbindexer.speed_check 12 ../../sample_data_dec2019/ > speed_check_dec1019_x12.txt``

Terminal output:

.. code-block:: none

   real	 28m59.996s
   user	 29m52.901s
   sys	 1m35.288s


The terminal output (above) shows the time required to run the command.  The output of the command (the speed_check utility)
is stored in file `speed_check_dec1019_x12.txt`.  The program also creates a bar chart showing the average, minimum and maximum
time for each tool on each query.

Partial contents of the output (in file `speed_check_dec1019_x12.txt`) is shown below.   
A line with three dots ( ... )
indicates lines that were removed from the output to reduce the length.  The actual output is over
47,800 lines.  The execution times found can vary between runs due to variations in the system
operation (threads running, memory usage). 


.. code-block:: none

   
   # A
   
   ------- query A -------
   epochs*:(start_time>200 & stop_time<250 | stop_time>4850)
   
   ** Starting run 0, NWB Query Engine with: epochs*:(start_time>200 & stop_time<250 | stop_time>4850)
   dir:/Users/jt/crcns/projects/petr_nwbqe_paper/NwbQueryEngine5
   cmd:java -Djava.library.path=src/main/resources/ -jar target/nwbqueryengine-1.0-SNAPSHOT-jar-with-dependencies.jar /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019 'epochs*:(start_time>200 & stop_time<250 | stop_time>4850)'
   Dataset: epochs/trial_011/start_time, Value: 214.274403, DataStorageName: /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/alm-1/data_structure_ANM210861_20130701.nwb
   Dataset: epochs/trial_010/start_time, Value: 202.908281, DataStorageName: /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/alm-1/data_structure_ANM210861_20130701.nwb
   Dataset: epochs/trial_011/stop_time, Value: 223.430533, DataStorageName: /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/alm-1/data_structure_ANM210861_20130701.nwb
   Dataset: epochs/trial_010/stop_time, Value: 214.274403, DataStorageName: /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/alm-1/data_structure_ANM210861_20130701.nwb
   Dataset: epochs/trial_012/start_time, Value: 223.430533, DataStorageName: /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/alm-1/data_structure_ANM210861_20130701.nwb
   Dataset: epochs/trial_012/stop_time, Value: 243.704452, DataStorageName: /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/alm-1/data_structure_ANM210861_20130701.nwb
   
   
   Time, user=10.9194, sys=0.6361, total=11.5555
   
   ** Starting run 0, search_nwb with: epochs*:(start_time>200 & stop_time<250 | stop_time>4850)
   dir:/Users/jt/crcns/projects/petr_nwbqe_paper/NwbQueryEngine5
   cmd:python -m nwbindexer.search_nwb /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019 'epochs*:(start_time>200 & stop_time<250 | stop_time>4850)'
   Found 12 matching files:
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
                                 {   'node': '/epochs/trial_421',
                                     'vind': {   'start_time': 4843.970217,
                                                 'stop_time': 4853.064514},
   
   ...
   
   # B
   
   ------- query B -------
   */data: (unit == "unknown")
   
   ** Starting run 0, NWB Query Engine with: */data: (unit == "unknown")
   dir:/Users/jt/crcns/projects/petr_nwbqe_paper/NwbQueryEngine5
   cmd:java -Djava.library.path=src/main/resources/ -jar target/nwbqueryengine-1.0-SNAPSHOT-jar-with-dependencies.jar /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019 '*/data: (unit == "unknown")'
   Dataset: acquisition/timeseries/lick_trace/data/unit, Value: unknown, DataStorageName: /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/alm-1/data_structure_ANM210861_20130701.nwb
   Dataset: stimulus/presentation/pole_in/data/unit, Value: unknown, DataStorageName: /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/alm-1/data_structure_ANM210861_20130701.nwb
   Dataset: stimulus/presentation/pole_out/data/unit, Value: unknown, DataStorageName: /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/alm-1/data_structure_ANM210861_20130701.nwb
   
   ...
   
   
   Time, user=1.5189, sys=0.1340, total=1.6529
   
   Queries in test:
   A. epochs*:(start_time>200 & stop_time<250 | stop_time>4850)
   B. */data: (unit == "unknown")
   C. general/subject: (subject_id == "anm00210863") & epochs/*: (start_time > 500 & start_time < 550 & tags LIKE "%LickEarly%")
   D. units: (id > -1 & location == "CA3" & quality > 0.8)
   E. general:(virus LIKE "%infectionLocation: M2%")
   F. general/optophysiology/*: (excitation_lambda)
   timing results are:
   [   [   ['NWB Query Engine', 'search_nwb', 'query_index'],
           [11.555488, 17.664302, 0.6155299999999975],
           [45.217116000000004, 44.385037000000004, 0.7054779999999994],
           [12.862747000000002, 19.03428699999999, 0.40231400000000583],
           [1.7620999999999984, 0.4136630000000068, 0.3810600000000033],
           [1.521589999999998, 0.4339169999999921, 0.3874990000000125],
           [1.4209560000000039, 0.49404699999999657, 0.386863999999985]],
       [   ['NWB Query Engine', 'search_nwb', 'query_index'],
           [11.737016000000013, 17.793285000000004, 0.4799729999999851],
           [31.888129999999997, 44.75922200000001, 0.5863960000000006],
           [14.039116999999987, 19.000447000000015, 0.395937],
           [1.7673079999999999, 0.4048699999999599, 0.38047000000001674],
           [1.6904070000000395, 0.4318000000000133, 0.3855579999999925],
           [1.470128999999961, 0.4930020000000219, 0.3864729999999881]],
       [   ['NWB Query Engine', 'search_nwb', 'query_index'],
           [12.676878000000048, 18.145757999999983, 0.48361699999997754],
           [31.33981099999997, 44.07408400000001, 0.5816910000000064],
           [13.775551999999987, 18.925423000000002, 0.4024800000000326],
           [1.7823600000000255, 0.4207419999999793, 0.3828839999999971],
           [1.5701059999999885, 0.42625499999999406, 0.3870170000000286],
           [1.5202320000000498, 0.4891279999999476, 0.38959299999998365]],
       [   ['NWB Query Engine', 'search_nwb', 'query_index'],
           [13.154039000000019, 17.61850300000001, 0.4761149999999681],
           [34.38398700000007, 45.62109399999998, 0.592054000000001],
           [13.795867000000094, 19.574963999999916, 0.3998979999999932],
           [1.9823880000000074, 0.48766199999996473, 0.44980099999994394],
           [1.68300100000004, 0.5201319999999754, 0.4447070000000579],
           [1.5655020000000093, 0.5649060000000006, 0.44038399999998035]],
       [   ['NWB Query Engine', 'search_nwb', 'query_index'],
           [13.775499000000025, 19.458508000000002, 0.5512669999999389],
           [34.610295000000036, 46.16795499999997, 0.6142990000000097],
           [14.78548800000003, 20.366887999999946, 0.39981099999996417],
           [1.7721429999999572, 0.42912500000007725, 0.3811330000000339],
           [1.5849790000000041, 0.4799619999999649, 0.40381999999999607],
           [1.5102449999999763, 0.5374970000000232, 0.416577999999987]],
       [   ['NWB Query Engine', 'search_nwb', 'query_index'],
           [13.23108299999997, 19.140226000000048, 0.5245360000000119],
           [34.28354699999998, 46.86952999999997, 0.7086280000000258],
           [15.09476900000002, 19.786680999999973, 0.4079040000000518],
           [2.0031289999999586, 0.47979900000000697, 0.4627219999999639],
           [1.7406860000000108, 0.5081309999999419, 0.4648180000000508],
           [1.6099549999999638, 0.5765929999999742, 0.46667700000005397]],
       [   ['NWB Query Engine', 'search_nwb', 'query_index'],
           [14.070656000000021, 19.552270000000064, 0.4836919999999765],
           [34.816873, 47.07685500000003, 0.6190009999999617],
           [14.327312999999997, 20.025065999999967, 0.41651300000006586],
           [1.7532349999999681, 0.43728699999996223, 0.39734900000006945],
           [1.564530000000083, 0.47730599999982815, 0.4233790000000468],
           [1.544811999999915, 0.5613840000001531, 0.44094799999984247]],
       [   ['NWB Query Engine', 'search_nwb', 'query_index'],
           [13.915329000000163, 19.83806400000001, 0.6145769999999686],
           [34.53574500000002, 47.07437999999984, 0.6017320000000197],
           [15.462741000000136, 21.116008000000008, 0.4730059999999696],
           [1.7472179999999327, 0.43963199999992497, 0.4067010000000266],
           [1.5766670000001355, 0.474060999999935, 0.4238430000000477],
           [1.5793789999998609, 0.5844370000001788, 0.4435910000000405]],
       [   ['NWB Query Engine', 'search_nwb', 'query_index'],
           [13.408717000000081, 19.85163299999988, 0.5826869999999928],
           [34.5495710000001, 47.525296999999895, 0.6316689999999312],
           [14.595589999999973, 20.00971199999995, 0.47171000000004426],
           [2.0618829999999235, 0.4822270000001083, 0.463105999999911],
           [1.7316270000000031, 0.5187030000001727, 0.45987299999997333],
           [1.6411280000000374, 0.5823469999999418, 0.4682709999998593]],
       [   ['NWB Query Engine', 'search_nwb', 'query_index'],
           [13.212591999999887, 19.744173000000202, 0.5104959999999039],
           [34.91291799999989, 47.44322600000011, 0.617238000000043],
           [14.653718000000168, 19.772444999999976, 0.4007819999999924],
           [1.998737999999932, 0.4906129999998683, 0.4551790000000864],
           [1.7566449999999634, 0.5153410000001202, 0.4601289999998954],
           [1.6417740000001402, 0.5886680000000837, 0.4555999999998903]],
       [   ['NWB Query Engine', 'search_nwb', 'query_index'],
           [14.25105400000001, 19.579493, 0.5792170000000425],
           [35.00160600000008, 47.04914199999983, 0.594908999999916],
           [14.398289999999918, 20.39642399999991, 0.4000700000001274],
           [1.7732929999999385, 0.43341399999994223, 0.38483000000017853],
           [1.5396449999999504, 0.4768230000000955, 0.39817100000001915],
           [1.5797109999998753, 0.5593440000000243, 0.4196660000000776]],
       [   ['NWB Query Engine', 'search_nwb', 'query_index'],
           [13.255340999999888, 19.34880400000003, 0.5536300000000267],
           [34.602333000000115, 47.16575299999995, 0.7093430000000325],
           [14.67361200000019, 19.81225499999981, 0.4029790000000588],
           [2.0453129999998225, 0.4956770000001569, 0.4530679999998455],
           [1.7797189999998153, 0.5198910000000865, 0.4628060000001142],
           [1.652906999999999, 0.5844759999998104, 0.46387700000015286]]]
   tool: NWB Query Engine
   time_ave: [13.186974333333344, 35.01182766666668, 14.372067000000044, 1.8707589999999552, 1.644966833333336, 1.5613941666666493]
   time_min: [11.555488, 31.33981099999997, 12.862747000000002, 1.7472179999999327, 1.521589999999998, 1.4209560000000039]
   time_max: [14.25105400000001, 45.217116000000004, 15.462741000000136, 2.0618829999999235, 1.7797189999998153, 1.652906999999999]
   tool: search_nwb
   time_ave: [18.977918250000016, 46.267631249999965, 19.81838333333329, 0.4512259166666632, 0.48186016666667664, 0.5513190833333463]
   time_min: [17.61850300000001, 44.07408400000001, 18.925423000000002, 0.4048699999999599, 0.42625499999999406, 0.4891279999999476]
   time_max: [19.85163299999988, 47.525296999999895, 21.116008000000008, 0.4956770000001569, 0.5201319999999754, 0.5886680000000837]
   tool: query_index
   time_ave: [0.5379447499999825, 0.6302031666666622, 0.41445033333335884, 0.41652525000000634, 0.4251350000000196, 0.43154349999998676]
   time_min: [0.4761149999999681, 0.5816910000000064, 0.395937, 0.38047000000001674, 0.3855579999999925, 0.3864729999999881]
   time_max: [0.6155299999999975, 0.7093430000000325, 0.4730059999999696, 0.463105999999911, 0.4648180000000508, 0.4682709999998593]
   


In addition to the above output, the speed_check.py program also generates a bar chart showing the
average time required for each tool to perform each query.  Superimposed on the top of each bar is
a vertical line which shows the minimum and maximum times required for the tool to run the query.

The bar chart generated from the above run is shown below.


.. image:: _static/images/speedcheck_figure_2020-01-30_161647.pdf


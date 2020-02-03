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
   ...
   
   Time, user=11.6178, sys=0.7059, total=12.3236
   
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
   
   ...
   
   Time, user=17.2793, sys=0.5086, total=17.7879
   
   ** Starting run 0, nwbindexer with: epochs*:(start_time>200 & stop_time<250 | stop_time>4850)
   dir:/Users/jt/crcns/projects/petr_nwbqe_paper/NwbQueryEngine5
   cmd:python -m nwbindexer.query_index /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/nwb_index.db 'epochs*:(start_time>200 & stop_time<250 | stop_time>4850)'
   Opening '/Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/nwb_index.db'
   Found 12 matching files:
   [   {   'file': './alm-1/data_structure_ANM210861_20130701.nwb',
           'subqueries': [   [   {   'node': '/epochs/trial_010',
                                     'vind': {   'start_time': 202.908281,
                                                 'stop_time': 214.274403},
                                     'vtbl': {}},
                                 {   'node': '/epochs/trial_011',
                                     'vind': {   'start_time': 214.274403,
                                                 'stop_time': 223.430533},
                                     'vtbl': {}},
   ...
   
   Time, user=0.4064, sys=0.0699, total=0.4763
   # B
   
   ------- query B -------
   */data: (unit == "unknown")
   
   ** Starting run 0, NWB Query Engine with: */data: (unit == "unknown")
   dir:/Users/jt/crcns/projects/petr_nwbqe_paper/NwbQueryEngine5
   cmd:java -Djava.library.path=src/main/resources/ -jar target/nwbqueryengine-1.0-SNAPSHOT-jar-with-dependencies.jar /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019 '*/data: (unit == "unknown")'
   Dataset: acquisition/timeseries/lick_trace/data/unit, Value: unknown, DataStorageName: /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/alm-1/data_structure_ANM210861_20130701.nwb
   ...
   
   Time, user=30.6447, sys=1.8166, total=32.4613
   
   ** Starting run 0, search_nwb with: */data: (unit == "unknown")
   dir:/Users/jt/crcns/projects/petr_nwbqe_paper/NwbQueryEngine5
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
   ...
   
   Time, user=42.6341, sys=1.6830, total=44.3171
   
   
   ...
   
   Dataset: general/optophysiology/imaging_plane/excitation_lambda, Value: 910.0, DataStorageName: /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/tutorials/domain/brain_observatory.nwb
   Dataset: general/optophysiology/my_imgpln/excitation_lambda, Value: 600.0, DataStorageName: /Users/jt/crcns/projects/petr_nwbqe_paper/sample_data_dec2019/tutorials/domain/ophys_example.nwb
   
   Time, user=1.5345, sys=0.1322, total=1.6667
   
   Queries in test:
   A. epochs*:(start_time>200 & stop_time<250 | stop_time>4850)
   B. */data: (unit == "unknown")
   C. general/subject: (subject_id == "anm00210863") & epochs/*: (start_time > 500 & start_time < 550 & tags LIKE "%LickEarly%")
   D. units: (id > -1 & location == "CA3" & quality > 0.8)
   E. general:(virus LIKE "%infectionLocation: M2%")
   F. general/optophysiology/*: (excitation_lambda)
   timing results are:
   [   [   ['NWB Query Engine', 'search_nwb', 'nwbindexer'],
           [12.323649999999999, 17.78795, 0.4762710000000021],
           [32.461324, 44.317103, 0.5755010000000045],
           [13.388241999999995, 18.805749000000002, 0.38864600000001115],
           [1.7776289999999744, 0.40620900000002624, 0.3828319999999854],
           [1.5525489999999929, 0.4276980000000199, 0.3758489999999952],
           [1.4789959999999809, 0.49392600000000186, 0.38840800000002407]],
       [   ['NWB Query Engine', 'search_nwb', 'nwbindexer'],
           [11.951703999999975, 17.684409000000002, 0.4850340000000246],
           [33.06460499999998, 44.871867000000016, 0.5884969999999967],
           [13.00898899999999, 18.879096999999987, 0.39565400000001283],
           [1.8240300000000254, 0.40825000000000244, 0.3842249999999545],
           [1.523098000000008, 0.4308119999999853, 0.3792180000000105],
           [1.4620449999999927, 0.48747699999997707, 0.3942920000000534]],
       [   ['NWB Query Engine', 'search_nwb', 'nwbindexer'],
           [12.292634999999988, 17.71122100000002, 0.4931979999999925],
           [31.715346000000025, 44.269245999999974, 0.5827180000000176],
           [13.615158999999991, 18.62413699999996, 0.400113000000033],
           [1.77765100000002, 0.3981279999999856, 0.3793939999999729],
           [1.5594440000000311, 0.42230299999999943, 0.3798599999999581],
           [1.4684130000000266, 0.48533700000000124, 0.383213000000012]],
       [   ['NWB Query Engine', 'search_nwb', 'nwbindexer'],
           [12.56530700000004, 17.789719999999985, 0.4703429999999891],
           [31.675452000000043, 44.14379199999996, 0.5683930000000146],
           [13.648998000000073, 18.566490999999914, 0.38886699999999763],
           [1.7804190000000304, 0.40790099999992435, 0.38032800000005196],
           [1.55089499999999, 0.4261669999999782, 0.3787000000000198],
           [1.4687469999999614, 0.49429700000000665, 0.39292099999995145]],
       [   ['NWB Query Engine', 'search_nwb', 'nwbindexer'],
           [12.537729000000027, 17.740118999999975, 0.48057100000004027],
           [30.873830999999957, 44.026783000000066, 0.5713640000000311],
           [13.659739000000002, 18.732270999999955, 0.3886049999999628],
           [1.732225999999919, 0.4136850000000223, 0.3754670000000644],
           [1.5275830000000497, 0.42749299999999124, 0.37764900000000523],
           [1.4371710000000277, 0.49300199999998995, 0.37664699999994866]],
       [   ['NWB Query Engine', 'search_nwb', 'nwbindexer'],
           [12.065124000000033, 17.71671100000001, 0.473039],
           [34.59439099999999, 44.41940400000001, 0.5749450000000067],
           [14.824584000000094, 20.070431999999975, 0.4134939999999574],
           [2.0133959999999576, 0.49045400000002815, 0.4563129999999589],
           [1.7613109999999637, 0.5116970000000407, 0.45816899999998384],
           [1.6201010000000338, 0.5919250000000389, 0.4557319999999905]],
       [   ['NWB Query Engine', 'search_nwb', 'nwbindexer'],
           [13.863780999999896, 20.10773000000004, 0.4887419999999736],
           [34.575612000000014, 48.08052500000007, 0.6126809999999523],
           [14.748455999999948, 21.717973000000015, 0.4133940000000962],
           [1.8125289999999268, 0.4475129999999936, 0.4192520000000499],
           [1.6164730000000205, 0.4934969999999623, 0.4398180000000451],
           [1.6412199999999615, 0.578479999999999, 0.46646600000001825]],
       [   ['NWB Query Engine', 'search_nwb', 'nwbindexer'],
           [14.183431999999925, 19.463961999999952, 0.5685050000000729],
           [33.69680699999992, 46.44652799999985, 0.5893350000001405],
           [13.886630000000025, 19.663959999999953, 0.4755180000001431],
           [1.7565279999999603, 0.41089800000007415, 0.390275999999929],
           [1.5056289999999493, 0.4478090000000705, 0.40615499999995563],
           [1.4745139999999282, 0.5386419999998964, 0.4159240000001958]],
       [   ['NWB Query Engine', 'search_nwb', 'nwbindexer'],
           [13.39936200000016, 18.57474999999993, 0.5622109999999694],
           [33.46206100000019, 46.73720199999987, 0.5941449999999762],
           [14.150975000000066, 19.905867999999963, 0.46484499999986184],
           [1.987123999999838, 0.48372400000012306, 0.4484090000000194],
           [1.7172100000001436, 0.5058690000000183, 0.4525939999999835],
           [1.6099890000000698, 0.573598999999831, 0.4544750000000448]],
       [   ['NWB Query Engine', 'search_nwb', 'nwbindexer'],
           [13.135035000000023, 18.866990999999928, 0.5028779999999742],
           [34.27441100000003, 48.12650700000013, 0.5868599999999731],
           [14.724086999999983, 19.623490999999817, 0.40979000000018573],
           [1.9606950000000296, 0.4782629999999557, 0.44371199999993394],
           [1.705235000000016, 0.5093840000000824, 0.446410999999884],
           [1.648959000000076, 0.582082999999912, 0.4529080000000647]],
       [   ['NWB Query Engine', 'search_nwb', 'nwbindexer'],
           [13.732621999999807, 19.141613000000206, 0.5681570000000562],
           [34.59157899999997, 46.49771199999998, 0.613060999999874],
           [14.279798999999983, 20.263692999999975, 0.40834800000018845],
           [1.6990480000000048, 0.42399300000012374, 0.3962589999999011],
           [1.5614639999999724, 0.46319500000002733, 0.399421999999916],
           [1.5296450000001016, 0.5506969999998432, 0.41318099999999447]],
       [   ['NWB Query Engine', 'search_nwb', 'nwbindexer'],
           [13.533899999999988, 19.061607000000024, 0.5465729999999951],
           [35.23903399999986, 47.30263100000009, 0.6926130000000512],
           [14.941060999999976, 19.97429000000018, 0.4123069999999416],
           [2.001859000000195, 0.47430499999980213, 0.44398300000004554],
           [1.7040489999999409, 0.507457000000116, 0.448450999999892],
           [1.6666550000001905, 0.5813069999999954, 0.452112999999855]]]
   tool: NWB Query Engine
   time_ave: [12.96535674999999, 33.352037749999994, 14.07305991666668, 1.84359449999999, 1.6070783333333398, 1.5422045833333626]
   time_min: [11.951703999999975, 30.873830999999957, 13.00898899999999, 1.6990480000000048, 1.5056289999999493, 1.4371710000000277]
   time_max: [14.183431999999925, 35.23903399999986, 14.941060999999976, 2.0133959999999576, 1.7613109999999637, 1.6666550000001905]
   tool: search_nwb
   time_ave: [18.470565250000007, 45.76994166666666, 19.56895433333331, 0.43694358333333844, 0.46444841666669096, 0.537564333333291]
   time_min: [17.684409000000002, 44.026783000000066, 18.566490999999914, 0.3981279999999856, 0.42230299999999943, 0.48533700000000124]
   time_max: [20.10773000000004, 48.12650700000013, 21.717973000000015, 0.49045400000002815, 0.5116970000000407, 0.5919250000000389]
   tool: nwbindexer
   time_ave: [0.5096268333333408, 0.5958427500000032, 0.4132984166666993, 0.40837083333332225, 0.41185799999997075, 0.42052333333334607]
   time_min: [0.4703429999999891, 0.5683930000000146, 0.3886049999999628, 0.3754670000000644, 0.3758489999999952, 0.37664699999994866]
   time_max: [0.5685050000000729, 0.6926130000000512, 0.4755180000001431, 0.4563129999999589, 0.45816899999998384, 0.46646600000001825]
   

In addition to the above output, the speed_check.py program also generates a bar chart showing the
average time required for each tool to perform each query.  Superimposed on the top of each bar is
a vertical line which shows the minimum and maximum times required for the tool to run the query.

The bar chart generated from the above run is shown below.


.. image:: _static/images/speedcheck_figure_2020-02-01_181421.pdf




.. index::
   single: Multiple subquery examples


Multiple subquery examples
==========================

Queries can be created by combining multiple subqueries.  Some examples along with the output are shown
in this section.  The datasets (nwb files) used in the examples are:

* The first 16 files in the alm-1 data set at CRCNS.org
  (http://crcns.org/data-sets/motor-cortex/alm-1), which contains
  anterior motor cortex recordings from the Svoboda Lab at Janelia Farm.
  The total size of these data files is (2.2 GB).

* NWB-formatted dataset from Steinmetz et al. Nature 2019.  Available at:
  https://figshare.com/articles/Datasets_from_Steinmetz_et_al_2019_in_NWB_format/11274968
  File: Steinmetz2019_Forssmann_2017-11-05.nwb (267.96 MB)

In the sample queries (done with the query_index.py utility) the index file (*nwb_index.db*) is located in
the `../../sample_data`` directory).  The output would be the same if the *search_nwb.py* utility is
used if a directory containing the nwb files was specified as the *<path>* in the *search_nwb* 
command as described in section :ref:`search_nwb_usage`.  The format of the output is
as described in section :ref:`format_of_query_output`.


Query:

.. code-block:: none

   $ python -m nwbindexer.query_index ../../sample_data '/general/subject: (age LIKE "%3 months 16 days%" & species LIKE "%Mus musculu%") & /:file_create_date LIKE "%2017-04%" & /epochs/* : start_time < 15'


Output is:

.. code-block:: none

   Using index_path: '../../sample_data/nwb_index.db'
   Opening '../../sample_data/nwb_index.db'
   Found 2 matching files:
   [   {   'file': './nwb1/data_structure_ANM210862_20130627.nwb',
           'subqueries': [   [   {   'node': '/general/subject',
                                     'vind': {   'age': '3 months 16 days  weeks',
                                                 'species': 'Mus musculus'},
                                     'vtbl': {}}],
                             [   {   'node': '/',
                                     'vind': {   'file_create_date': '2017-04-24T11:32:54.215883'},
                                     'vtbl': {}}],
                             [   {   'node': '/epochs/trial_001',
                                     'vind': {'start_time': 2.284463},
                                     'vtbl': {}}]]},
       {   'file': './nwb1/data_structure_ANM210863_20130627.nwb',
           'subqueries': [   [   {   'node': '/general/subject',
                                     'vind': {   'age': '3 months 16 days  weeks',
                                                 'species': 'Mus musculus'},
                                     'vtbl': {}}],
                             [   {   'node': '/',
                                     'vind': {   'file_create_date': '2017-04-24T11:32:54.076284'},
                                     'vtbl': {}}],
                             [   {   'node': '/epochs/trial_001',
                                     'vind': {'start_time': 2.222392},
                                     'vtbl': {}}]]}]




Query:

.. code-block:: none

   python -m nwbindexer.query_index ../../sample_data 'intervals/trials: id, visual_stimulus_time, visual_stimulus_left_contrast == 0.25 & visual_stimulus_right_contrast == 0.25'


Output:

.. code-block:: none

   Using index_path: '../../sample_data/nwb_index.db'
   Opening '../../sample_data/nwb_index.db'
   Found 1 matching files:
   [   {   'file': './steinmentz2019/Steinmetz2019_Forssmann_2017-11-05.nwb',
           'subqueries': [   [   {   'node': '/intervals/trials',
                                     'vind': {},
                                     'vtbl': {   'child_names': [   'id',
                                                                    'visual_stimulus_time',
                                                                    'visual_stimulus_left_contrast',
                                                                    'visual_stimulus_right_contrast'],
                                                 'combined': [   {   'id': 95,
                                                                     'visual_stimulus_left_contrast': 0.25,
                                                                     'visual_stimulus_right_contrast': 0.25,
                                                                     'visual_stimulus_time': 468.198},
                                                                 {   'id': 150,
                                                                     'visual_stimulus_left_contrast': 0.25,
                                                                     'visual_stimulus_right_contrast': 0.25,
                                                                     'visual_stimulus_time': 697.717}],
                                                 'row_values': [   (   95,
                                                                       468.198,
                                                                       0.25,
                                                                       0.25),
                                                                   (   150,
                                                                       697.717,
                                                                       0.25,
                                                                       0.25)]}}]]}]


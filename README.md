# nwbindexer
Creates an sqlite index of metadata in a collection of NWB (HDF5) files files.  Also allows searching the
files using a query syntax similar to that used in the NWB Query Engine.
These tools were developed for searching within NWB files.

## Requirements:
Python 3.6
(Tested with anaconda Python 3.6; might work with other versions too).

## Usage:

### 1) Build the index.

First, build the index by running:

`python build_index.py <directory>`

where:
`<directory>` is a directory containing nwb files (extension ".nwb).

This should scan all the nwb files in the directory and save the
information about the small datasets and attributes in an SQLite3 database.
Name of the database file will be "nwb_index.db".


### 2) Running queries.

Queries can be run by running:

`python run_query.py  [ <index_file> ]`

Where the optional `<index_file>` is the name of a SQLite3 databaes created in
step 1.  (Default is "nwb_index.db").


Queries are entered using the format described in the NWB Query Engine paper, except that:
* ":" is used instead of "=", and the parentheses are not required.  (I call the location before the ":", the "parent location").
* The parent location and ":" can be left off, which is the same as parent location == "*" (search entire tree).
* String constants must always be enclosed in either single or doulble quotes.
* Any string constant used with LIKE must have wildcards ("%" or "_") explicitly included (if no wildcards are included, the query does an exact match).
* The expression on the right must always have a relational operator.  Just giving the child location (e.g. `epochs:(start_time)`) is currently not allowed.

* Currently the queries only work for dataset values, not for any attributes (of groups or datasets).
The database schema (given in file "build_index.py" might need to be changed to have queries search 
both groups and datasets.  Or there might need to be a way to specify explicitly whether the
child value being searched for is a group attribute, dataset attribute or dataset value.

#### Example queries (Datasets):
(Using same datasets at the NWB Query Engine test site: http://eeg.kiv.zcu.cz:8080/nwb-query-engine-web/)

`/:session_start_time LIKE "%Jun __ 2013%"`

Output:
```
Found 6:
1. ('../sample_data/data_structure_ANM210862_20130627.nwb', '', 'session_start_time', 'Thu Jun 27 2013 10:36:32')
2. ('../sample_data/data_structure_ANM210862_20130626.nwb', '', 'session_start_time', 'Wed Jun 26 2013 10:44:32')
3. ('../sample_data/data_structure_ANM210863_20130626.nwb', '', 'session_start_time', 'Wed Jun 26 2013 12:23:37')
4. ('../sample_data/data_structure_ANM210863_20130627.nwb', '', 'session_start_time', 'Thu Jun 27 2013 12:15:14')
5. ('../sample_data/data_structure_ANM210863_20130628.nwb', '', 'session_start_time', 'Fri Jun 28 2013 16:24:15')
6. ('../sample_data/data_structure_ANM210862_20130628.nwb', '', 'session_start_time', 'Fri Jun 28 2013 14:58:30')
```

`epochs:(start_time>200 & stop_time<210)`

Output:
```
Found 2:
1. ('../sample_data/data_structure_ANM214429_20130807.nwb', 'epochs/trial_015', 'start_time', 200.719654, 'stop_time', 208.157124)
2. ('../sample_data/data_structure_ANM214429_20130806.nwb', 'epochs/trial_268', 'start_time', 3317.152814, 'stop_time', 2.683177)```
```

`/:file_create_date LIKE "%"`

Output:
```
Found 16:
1. ('../sample_data/data_structure_ANM210861_20130701.nwb', '', 'file_create_date', '2017-04-24T11:32:54.281831')
2. ('../sample_data/data_structure_ANM210861_20130702.nwb', '', 'file_create_date', '2017-04-24T11:32:54.225763')
3. ('../sample_data/data_structure_ANM210861_20130703.nwb', '', 'file_create_date', '2017-04-24T11:32:53.889109')
4. ('../sample_data/data_structure_ANM214427_20130805.nwb', '', 'file_create_date', '2017-04-24T11:32:55.180281')
5. ('../sample_data/data_structure_ANM214427_20130807.nwb', '', 'file_create_date', '2017-04-24T11:32:54.249098')
6. ('../sample_data/data_structure_ANM210862_20130627.nwb', '', 'file_create_date', '2017-04-24T11:32:54.215883')
7. ('../sample_data/data_structure_ANM210862_20130626.nwb', '', 'file_create_date', '2017-04-24T11:32:54.063820')
8. ('../sample_data/data_structure_ANM214427_20130806.nwb', '', 'file_create_date', '2017-04-24T11:32:54.223924')
9. ('../sample_data/data_structure_ANM210863_20130626.nwb', '', 'file_create_date', '2017-04-24T11:32:54.216323')
10. ('../sample_data/data_structure_ANM210863_20130627.nwb', '', 'file_create_date', '2017-04-24T11:32:54.076284')
11. ('../sample_data/data_structure_ANM210863_20130628.nwb', '', 'file_create_date', '2017-04-24T11:32:54.170602')
12. ('../sample_data/data_structure_ANM214427_20130808.nwb', '', 'file_create_date', '2017-04-24T11:32:55.170812')
13. ('../sample_data/data_structure_ANM210862_20130628.nwb', '', 'file_create_date', '2017-04-24T11:32:54.170415')
14. ('../sample_data/data_structure_ANM214429_20130807.nwb', '', 'file_create_date', '2017-04-24T11:32:55.515740')
15. ('../sample_data/data_structure_ANM214429_20130806.nwb', '', 'file_create_date', '2017-04-24T11:32:54.174653')
16. ('../sample_data/data_structure_ANM214429_20130805.nwb', '', 'file_create_date', '2017-04-24T11:32:55.174861')
```

`/general/subject/: (age LIKE "%3 months 16 days%" & species LIKE "%Mus musculu%") & /:file_create_date LIKE "%2017-04%" & /epochs : start_time < 150`

(This is equivalant to the following query in the NWB Query Engine):

`/general/subject/= (age LIKE "3 months 16 days" & species LIKE "Mus musculu") & /=(file_create_date LIKE "2017-04") & /epochs=(start_time < 150)`

Output:
```
Found 2:
1. ('../sample_data/data_structure_ANM210862_20130627.nwb', 'general/subject', 'age', '3 months 16 days  weeks', 'species', 'Mus musculus', '', 'file_create_date', '2017-04-24T11:32:54.215883', 'epochs/trial_001', 'start_time', 2.284463)
2. ('../sample_data/data_structure_ANM210863_20130627.nwb', 'general/subject', 'age', '3 months 16 days  weeks', 'species', 'Mus musculus', '', 'file_create_date', '2017-04-24T11:32:54.076284', 'epochs/trial_001', 'start_time', 2.222392)
```

`/general/subject/: (age LIKE "3 months 16 days%" & species LIKE "Mus musculus") & /:session_start_time < "Thu Jun 27 2013 12" & /epochs : start_time < 250`

Output:
```
Found 1:
1. ('../sample_data/data_structure_ANM210862_20130627.nwb', 'general/subject', 'age', '3 months 16 days  weeks', 'species', 'Mus musculus', '', 'session_start_time', 'Thu Jun 27 2013 10:36:32', 'epochs/trial_001', 'start_time', 2.284463)
```

#### Example queries (Attributes)

`/acquisition/timeseries:neurodata_type LIKE "TimeSeries"`

Output (two are pynwb sample files):
```
Found 18:
1. ('../sample_data/data_structure_ANM210861_20130701.nwb', 'acquisition/timeseries/lick_trace', 'acquisition/timeseries/lick_trace/neurodata_type', 'TimeSeries')
2. ('../sample_data/data_structure_ANM210861_20130702.nwb', 'acquisition/timeseries/lick_trace', 'acquisition/timeseries/lick_trace/neurodata_type', 'TimeSeries')
3. ('../sample_data/data_structure_ANM210861_20130703.nwb', 'acquisition/timeseries/lick_trace', 'acquisition/timeseries/lick_trace/neurodata_type', 'TimeSeries')
4. ('../sample_data/data_structure_ANM214427_20130805.nwb', 'acquisition/timeseries/lick_trace', 'acquisition/timeseries/lick_trace/neurodata_type', 'TimeSeries')
5. ('../sample_data/data_structure_ANM214427_20130807.nwb', 'acquisition/timeseries/lick_trace', 'acquisition/timeseries/lick_trace/neurodata_type', 'TimeSeries')
6. ('../sample_data/data_structure_ANM210862_20130627.nwb', 'acquisition/timeseries/lick_trace', 'acquisition/timeseries/lick_trace/neurodata_type', 'TimeSeries')
7. ('../sample_data/data_structure_ANM210862_20130626.nwb', 'acquisition/timeseries/lick_trace', 'acquisition/timeseries/lick_trace/neurodata_type', 'TimeSeries')
8. ('../sample_data/data_structure_ANM214427_20130806.nwb', 'acquisition/timeseries/lick_trace', 'acquisition/timeseries/lick_trace/neurodata_type', 'TimeSeries')
9. ('../sample_data/data_structure_ANM210863_20130626.nwb', 'acquisition/timeseries/lick_trace', 'acquisition/timeseries/lick_trace/neurodata_type', 'TimeSeries')
10. ('../sample_data/data_structure_ANM210863_20130627.nwb', 'acquisition/timeseries/lick_trace', 'acquisition/timeseries/lick_trace/neurodata_type', 'TimeSeries')
11. ('../sample_data/data_structure_ANM210863_20130628.nwb', 'acquisition/timeseries/lick_trace', 'acquisition/timeseries/lick_trace/neurodata_type', 'TimeSeries')
12. ('../sample_data/data_structure_ANM214427_20130808.nwb', 'acquisition/timeseries/lick_trace', 'acquisition/timeseries/lick_trace/neurodata_type', 'TimeSeries')
13. ('../sample_data/data_structure_ANM210862_20130628.nwb', 'acquisition/timeseries/lick_trace', 'acquisition/timeseries/lick_trace/neurodata_type', 'TimeSeries')
14. ('../sample_data/data_structure_ANM214429_20130807.nwb', 'acquisition/timeseries/lick_trace', 'acquisition/timeseries/lick_trace/neurodata_type', 'TimeSeries')
15. ('../sample_data/data_structure_ANM214429_20130806.nwb', 'acquisition/timeseries/lick_trace', 'acquisition/timeseries/lick_trace/neurodata_type', 'TimeSeries')
16. ('../sample_data/data_structure_ANM214429_20130805.nwb', 'acquisition/timeseries/lick_trace', 'acquisition/timeseries/lick_trace/neurodata_type', 'TimeSeries')
17. ('../pynwb_examples/tutorials_python/domain/ophys_experiment_data_orig/562095852.nwb', 'acquisition/timeseries/2p_image_series', 'acquisition/timeseries/2p_image_series/neurodata_type', 'TimeSeries')
18. ('../pynwb_examples/tutorials_python/domain/ophys_experiment_data/562095852.nwb', 'acquisition/timeseries/2p_image_series', 'acquisition/timeseries/2p_image_series/neurodata_type', 'TimeSeries')
```

`/processing:neurodata_type LIKE "ROIResponseSeries"`

Output (pynwb sample files):
```
Found 2:
1. ('../pynwb_examples/tutorials_python/domain/brain_observatory.nwb', 'processing/ophys_module/dff_interface/df_over_f', 'processing/ophys_module/dff_interface/df_over_f/neurodata_type', 'RoiResponseSeries')
2. ('../pynwb_examples/tutorials_python/domain/ophys_example.nwb', 'processing/my_ca_imaging_module/Fluorescence/my_rrs', 'processing/my_ca_imaging_module/Fluorescence/my_rrs/neurodata_type', 'RoiResponseSeries')
```

# search_nwb2.py

#### Example queries (NWB 1.0x files):

```
> /general/subject:age LIKE "3 months 16 days%" & /epochs/*: start_time < 250
file ../sample_data/data_structure_ANM210862_20130627.nwb:
[   [   {   'node': '/general/subject',
            'vind': [['age', b'3 months 16 days  weeks']],
            'vrow': []}],
    [   {   'node': '/epochs/trial_001',
            'vind': [['start_time', 2.284463]],
            'vrow': []}]]
file ../sample_data/data_structure_ANM210863_20130627.nwb:
[   [   {   'node': '/general/subject',
            'vind': [['age', b'3 months 16 days  weeks']],
            'vrow': []}],
    [   {   'node': '/epochs/trial_001',
            'vind': [['start_time', 2.222392]],
            'vrow': []},
        {   'node': '/epochs/trial_002',
            'vind': [['start_time', 225.421499]],
            'vrow': []},
        {   'node': '/epochs/trial_003',
            'vind': [['start_time', 234.211464]],
            'vrow': []},
        {   'node': '/epochs/trial_004',
            'vind': [['start_time', 243.062595]],
            'vrow': []}]]
> /general/subject/: (age LIKE "%3 months 16 days%" & species LIKE "%Mus musculu%") & /:file_create_date LIKE "%2017-04%" & /epochs : start_time < 150
> /general/subject/: (age LIKE "%3 months 16 days%" & species LIKE "%Mus musculu%") & /:file_create_date LIKE "%2017-04%" & /epochs/* : start_time < 150
file ../sample_data/data_structure_ANM210862_20130627.nwb:
[   [   {   'node': '/general/subject',
            'vind': [   ['age', b'3 months 16 days  weeks'],
                        ['species', b'Mus musculus']],
            'vrow': []}],
    [   {   'node': '/',
            'vind': [['file_create_date', b'2017-04-24T11:32:54.215883']],
            'vrow': []}],
    [   {   'node': '/epochs/trial_001',
            'vind': [['start_time', 2.284463]],
            'vrow': []}]]
file ../sample_data/data_structure_ANM210863_20130627.nwb:
[   [   {   'node': '/general/subject',
            'vind': [   ['age', b'3 months 16 days  weeks'],
                        ['species', b'Mus musculus']],
            'vrow': []}],
    [   {   'node': '/',
            'vind': [['file_create_date', b'2017-04-24T11:32:54.076284']],
            'vrow': []}],
    [   {   'node': '/epochs/trial_001',
            'vind': [['start_time', 2.222392]],
            'vrow': []}]]
```


#### Example queries (NWB 2.x files):


```
Jeffs-MacBook:nwbindexer jt$ python search_nwb2.py -
Using default path: '../pynwb_examples/tutorials_python/general/basic_example.nwb'
Enter query, control-d to quit
> units: id, location, quality > 0.93
file ../pynwb_examples/tutorials_python/general/basic_example.nwb:
[   [   {   'node': '/units',
            'vind': [],
            'vrow': [[['id', 'location', 'quality'], (1, 'CA1', 0.95)]]}]]
> intervals/epochs: id, start_time, stop_time, timeseries[timeseries], tags LIKE "fir%"
child=timeseries[timeseries], after indexed vals=[['/acquisition/test_timeseries', '/processing/added_mod/ts_for_mod'], ['/acquisition/test_timeseries', '/processing/added_mod/ts_for_mod']]
child=tags, after indexed vals=[['first', 'example'], ['second', 'example']]
file ../pynwb_examples/tutorials_python/general/basic_example.nwb:
[   [   {   'node': '/intervals/epochs',
            'vind': [],
            'vrow': [   [   [   'id',
                                'start_time',
                                'stop_time',
                                'timeseries[timeseries]',
                                'tags'],
                            (   0,
                                2.0,
                                4.0,
                                [   '/acquisition/test_timeseries',
                                    '/processing/added_mod/ts_for_mod'],
                                ['first', 'example'])]]}]]
> /units: id, obs_intervals[0], obs_intervals[1], quality, location LIKE "CA1"
file ../pynwb_examples/tutorials_python/general/basic_example.nwb:
[   [   {   'node': '/units',
            'vind': [],
            'vrow': [   [   [   'id',
                                'obs_intervals[0]',
                                'obs_intervals[1]',
                                'quality',
                                'location'],
                            (1, [1.0], [10.0], 0.95, 'CA1'),
                            (3, [1.0, 20.0], [10.0, 30.0], 0.9, 'CA1')]]}]]
> /units: id, obs_intervals[0], obs_intervals[1], quality, neurodata_type LIKE "units" & location LIKE "CA1"
> /units: id, obs_intervals[0], obs_intervals[1], quality, neurodata_type LIKE "Units" & location LIKE "CA1"
file ../pynwb_examples/tutorials_python/general/basic_example.nwb:
[   [   {   'node': '/units',
            'vind': [['neurodata_type', 'Units']],
            'vrow': [   [   [   'id',
                                'obs_intervals[0]',
                                'obs_intervals[1]',
                                'quality',
                                'location'],
                            (1, [1.0], [10.0], 0.95, 'CA1'),
                            (3, [1.0, 20.0], [10.0, 30.0], 0.9, 'CA1')]]}]]
> 
$ python search_nwb2.py -
Using default path: '../pynwb_examples/tutorials_python/general/basic_example.nwb'
Enter query, control-d to quit
> */epochs: id, neurodata_type, start_time > 2
file ../pynwb_examples/tutorials_python/general/basic_example.nwb:
[   [   {   'node': '/intervals/epochs',
            'vind': [['neurodata_type', 'TimeIntervals']],
            'vrow': [[['id', 'start_time'], (1, 6.0)]]}]]
> *: id, neurodata_type, start_time > 2
file ../pynwb_examples/tutorials_python/general/basic_example.nwb:
[   [   {   'node': '/intervals/epochs',
            'vind': [['neurodata_type', 'TimeIntervals']],
            'vrow': [[['id', 'start_time'], (1, 6.0)]]},
        {   'node': '/intervals/trials',
            'vind': [['neurodata_type', 'TimeIntervals']],
            'vrow': [[['id', 'start_time'], (1, 3.0), (2, 6.0)]]}]]
>
```

.. _query_format:

Query Format
------------

Queries are specified using the following format (BNF Grammar):::


    ⟨query⟩ ::= ⟨subquery⟩ ( ⟨andor⟩ ⟨subquery⟩ )*
    ⟨subquery⟩ ::= ⟨parent⟩ ‘:’ ( <rhs> | '(' <rhs> ')' )
    <rhs> ::= ( <child_list> <expression> | <child_list> | <expression> )
    <child_list> ::= <child> ( [ ',' ] <child> )* [ ',' ]
    <expression> ::= ⟨expression⟩ ⟨andor⟩ ⟨expression⟩ | ‘(’ ⟨expression⟩ ‘)’
                     | ⟨child⟩ ⟨relop⟩ ⟨constant⟩
                     | ⟨child⟩ 'LIKE' ⟨string⟩ | ⟨child⟩
    ⟨relop⟩ ::= ‘==’ | ‘<=’ | ‘<’ | ‘>=’ | ‘>’ | ‘!=’
    ⟨constant⟩ ::= ⟨string⟩ | ⟨number⟩
    ⟨andor⟩ ::= ‘&’ | ‘|’


In the grammar: square brakets `[ ]` indicate optional contents, `( )*` indicates zero or more, `( x | y )` indicates `x` or `y` and:

`<parent>`
     is a path to an HDF5 group or dataset. The path can contain asterisk (*) characters which match
     zero or more charaters (e.g. '*' functions as a wildcard). 

`<string>`
     is a string constant enclosed in single or double quotes (with a backslash used to escape quotes).
     Any string constant used with LIKE must have wildcards ("%" or "_") explicitly included (if no wildcards are
     included, the query does an exact match).

`<number>`
     is a numeric constant. 

`<child>`
     is the name of an HDF5 attribute or dataset within the parent.

`<string>`
     is a string constant enclosed in single or double quotes with a backslash used to escape the strings.

`<number>`
     is a numeric constant.


Some example queries:

.. csv-table::
   :header: "Query", "Description"
   :widths: 35, 25

   "/general/subject: (species == ""Mus musculus"")",   "Selects all files with the specified species"
   "/general:(virus)",                                  "Selects all records with a virus dataset"
   "/general:(virus LIKE ""%infectionLocation: M2%"")", "Selects all datasets virus with infectionLocation: M2"
   "\*:(neurodata_type == ""RoiResponseSeries"")",      "Select all TimeSeries containing Calcium imaging data"
   "\*/data: (unit == ""unknown"")",                    "Selects all datasetes data which unit is unknown"
   "\*/epochs/\*: (start_time > 500 & start_time < 550 & tags LIKE ""%HitL%"" & tags LIKE ""%LickEarly%"")", "Select all epochs with the matching start_time and tags"
   "/general/subject: (subject_id == ""anm00210863"") & \*/epochs/\*: (start_time > 500 & start_time < 550 & tags LIKE ""%LickEarly%"")", "Select files with the specified subject_id and epochs"
   "/units: id, location == ""CA3"" & quality > 0.8",   "Select unit id where location is CA3 and quality > 0.8"

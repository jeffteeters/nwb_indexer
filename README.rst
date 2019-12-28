nwbindexer and search_nwb
=========================

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
--------------------

Instructions for installation and usage are at:
https://nwbindexer.readthedocs.io

License
-------

License terms are in file ``license.txt`` (reproduced below).


Copyright ©2019. The Regents of the University of California (Regents).  All Rights Reserved.

Permission to use, copy, modify, and distribute this software
and its documentation for educational, research, and not-for-profit purposes, without 
fee and without a signed licensing agreement, is hereby granted, provided that the 
above copyright notice, this paragraph and the following two paragraphs appear in all 
copies, modifications, and distributions.  Contact The Office of Technology Licensing, 
UC Berkeley, 2150 Shattuck Avenue, Suite 510, Berkeley, CA 94720-1620,
(510) 643-7201, otl@berkeley.edu, http://ipira.berkeley.edu/industry-info 
for commercial licensing opportunities.

IN NO EVENT SHALL REGENTS BE LIABLE TO ANY PARTY FOR DIRECT, INDIRECT, SPECIAL, 
INCIDENTAL, OR CONSEQUENTIAL DAMAGES, INCLUDING LOST PROFITS, ARISING OUT OF THE USE 
OF THIS SOFTWARE AND ITS DOCUMENTATION, EVEN IF REGENTS HAS BEEN ADVISED OF THE 
POSSIBILITY OF SUCH DAMAGE.

REGENTS SPECIFICALLY DISCLAIMS ANY WARRANTIES, INCLUDING, BUT NOT LIMITED TO, 
THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE. 
THE SOFTWARE AND ACCOMPANYING DOCUMENTATION, IF ANY, PROVIDED HEREUNDER IS PROVIDED 
"AS IS". REGENTS HAS NO OBLIGATION TO PROVIDE MAINTENANCE, SUPPORT, UPDATES, 
ENHANCEMENTS, OR MODIFICATIONS.




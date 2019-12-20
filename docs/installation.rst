Installation
============

1. Download the repository using:

   ``git clone https://github.com/jeffteeters/nwbindexer.git``


2. cd into the created directory:

   ``cd nwbindexer``

3. Optional: if parsimonious and pytest are installed, tests can be run on the downloaded package
   (before installing) by running pytest with no arguments:

   ``pytest``

   Output should indicate all tests (5) passed.

4. To install, make sure you are in the directory 'nwbindexer' containing file "setup.py".  Then type:

   ``pip install .``

5. To test the installation (separately from the files downloaded), cd to a dirctory that does not contain
   the nwbindexer directory, then type:

   ``pytest --pyargs nwbindexer``

   Output should indicate all all tests (5) passed. 

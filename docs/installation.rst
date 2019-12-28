.. index:: 
   single: Installation
   single: pytest
   single: testing


Installation
============

Install release from TestPyPI
-----------------------------

.. note::

   This method (Install from `TestPyPI <https://test.pypi.org/>`_) is setup temporarily for testing.
   When the package is uploaded to PyPI (below), this method will be removed.  It is setup
   now because the PyPI method (below) is not yet ready.

..

   To install using `TestPyPI <https://test.pypi.org/>`_ run:

   $ ``pip install -i https://test.pypi.org/simple/ nwbindexer``


Install release from PyPI
-------------------------

.. warning::

   The PyPI installation method is not yet ready.  Use either TestPyPI (above)
   or Install from Git repository (below).


The `Python Package Index (PyPI) <https://pypi.org>`_ is a repository of software for the
Python programming language.  To install or update nwbindexer from PyPI run:

    $ ``pip install -U nwbindexer``


This will automatically install the following dependencies as well as *nwbindexer*:

 * *parsimonious*
 * *h5py*
 * *numpy*


.. _testing_the_installation:

Testing the installation (optional)
...................................


To test the installation, *pytest* must be installed.  It can be installed
using:

   $ ``pip install pytest``

Once *pytest* is installed, the nwbindexer installation can be tested by running:

   $ ``pytest --pyargs nwbindexer``


Output should indicate all all tests (5) passed. 


.. _install_from_git_repository:

Install from Git repository
---------------------------

First clone the repository and cd into the created directory:

   | $ ``git clone https://github.com/jeffteeters/nwbindexer.git``
   | $ ``cd nwbindexer``


Test local files, not yet installed (optional)
..............................................


To test the locally cloned files before installing, first
packages *parsimonious*, *h5py* and *pytest* must be
installed.  They can be installed using:

   | $ ``pip install parsimonious``
   | $ ``pip install h5py``
   | $ ``pip install pytest``

Then, the tests can be run when inside the top-level nwbindexer directory
created from the clone (which contains file *setup.py*),
by entering *pytest* with no arguments:


   $ ``pytest``


Output should indicate all tests (5) passed.

Completing the installation
...........................


To complete the installation, when directly inside the directory created by the clone
(containing file *setup.py*) either enter the following for a normal installation
(not used for development):

   $ ``pip install .``


**OR** enter the following to create an `editable install <https://packaging.python.org/guides/distributing-packages-using-setuptools/#working-in-development-mode>`_
which is recommended for development (include the `-e` option):

   $ ``pip install -e .``


Test the installation (optional)
................................


To test the installation (separately from the cloned files downloaded), cd to a directory
that does not contain the cloned nwbindexer directory, then type:

   $ ``pytest --pyargs nwbindexer``

Output should indicate all all tests (5) passed.


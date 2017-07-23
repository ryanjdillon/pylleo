Pylleo
======

|Documentation Status|_

A collection of python utilities for working with data from Little
Leonardo accelerometers

Quickstart
----------
`pylleo` is currently only available for `Python 3` and has not been
extensively tested with different versions. For more detail, please refer to
the documentation.

Install
~~~~~~~

.. code::

    pip3 install pylleo

Load data
~~~~~~~~~

.. code:: python

    import pylleo

    path_dir = './'
    meta = pylleo.lleoio.read_meta(path_dir, 'W190PD3GT', 34840)
    data = pylleo.lleoio.read_data(meta, path_dir)

Calibration app
~~~~~~~~~~~~~~~
o
.. code::

    pylleo-cal


Documentation
-------------
The latest documentation for `pylleo` can be found
here_

.. _here: `Documentation Status`_
.. |Documentation Status| image:: https://readthedocs.org/projects/pylleo/badge/?version=latest
.. _Documentation Status: http://pylleo.readthedocs.io/en/latest/?badge=latest

License
-------
This project is licensed under the terms of the GPLv3 license. Please see the
license file in this repository.

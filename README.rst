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
Launch an interpreter:

.. code::

    ipython3

Then load data organized as described in the documentation:

.. code:: python

    import pylleo

    data_path = './'
    meta = pylleo.lleoio.read_meta(data_path, 'W190PD3GT', 34840)
    data = pylleo.lleoio.read_data(meta, data_path)

Calibration app
~~~~~~~~~~~~~~~
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
This project is licensed under the terms of the MIT license. Please see the
license file in this repository.

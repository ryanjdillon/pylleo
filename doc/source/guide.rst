Guide
=====

Installation
------------
`pylleo` is written in `Python 3.5` and does not currently support prior
versions. It is available from the PyPi repository and can be installed using
`pip`:

.. code::

    pip3 install pylleo

It is preferable to use a Python virtual environment, particularly to avoid any
problems if you are have multiple Python versions installed.

.. code::

   cd <project path>
   virtualenv --python=python3 venv
   source venv/bin/activate
   pip install pylleo

If you have installed `pylleo` using a virtual environment, be sure to activate
that environment before running the `pylleo-cal` script described in the
:ref:`calibration` documentation.

Loading data
------------
The data must first be downloaded from the datalogger using the Little Leonardo
software. `pylleo` uses the filename for loading the data, so care should be
taken to name the files correctly (shown below). While `pylleo` will
automatically try to identiy for the timestamp format used, it is recommended
that you follow the `ISO 8601` date format without underscores, i.e.
`YYYYMMDD`.

.. code:: bash

    <date>_<tag model>_<tag serial>_<animal_name>_<modification>_suffix.TXT


Below is an example of how the contents of a Little Leonardo data directory
should look:

.. code:: bash

    ./20160418_W190PD3GT_34840_Skinny_2Neutral
    ├── 20160418_W190PD3GT_34840_Skinny_2Neutral-Acceleration-X.TXT
    ├── 20160418_W190PD3GT_34840_Skinny_2Neutral-Acceleration-Y.TXT
    ├── 20160418_W190PD3GT_34840_Skinny_2Neutral-Acceleration-Z.TXT
    ├── 20160418_W190PD3GT_34840_Skinny_2Neutral-Depth.TXT
    ├── 20160418_W190PD3GT_34840_Skinny_2Neutral-Propeller.TXT
    └── 20160418_W190PD3GT_34840_Skinny_2Neutral-Temperature.TXT

The code can then be loaded to a pandas dataframe, by first creating a
meta-data dictionary (saved as a YAML format file to the data directory), and
then loading the data using the created meta-data.

.. code:: python

    import pylleo

    path_dir = './'
    meta = pylleo.lleoio.read_meta(path_dir, 'W190PD3GT', 34840)
    data = pylleo.lleoio.read_data(meta, path_dir)


Calibration
-----------

The acclerometer and propeller data must be calibrated before being used for
analysis. The sections below provide information on how to apply these
calibrations. For instructions on how to a calibration file (i.e. `cal.yml`)
or the propeller calibration `.csv` file, please see the :ref:`calibration`
documentation.

Calibrating accelerometer data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The calibration file `cal.yml` created during the calibration process is first
loaded, and then the coefficents for the fit of the calibration data for each
axis is applied to that axis data in the loaded dataframe.

.. code:: python

    from pylleo import lleocal

    # Load calibrate data
    cal_dict = yamlord.read_yaml('cal.yml')

    # Apply calibration to accelerometer axes and
    # save as new columns to the dataframe
    data = lleocal.calibrate_acc(data, cal_dict, col_name)


Calibrating propeller data
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

    cal_fname = './speed_calibrations.csv'

    # Calibrate propeller measurements to speed m s^-2
    data = calibrate_propeller(data_df, cal_fname)

Interpolation of sensor data
----------------------------------
The data of sensors that sample at a lower frequency than another sensor (e.g.
the accelerometer) can be interpolated using the `pandas.DataFrame` class
method `interpolate
<https://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.interpolate.html>`_
as shown below.

.. code:: python

    data.interpolate('linear', inplace=True)


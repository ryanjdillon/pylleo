
def get_cal_data(data_df, cal_dict, param):
    '''Get data along specified axis during calibration intervals

    Args
    ----
    data_df: pandas.DataFrame
        Pandas dataframe with lleo data
    cal_dict: dict
        Calibration dictionary

    Returns
    -------
    lower: pandas dataframe
        slice of lleo datafram containing points at -1g calibration position
    upper: pandas dataframe
        slice of lleo datafram containing points at -1g calibration position

    See also
    --------
    lleoio.read_data: creates pandas dataframe `data_df`
    read_cal: creates `cal_dict` and describes fields
    '''

    param = param.lower().replace(' ','_').replace('-','_')

    idx_lower_start = cal_dict['parameters'][param]['lower']['start']
    idx_lower_end   = cal_dict['parameters'][param]['lower']['end']
    idx_upper_start = cal_dict['parameters'][param]['upper']['start']
    idx_upper_end   = cal_dict['parameters'][param]['upper']['end']

    idx_lower = (data_df.index >= idx_lower_start) & \
                (data_df.index <= idx_lower_end)

    idx_upper = (data_df.index >= idx_upper_start) & \
                (data_df.index <= idx_upper_end)

    return data_df[param][idx_lower], data_df[param][idx_upper]


def read_cal(cal_yaml_path):
    '''Load calibration file if exists, else create

    Args
    ----
    cal_yaml_path: str
        Path to calibration YAML file

    Returns
    -------
    cal_dict: dict
        Key value pairs of calibration meta data
    '''
    from collections import OrderedDict
    import datetime
    import os
    import warnings
    import yamlord

    from . import utils

    def __create_cal(cal_yaml_path):
        cal_dict = OrderedDict()

        # Add experiment name for calibration reference
        base_path, _ = os.path.split(cal_yaml_path)
        _, exp_name = os.path.split(base_path)
        cal_dict['experiment'] = exp_name

        return cal_dict

    # Try reading cal file, else create
    if os.path.isfile(cal_yaml_path):
        cal_dict = yamlord.read_yaml(cal_yaml_path)
    else:
        cal_dict = __create_cal(cal_yaml_path)
        cal_dict['parameters'] = OrderedDict()

    for key, val in utils.parse_experiment_params(cal_dict['experiment']).items():
        cal_dict[key] = val

    fmt = "%Y-%m-%d %H:%M:%S"
    cal_dict['date_modified'] = datetime.datetime.now().strftime(fmt)

    return cal_dict


def update(data_df, cal_dict, param, bound, start, end):
    '''Update calibration times for give parameter and boundary'''
    from collections import OrderedDict

    if param not in cal_dict['parameters']:
        cal_dict['parameters'][param] = OrderedDict()
    if bound not in cal_dict['parameters'][param]:
        cal_dict['parameters'][param][bound] = OrderedDict()

    cal_dict['parameters'][param][bound]['start'] = start
    cal_dict['parameters'][param][bound]['end']   = end

    return cal_dict


def fit1d(lower, upper):
    '''Fit acceleration data at lower and upper boundaries of gravity

    Args
    ----
    lower: pandas dataframe
        slice of lleo datafram containing points at -1g calibration position
    upper: pandas dataframe
        slice of lleo datafram containing points at -1g calibration position

    Returns
    -------
    p: ndarray
        Polynomial coefficients, highest power first. If y was 2-D, the
        coefficients for k-th data set are in p[:,k]. From `numpy.polyfit()`.

    NOTE
    ----
    This method should be compared agaist alternate linalg method, which allows
    for 2d for 2d poly, see - http://stackoverflow.com/a/33966967/943773

    A = numpy.vstack(lower, upper).transpose()
    y = A[:,1]
    m, c = numpy.linalg.lstsq(A, y)[0]
    '''
    import numpy

    # Get smallest size as index position for slicing
    idx = min(len(lower), len(upper))

    # Stack accelerometer count values for upper and lower bounds of curve
    x = numpy.hstack((lower[:idx].values, upper[:idx].values))
    x = x.astype(float)

    # Make corresponding y array where all lower bound points equal -g
    # and all upper bound points equal +g
    y = numpy.zeros(len(x), dtype=float)
    y[:idx] = -1.0 # negative gravity
    y[idx:] =  1.0 # positive gravity

    return numpy.polyfit(x, y, deg=1)


def calibrate_acc(data_df, cal_dict):

    def apply_poly(data_df, cal_dict, param):
        '''Apply poly fit to data array'''
        import numpy

        poly = cal_dict['parameters'][param]['poly']
        a = numpy.polyval(poly, data_df[param])

        return a.astype(float)

    # Apply calibration and add as a new column to the dataframe
    for ax in ['x', 'y', 'z']:
        col = 'A{}_g'.format(ax)
        col_cal = 'acceleration_{}'.format(ax)
        data_df[col] = apply_poly(data_df, cal_dict, col_cal)

    return data_df


def create_speed_csv(cal_fname, data):
    import numpy

    # Get a mask of values which contain a sample, assuming the propeller was
    # not sampled at as high of a frequency as the accelerometer
    notnan = ~numpy.isnan(data['propeller'])

    # Read speed, start, and end times from csv
    cal = pandas.read_csv(cal_fname)

    # For each calibration in `speed_calibrations.csv`
    for i in range(len(cal)):
        start = cal.loc[i, 'start']
        start = cal.loc[i, 'end']
        dt0 = pylleo.utils.nearest(data['datetimes'][notnan], start)
        dt1 = pylleo.utils.nearest(data['datetimes'][notnan], end)
        cal_mask = (data['datetimes']>=dt0) & (data['datetimes']<=dt1)
        count_avg = data['propeller'][cal_mask].mean()

        cal.loc[i, 'count_average'] = count_avg

    cal.to_csv(cal_fname)

    return cal


def calibrate_propeller(data_df, cal_fname, plot=False):

    def speed_calibration_average(cal_fname, plot):
        '''Cacluate the coefficients for the mean fit of calibrations

        Notes
        -----
        `cal_fname` should contain three columns:
        date,est_speed,count_average
        2014-04-18,2.012,30
        '''
        import datetime
        import matplotlib.pyplot as plt
        import numpy
        import pandas

        # Read calibration data
        calibs = pandas.read_csv(cal_fname)
        calibs['date'] = pandas.to_datetime(calibs['date'])

        # Get unique dates to process fits for
        udates = numpy.unique(calibs['date'])

        # Create x data for samples and output array for y
        n_samples = 1000
        x = numpy.arange(n_samples)
        fits = numpy.zeros((len(udates), n_samples), dtype=float)

        # Calculate fit coefficients then store `n_samples number of samples
        # Force intercept through zero (i.e. zero counts = zero speed)
        # http://stackoverflow.com/a/9994484/943773
        for i in range(len(udates)):
            cal = calibs[calibs['date']==udates[i]]
            xi = cal['count_average'].values[:, numpy.newaxis]
            yi = cal['est_speed'].values
            m, _, _, _ = numpy.linalg.lstsq(xi, yi)
            fits[i, :] = m*x
            # Add fit to plot if switch on
            if plot:
                plt.plot(x, fits[i,:], label='cal{}'.format(i))

        # Calculate average of calibration samples
        y_avg = numpy.mean(fits, axis=0)

        # Add average fit to plot and show if switch on
        if plot:
            plt.plot(x, y_avg, label='avg')
            plt.legend()
            plt.show()

        # Calculate fit coefficients for average samples
        x_avg = x[:, numpy.newaxis]
        m_avg, _, _, _ = numpy.linalg.lstsq(x_avg, y_avg)

        return m_avg

    m_avg = speed_calibration_average(cal_fname, plot=plot)
    data_df['speed'] = m_avg * data_df['propeller']

    return data_df

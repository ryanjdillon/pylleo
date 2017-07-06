
def get_cal_data(data_df, cal_dict, param):
    '''Get data along specified axis during calibration intervals

    Args
    ----
    data_df: pd.dataframe
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

    Returns
    -------
    cal_dict: dict
        Key value pairs of calibration meta data including:
        - date modified
        - experiment name
        - parameters:
            * start/stop indices for calibration points
            * polyfit coefficients for fitting data to calibration curve
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
        _, experiment = os.path.split(base_path)
        cal_dict['experiment'] = experiment

        return cal_dict

    # Try reading cal file, else create
    if os.path.isfile(cal_yaml_path):
        cal_dict = yamlord.read_yaml(cal_yaml_path)
    else:
        cal_dict = __create_cal(cal_yaml_path)
        cal_dict['parameters'] = OrderedDict()

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

def apply_poly(data_df, cal_dict, param):
    '''Apply poly fit to data array'''
    import numpy

    poly = cal_dict['parameters'][param]['poly']
    a = numpy.polyval(poly, data_df[param])

    return a.astype(float)

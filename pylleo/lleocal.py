
def get_cal_data(data_df, cal_dict, param):
    '''Get data along specified axis during calibration intervals'''

    param = param.lower().replace(' ','_').replace('-','_')

    idx_lower_start = cal_dict[param]['lower']['start']
    idx_lower_end   = cal_dict[param]['lower']['end']
    idx_upper_start = cal_dict[param]['upper']['start']
    idx_upper_end   = cal_dict[param]['upper']['end']

    idx_lower = (data_df.index >= idx_lower_start) & \
                (data_df.index <= idx_lower_end)

    idx_upper = (data_df.index >= idx_upper_start) & \
                (data_df.index <= idx_upper_end)

    return data_df[param][idx_lower], data_df[param][idx_upper]


def read_cal(cal_yaml_path):
    '''Load calibration file if exists, else create'''
    from collections import OrderedDict
    import datetime
    import os
    import warnings

    from pylleo.pylleo import yamlutils
    from pylleo.pylleo import utils

    def __create_cal(cal_yaml_path):
        cal_dict = OrderedDict()

        cal_dict['versions'] = utils.get_versions()

        # Add experiment name for calibration reference
        base_path, _ = os.path.split(cal_yaml_path)
        _, experiment = os.path.split(base_path)
        cal_dict['experiment'] = experiment


    # Try reading cal file, else create
    try:
        cal_dict = yamlutils.read_yaml(cal_yaml_path)
    except:
        cal_dict = __create_cal(cal_yaml_path)

    fmt = "%Y-%m-%d %H:%M:%S"
    cal_dict['date_modified'] = datetime.datetime.now().strftime(fmt)

    # TODO necessary?
    # Give warning if loaded calibration file created with older version
    current_version = utils.get_githash('long')
    cal_version = cal_dict['versions']['pylleo']
    if (current_version!=cal_version):
        warnings.warn('The calibration file has been created with an '
                      'older version of Pylleo')
    return cal_dict


def update(data_df, cal_dict, param, bound, start, end):
    '''Update calibration times for give parameter and boundary'''
    from collections import OrderedDict

    if param not in cal_dict:
        cal_dict[param] = OrderedDict()
    if bound not in cal_dict[param]:
        cal_dict[param][bound] = OrderedDict()

    cal_dict[param][bound]['start'] = start
    cal_dict[param][bound]['end']   = end

    return cal_dict


def fit1d(lower, upper):
    '''Fit acceleration data at lower and upper boundaries of gravity

    # TODO compare agaist alternate linalg method, allows for 2d
    # for 2d poly, see - http://stackoverflow.com/a/33966967/943773
    #A = numpy.vstack(lower, upper).transpose()
    #y = A[:,1]
    #m, c = numpy.linalg.lstsq(A, y)[0]
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

    poly = cal_dict[param]['poly']

    return numpy.polyval(poly, data_df[param])

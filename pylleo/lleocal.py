
def get_cal_data(data_df, cal_dict, param):
    '''Get data along specified axis during calibration intervals'''

    param = param.lower().replace(' ','_').replace('-','_')

    idx_lower = (data_df['datetime'] >= cal_dict[param]['lower']['start']) & \
                (data_df['datetime'] <= cal_dict[param]['lower']['end'])

    idx_upper = (data_df['datetime'] >= cal_dict[param]['upper']['start']) & \
                (data_df['datetime'] <= cal_dict[param]['upper']['end'])

    return data_df[param][idx_lower], data_df[param][idx_upper]


def load(cal_yaml_path):
    '''Load calibration file if exists, else create'''
    from collections import OrderedDict
    import os

    from pylleo.pylleo import yamlutils
    import datetime

    try:
        cal_dict = yamlutils.read_yaml(cal_yaml_path)
    except:
        cal_dict = OrderedDict()

    param = str(cal_select.value)
    bound = str(bound_select.value)

    # Create dictionary fields if not in meta dict
    if 'git_hash' not in cal_dict:
        cal_dict['git_hash'] = utils.get_githash('long')

    if 'date_created' not in cal_dict:
        fmt = "%Y-%m-%d %H:%M"
        cal_dict['date_created'] = datetime.datetime.now().strftime(fmt)

    if 'experiment' not in cal_dict:
        cal_dict = os.path.split(data_path)[1]

    cal_dict = update_calibration(cal_dict, param, start, end):

    return cal_dict


def update(cal_dict, param, bound, start, end):
    '''Update calibration times for give parameter and boundary'''
    from collections import OrderedDict

    if param not in cal_dict:
        cal_dict[param] = OrderedDict()
    if bound not in cal_dict[param]:
        cal_dict[param][bound] = OrderedDict()

    cal_dict[param][bound]['start'] = start
    cal_dict[param][bound]['end']   = end

    cal_dict[param]['poly'] = fit1d(get_cal_data(data_df, cal_dict, param))

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

    return polyfit(x, y, deg=1)

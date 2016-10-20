
#    ACC:
#      CALTIMESPAN:
#      - '82.949309', '8444.2396'
#      CALTIMESPANUNIT: seconds
#      LASTCAL:
#	  - '2015', '12', '18', '12', '7', '7.769'
#      MAP:
#	  - '-1', '0', '0', '0', '1', '0', '0', '0', '1'
#      MAPRULE: front#45;right#45;up
#      METHOD: data
#      PC:
#        POLY:
#		- '-1.5821e-05', '5.0451e-05', '8.9794e-05', '0', '0', '0'
#        SRC: PRESS
#      POLY:
#	  - '5.1327', '4.9815', '4.9918', '-2.4621', '-2.5832', '-2.4605'
#      TC:
#        POLY:
#		- '0', '0', '0'
#        SRC: TEMPR
#      TREF:
#      - '20'
#      TYPE: MEMS#32;accelerometer
#      UNIT: g
#      XC:
	  - '0', '0', '0', '0', '0', '0', '0', '0', '0'

def get_calibration(base_path, filename):
    import os

    import biotelem.acc.yaml_tools

    # TODO make ordered dict, cleaner YAML, meta with calibration?

    cal_yaml_path = os.path.join(base_path, filename+'_cal.yaml')
    if os.path.exists(cal_yaml_path):
        cal_vars = ['acc_x', 'acc_y', 'acc_z', 'max_x', 'mag_y', 'mag_z']
        attrs_l1 = ['lower', 'upper'] # bounds to linear regression
        attrs_l2 = ['start', 'end']   # time at start/end of calibration bound

        cals = dict()
        for var in cal_vars:
            cals[var] = dict()
            for attr1 in attrs_l1:
                cals[var][attr1] = dict()
                for attr2 in attrs_l2:
                    cals[var][attr2] = None
            cals[var]['fit'] = (None, None)
    else:
        cals = biotelem.acc.yaml_tools.read_yaml(cal_yaml_path)


def apply_cal():
    #TODO just pas directory, get base name, load data_df from pickle/create, cals
    cal_yaml_path = #TODO
    cal_dict = yaml_tools.read_yaml(cal_yaml_path)

    # Get slope/intercept of linear regression of calibration data
    #TODO load cals, if fit = acc_x start time None, ask to fill exit
    cals = dict()
    for var in ['acc_x', 'acc_y', 'acc_z']:
        cals[var]['fit'] = fit1d(get_cal_data(data_df, cal_dict, var))


    yaml_tools.write_yaml(cals, cal_yaml_path)

    return cals

    return cals


def calibrate(data_df, base_path, filename):
    '''Calculate calibration coefficients from start/end times for all axes'''
    import yaml_tools
    return None


def get_cal_data(data_df, cal_dict, var):
    '''Get data along specified axis during calibration intervals'''

    var = var.lower().replace(' ','_').replace('-','_')

    idx_lower = (data_df['datetime'] >= cal_dict[var]['lower']['start']) & \
                (data_df['datetime'] <= cal_dict[var]['lower']['end'])

    idx_upper = (data_df['datetime'] >= cal_dict[var]['upper']['start']) & \
                (data_df['datetime'] <= cal_dict[var]['upper']['end'])

    return data_df[var][idx_lower], data_df[var][idx_upper]


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
    y[:idx] = -9.80665 # negative gravity
    y[idx:] =  9.80665 # positive gravity

    return polyfit(x, y, deg=1)

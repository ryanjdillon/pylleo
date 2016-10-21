
def slice_dataframe(df, n):
    '''Return ever n sample from dataframe'''
    # TODO move to tools module
    return df.iloc[::n,:]


def get_file_path(data_path, search_str, file_ext):
    '''Find path of file in directory containing the search string'''
    import os

    file_path = None

    for file_name in os.listdir(data_path):
        if (search_str in file_name) and (file_name.endswith(file_ext)):
            file_path = os.path.join(data_path, file_name)
            break

    if file_path == None:
        raise SystemError('No file found containing string: '
                          '{}.'.format(search_str))

    return file_path


def read_meta(data_path, param_strs, n_header):
    '''Read meta data from Little Leonardo data header rows'''
    from collections import OrderedDict
    import os

    # TODO correct module heirarchy to avoid this
    # http://stackoverflow.com/a/16985066/943773
    from pylleo.pylleo import yamlutils
    from pylleo.pylleo import utils

    def __parse_meta_line(line):
        '''Return key, value pair parsed from data header line'''

        # Parse the key and its value from the line
        key, val = line.replace(':', '').replace('"', '').split(',')

        return key.strip(), val.strip()


    def __read_meta_all(file_path, meta_dict, n_header):
        '''Read all meta data from header rows of data file'''

        with open(file_path, 'r', encoding='ISO-8859-1') as f:
            # Skip 'File name' line
            f.seek(0)
            _ = f.readline()

            # Create child dictionary for channel / file
            line = f.readline()
            key_ch, val_ch = __parse_meta_line(line)
            meta_dict[val_ch] = OrderedDict()

            # Write header values to channel dict
            for _ in range(n_header-2):
                line = f.readline()
                key, val = __parse_meta_line(line)
                meta_dict[val_ch][key] = val.strip()

        return meta


    # Load meta data from YAML file if it already exists
    meta_yaml_path = os.path.join(data_path, 'meta.yaml')

    # TODO check if git hash has changed, if so re-do
    if os.path.isfile(meta_yaml_path):
        meta = yamlutils.read_yaml(meta_yaml_path)

    # Else create meta dictionary and save to YAML
    else:
        # Create dictionary of meta data
        meta = OrderedDict()
        meta['git_hash'] = utils.get_githash('long')

        for param_str in param_strs:
            print('Create meta entry for {}'.format(param_str))
            file_path = get_file_path(data_path, param_str, '.TXT')
            meta      = __read_meta_all(file_path, meta, n_header=n_header)

        yamlutils.write_yaml(meta, meta_yaml_path)

    return meta


def read_data(meta, data_path, n_header, sample_f=1):
    '''Read accelerometry data from leonardo txt files

    sample_f: frequency of values to return, ie. every 'sample_f' values

    'acc_x', float, X axis [m/s^2]
    'acc_y', float, Y axis [m/s^2]
    'acc_z', float, Z axis [m/s^2]
    '''
    import pandas

    #TODO decide how to truncate data, sample_f/n

    def __calc_datetimes(meta, param_str, n_timestamps=None):
        '''Combine accelerometry data'''
        from datetime import datetime, timedelta
        import pandas

        date = meta[param_str]['Start date']
        time = meta[param_str]['Start time']

        fmts  = ['%Y/%m/%d %H%M%S', '%d/%m/%Y %H%M%S', '%d/%m/%Y %I%M%S %p',]

        for fmt in fmts:
            try:
                start = pandas.to_datetime('{} {}'.format(date,time), format=fmt)
            except:
                print('{:14} - date format {:18} incorrect. '
                      'Trying next.'.format(param_str, fmt))
            else:
                print('{:14} - date format {:18} correct.'.format(param_str,
                                                                   fmt))
                break

        # Create datetime array
        datetimes = list()
        increment = float(meta[param_str]['Interval(Sec)'])
        for i in range(int(meta[param_str]['Data size'])):
            secs = increment*i
            datetimes.append(start + timedelta(seconds=secs))

        if n_timestamps:
            datetimes = datetimes[:n_timestamps]

        return datetimes


    def __read_data_file(meta, data_path, param_str, n_header):
        '''Read single Little Leonardo txt data file'''
        import numpy
        import os
        import pandas

        # Get path of data file and associated pickle file
        file_path = get_file_path(data_path, param_str, '.TXT')
        pickle_file = os.path.join(data_path, 'pydata_'+param_str+'.p')
        col_name = param_str.lower().replace(' ','_').replace('-','_')

        # Check if pickle file exists, else create dataframe
        # TODO check version in meta
        if os.path.exists(pickle_file):
            df = pandas.read_pickle(pickle_file)
        else:
            data      = numpy.genfromtxt(file_path, skip_header=n_header)
            datetimes = __calc_datetimes(meta, param_str, n_timestamps=len(data))
            data      = numpy.vstack((datetimes, data)).T
            df        = pandas.DataFrame(data, columns=['datetimes', col_name])

            df.to_pickle(pickle_file)

        return df


    # Read in data files to pandas dataframes
    acc_x = __read_data_file(meta, data_path, 'Acceleration-X', n_header)
    acc_y = __read_data_file(meta, data_path, 'Acceleration-Y', n_header)
    acc_z = __read_data_file(meta, data_path, 'Acceleration-Z', n_header)

    idx = min(len(acc_x), len(acc_y), len(acc_z))
    acc_x = acc_x.iloc[:idx]
    acc_y = acc_y.iloc[:idx]
    acc_z = acc_z.iloc[:idx]

    acc = pandas.concat([acc_x,
                         acc_y['acceleration_y'],
                         acc_z['acceleration_z']], axis=1)

    depth = __read_data_file(meta, data_path, 'Depth', n_header)
    prop  = __read_data_file(meta, data_path, 'Propeller', n_header)
    temp  = __read_data_file(meta, data_path, 'Temperature', n_header)

    return (slice_dataframe(d, sample_f) for d in [acc, depth, prop, temp])

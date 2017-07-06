def get_testdata_path(tag_model):
    '''Get path to sample data directory for given tag model'''
    import os

    tag_model = tag_model.upper().replace('-','').replace('_','')
    sample_path = os.path.join('../datasets/{}'.format(tag_model))

    if not os.path.isdir(sample_path):
        raise FileNotFoundError('No sample dataset found for tag '
                                '{}.'.format(tag_model))
    return sample_path


def load_tag_params(tag_model):
    '''Load param strs and n_header based on model of tag model'''

    tags = dict()
    tags['W190PD3GT'] = ['Acceleration-X', 'Acceleration-Y', 'Acceleration-Z',
                         'Depth', 'Propeller', 'Temperature']

    # Return tag parameters if found, else raise error
    if tag_model in tags:
        return tags[tag_model]
    else:
        raise KeyError('{} not found in tag dictionary'.format(tag_model))


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


def read_meta(data_path, tag_model, tag_id):
    '''Read meta data from Little Leonardo data header rows

    Args
    ----
    data_path: str
        parent directory containing lleo data files
    tag_model: str
        lleo tag model name
    tag_id: str, int
        lleo tag ID number

    Returns
    -------
    meta: dict
        dictionary with meta data from header lines of lleo data files
    '''
    from collections import OrderedDict
    import os
    import yamlord

    from . import utils

    def __parse_meta_line(line):
        '''Return key, value pair parsed from data header line'''

        # Parse the key and its value from the line
        key, val = line.replace(':', '').replace('"', '').split(',')

        return key.strip(), val.strip()


    def __read_meta_all(file_path, meta, n_header):
        '''Read all meta data from header rows of data file'''

        with open(file_path, 'r', encoding='ISO-8859-1') as f:
            # Skip 'File name' line
            f.seek(0)
            _ = f.readline()

            # Create child dictionary for channel / file
            line = f.readline()
            key_ch, val_ch = __parse_meta_line(line)
            val_ch = utils.posix_string(val_ch)
            meta['parameters'][val_ch] = OrderedDict()

            # Write header values to channel dict
            for _ in range(n_header-2):
                line = f.readline()
                key, val = __parse_meta_line(line)
                meta['parameters'][val_ch][key] = val.strip()

        return meta


    def __create_meta(data_path, tag_model, tag_id):
        '''Create meta data dictionary'''
        import datetime

        param_strs = load_tag_params(tag_model)

        # TODO determine n_header automatically
        n_header = 10

        # Create dictionary of meta data
        meta = OrderedDict()
        meta['tag_model'] = tag_model
        meta['tag_id'] = tag_id
        meta['experiment'] = os.path.split(data_path)[1]

        fmt = "%Y-%m-%d %H:%M:%S"
        meta['date_modified'] = datetime.datetime.now().strftime(fmt)

        meta['parameters'] = OrderedDict()
        meta['parameters']['n_header'] = n_header

        for param_str in param_strs:
            print('Create meta entry for {}'.format(param_str))
            file_path = get_file_path(data_path, param_str, '.TXT')
            meta      = __read_meta_all(file_path, meta, n_header=n_header)

        return meta


    # Load meta data from YAML file if it already exists
    meta_yaml_path = os.path.join(data_path, 'meta.yaml')

    # Load file if exists else create
    if os.path.isfile(meta_yaml_path):
        meta = yamlord.read_yaml(meta_yaml_path)

    # Else create meta dictionary and save to YAML
    else:
        meta = __create_meta(data_path, tag_model, tag_id)
        yamlord.write_yaml(meta, meta_yaml_path)

    return meta


def read_data(meta, data_path, sample_f=1, decimate=False, overwrite=False):
    '''Read accelerometry data from leonardo txt files

    Args
    ----
    meta: dict
        dictionary of meta data from header lines of lleo data files
    data_path: str
        parent directory containing lleo data files
    sample_f: int
        return every `sample_f` data points

    Returns
    -------
    acc: 4xn pd.dataframe
        pandas dataframe containing accelerometry data on x, y, z axes [m/s^2]
    depth: 2xn pd.dataframe
        pandas dataframe containing depth data [m]
    prop: 2xn pd.dataframe
        pandas dataframe containing speed data from propeller
    temp: 2xn pd.dataframe
        pandas dataframe containing temperature data
    '''
    import os
    import pandas

    from . import utils

    #TODO pass params in meta directly, remove dependence on meta

    def __calc_datetimes(date, time, interval_s, n_timestamps):
        '''Combine accelerometry data'''
        from datetime import datetime, timedelta
        import pandas

        # TODO problematic if both m/d d/m options
        fmts  = ['%Y/%m/%d %H%M%S',
                 '%d/%m/%Y %H%M%S',
                 '%m/%d/%Y %I%M%S %p',
                 '%d/%m/%Y %I%M%S %p',]

        for fmt in fmts:
            try:
                start = pandas.to_datetime('{} {}'.format(date,time), format=fmt)
            except:
                print('Date format {:18} incorrect, '
                      'trying next...'.format(fmt))
            else:
                print('Date format {:18} correct.'.format(fmt))
                break

        # Create datetime array
        datetimes = list()
        for i in range(n_timestamps):
            secs = interval_s*i
            datetimes.append(start + timedelta(seconds=secs))

        return datetimes


    def __read_data_file(meta, data_path, param_str):
        '''Read single Little Leonardo txt data file'''
        import numpy
        import os
        import pandas

        from . import utils

        # Get path of data file and associated pickle file
        file_path = get_file_path(data_path, param_str, '.TXT')
        col_name = utils.posix_string(param_str)
        n_header = meta['parameters']['n_header']

        print('\nReading: {}'.format(col_name))

        data = numpy.genfromtxt(file_path, skip_header=n_header)

        interval_s = float(meta['parameters'][col_name]['Interval(Sec)'])
        date = meta['parameters'][col_name]['Start date']
        time = meta['parameters'][col_name]['Start time']

        # Generate summed data if propeller sampling rate not 1
        # TODO review and make more general
        if (col_name == 'propeller') and (interval_s < 1):
            print('Too high sampling interval, taking sums')
            # Sampling rate
            fs = int(1/interval_s)

            print('data before', data.max())
            # Drop elements to make divisible by fs for summing
            data = data[:-int(len(data)%fs)]

            # Reshape to 2D with columns `fs` in length to be summed
            data = data.reshape(fs, int(len(data)/fs))
            data = numpy.sum(data, axis=0)
            interval_s = 1

            print('data after', data.max())

        datetimes = __calc_datetimes(date, time, interval_s, len(data))
        data      = numpy.vstack((datetimes, data)).T
        df        = pandas.DataFrame(data, columns=['datetimes', col_name])

        return df

    # Get list of string parameter names for tag model
    param_names = load_tag_params(meta['tag_model'])

    # Load pickle file exists and code unchanged
    pickle_file = os.path.join(data_path, 'pydata_'+meta['experiment']+'.p')

    # Load or create pandas dataframe with parameters associated with tag model
    if (os.path.exists(pickle_file)) and (overwrite is not True):
        data_df = pandas.read_pickle(pickle_file)
    else:
        first_col = True
        for name in param_names:
            next_df = __read_data_file(meta, data_path, name)
            if first_col == False:
                data_df = pandas.merge(data_df, next_df, on='datetimes', how='left')
            else:
                data_df = next_df
                first_col = False
        print('')

        # Covert columns to `datetime64` or `float64` types
        data_df = data_df.apply(lambda x: pandas.to_numeric(x, errors='ignore'))

        # Save file to pickle
        data_df.to_pickle(pickle_file)

    # Return dataframe with ever `sample_f` values
    return data_df.iloc[::sample_f,:]

    # TODO resample/decimate/interpolate

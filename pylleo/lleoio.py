
def read_meta(path_dir, tag_model, tag_id):
    '''Read meta data from Little Leonardo data header rows

    Args
    ----
    path_dir: str
        Parent directory containing lleo data files
    tag_model: str
        Little Leonardo tag model name
    tag_id: str, int
        Little Leonardo tag ID number

    Returns
    -------
    meta: dict
        dictionary with meta data from header lines of lleo data files
    '''
    from collections import OrderedDict
    import os
    import yamlord

    from . import utils

    def _parse_meta_line(line):
        '''Return key, value pair parsed from data header line'''

        # Parse the key and its value from the line
        key, val = line.replace(':', '').replace('"', '').split(',')

        return key.strip(), val.strip()


    def _read_meta_all(f, meta, n_header):
        '''Read all meta data from header rows of data file'''

        # Skip 'File name' line
        f.seek(0)
        _ = f.readline()

        # Create child dictionary for channel / file
        line = f.readline()
        key_ch, val_ch = _parse_meta_line(line)
        val_ch = utils.posix_string(val_ch)
        meta['parameters'][val_ch] = OrderedDict()

        # Write header values to channel dict
        for _ in range(n_header-2):
            line = f.readline()
            key, val = _parse_meta_line(line)
            meta['parameters'][val_ch][key] = val.strip()

        return meta


    def _create_meta(path_dir, tag_model, tag_id):
        '''Create meta data dictionary'''
        import datetime
        from . import utils

        param_strs = utils.get_tag_params(tag_model)

        # Create dictionary of meta data
        meta = OrderedDict()

        # Create fields for the parameters in data directory name
        exp_name = os.path.split(path_dir)[1]
        params_tag = utils.parse_experiment_params(exp_name)
        for key, value in params_tag.items():
            meta[key] = value

        fmt = "%Y-%m-%d %H:%M:%S"
        meta['date_modified'] = datetime.datetime.now().strftime(fmt)

        meta['parameters'] = OrderedDict()

        for param_str in param_strs:
            print('Create meta entry for {}'.format(param_str))

            path_file = utils.find_file(path_dir, param_str, '.TXT')
            # Get number of header rows
            enc = utils.predict_encoding(path_file, n_lines=20)
            with open(path_file, 'r', encoding=enc) as f:
                n_header = utils.get_n_header(f)
                f.seek(0)
                meta = _read_meta_all(f, meta, n_header=n_header)

        return meta


    # Load meta data from YAML file if it already exists
    meta_yaml_path = os.path.join(path_dir, 'meta.yml')

    # Load file if exists else create
    if os.path.isfile(meta_yaml_path):
        meta = yamlord.read_yaml(meta_yaml_path)

    # Else create meta dictionary and save to YAML
    else:
        meta = _create_meta(path_dir, tag_model, tag_id)
        yamlord.write_yaml(meta, meta_yaml_path)

    return meta


def read_data(meta, path_dir, sample_f=1, decimate=False, overwrite=False):
    '''Read accelerometry data from leonardo txt files

    Args
    ----
    meta: dict
        Dictionary of meta data from header lines of lleo data files
    path_dir: str
        Parent directory containing lleo data files
    sample_f: int
        Return every `sample_f` data points

    Returns
    -------
    acc: pandas.DataFrame
        Dataframe containing accelerometry data on x, y, z axes [m/s^2]
    depth: pandas.DataFrame
        Dataframe containing depth data [m]
    prop: pandas.DataFrame
        Dataframe containing speed data from propeller
    temp: pandas.DataFrame
        Dataframe containing temperature data
    '''
    import os
    import pandas

    from . import utils

    def _generate_datetimes(date, time, interval_s, n_timestamps):
        '''Generate list of datetimes from date/time with given interval'''
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


    def _read_data_file(meta, path_dir, param_str):
        '''Read single Little Leonardo txt data file'''
        import numpy
        import os
        import pandas

        from . import utils

        # Get path of data file and associated pickle file
        path_file = utils.find_file(path_dir, param_str, '.TXT')
        col_name = utils.posix_string(param_str)

        # Get number of header rows in file
        enc = utils.predict_encoding(path_file, n_lines=20)
        with open(path_file, 'r', encoding=enc) as f:
            n_header = utils.get_n_header(f)

        print('\nReading: {}'.format(col_name))

        data = numpy.genfromtxt(path_file, skip_header=n_header)

        interval_s = float(meta['parameters'][col_name]['Interval(Sec)'])
        date = meta['parameters'][col_name]['Start date']
        time = meta['parameters'][col_name]['Start time']

        # TODO review
        # Generate summed data if propeller sampling rate not 1
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

        datetimes = _generate_datetimes(date, time, interval_s, len(data))
        data      = numpy.vstack((datetimes, data)).T
        df        = pandas.DataFrame(data, columns=['datetimes', col_name])

        return df

    # Get list of string parameter names for tag model
    param_names = utils.get_tag_params(meta['tag_model'])

    # Load pickle file exists and code unchanged
    pickle_file = os.path.join(path_dir, 'pydata_'+meta['experiment']+'.p')

    # Load or create pandas DataFrame with parameters associated with tag model
    if (os.path.exists(pickle_file)) and (overwrite is not True):
        data_df = pandas.read_pickle(pickle_file)
    else:
        first_col = True
        for name in param_names:
            next_df = _read_data_file(meta, path_dir, name)
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

    # Return DataFrame with ever `sample_f` values
    return data_df.iloc[::sample_f,:]

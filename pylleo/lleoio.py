
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
    data_path: parent directory containing lleo data files
    tag_model: lleo tag model name
    tag_id:    lleo tag ID number

    Returns
    -------
    meta: dictionary with meta data from header lines of lleo data files
    '''
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
        meta['versions'] = utils.get_versions()
        meta['tag_model'] = tag_model
        meta['tag_id'] = tag_id

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
        meta = yamlutils.read_yaml(meta_yaml_path)

        # If current version the not same as meta version, create new
        current_version = utils.get_githash('long')
        meta_version = meta['versions']['pylleo']
        print('current hash:', current_version)
        print('   meta hash:' , meta_version)
        if (current_version!=meta_version):
            meta = __create_meta(data_path, tag_model, tag_id)

    # Else create meta dictionary and save to YAML
    else:
        meta = __create_meta(data_path, tag_model, tag_id)

        yamlutils.write_yaml(meta, meta_yaml_path)

    return meta


def read_data(meta, data_path, sample_f=1):
    '''Read accelerometry data from leonardo txt files

    Args
    ----
    meta:      dictionary of meta data from header lines of lleo data files
    data_path: parent directory containing lleo data files
    sample_f:  return every `sample_f` data points

    Returns
    -------
    acc:   pandas dataframe containing accelerometry data on x, y, z axes [m/s^2]
    depth: pandas dataframe containing depth data [m]
    prop:  pandas dataframe containing speed data from propeller
    temp:  pandas dataframe containing temperature data
    '''
    import pandas

    from pylleo.pylleo import utils

    #TODO pass params in meta directly, remove dependence on meta

    def __calc_datetimes(meta, param_str, n_timestamps=None):
        '''Combine accelerometry data'''
        from datetime import datetime, timedelta
        import pandas

        param_str = utils.posix_string(param_str)
        date = meta['parameters'][param_str]['Start date']
        time = meta['parameters'][param_str]['Start time']

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
        increment = float(meta['parameters'][param_str]['Interval(Sec)'])
        for i in range(int(meta['parameters'][param_str]['Data size'])):
            secs = increment*i
            datetimes.append(start + timedelta(seconds=secs))

        if n_timestamps:
            datetimes = datetimes[:n_timestamps]

        return datetimes


    def __read_data_file(meta, data_path, param_str):
        '''Read single Little Leonardo txt data file'''
        import numpy
        import os
        import pandas

        from pylleo.pylleo import utils

        # Get path of data file and associated pickle file
        file_path = get_file_path(data_path, param_str, '.TXT')
        pickle_file = os.path.join(data_path, 'pydata_'+param_str+'.p')
        col_name = utils.posix_string(param_str)
        n_header = meta['parameters']['n_header']

        # Load pickle file exists and code unchanged
        current_version = utils.get_githash('long')
        meta_version = meta['versions']['pylleo']
        if os.path.exists(pickle_file) and (current_version==meta_version):
            df = pandas.read_pickle(pickle_file)
        else:
            data      = numpy.genfromtxt(file_path, skip_header=n_header)
            datetimes = __calc_datetimes(meta, param_str, n_timestamps=len(data))
            data      = numpy.vstack((datetimes, data)).T
            df        = pandas.DataFrame(data, columns=['datetimes', col_name])

            df.to_pickle(pickle_file)

        return df

    # Read in data files to pandas dataframes
    acc_x = __read_data_file(meta, data_path, 'Acceleration-X')
    acc_y = __read_data_file(meta, data_path, 'Acceleration-Y')
    acc_z = __read_data_file(meta, data_path, 'Acceleration-Z')

    idx = min(len(acc_x), len(acc_y), len(acc_z))
    acc_x = acc_x.iloc[:idx]
    acc_y = acc_y.iloc[:idx]
    acc_z = acc_z.iloc[:idx]

    acc = pandas.concat([acc_x,
                         acc_y['acceleration_y'],
                         acc_z['acceleration_z']], axis=1)

    depth = __read_data_file(meta, data_path, 'Depth')
    prop  = __read_data_file(meta, data_path, 'Propeller')
    temp  = __read_data_file(meta, data_path, 'Temperature')

    return (d.iloc[::sample_f,:] for d in [acc, depth, prop, temp])

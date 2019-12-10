
def get_testdata_path(tag_model):
    '''Get path to sample data directory for given tag model'''
    import os

    tag_model = tag_model.upper().replace('-','').replace('_','')
    sample_path = os.path.join('../datasets/{}'.format(tag_model))

    if not os.path.isdir(sample_path):
        raise FileNotFoundError('No sample dataset found for tag '
                                '{}.'.format(tag_model))
    return sample_path


def predict_encoding(file_path, n_lines=20):
    '''Get file encoding of a text file'''
    import chardet

    # Open the file as binary data
    with open(file_path, 'rb') as f:
        # Join binary lines for specified number of lines
        rawdata = b''.join([f.readline() for _ in range(n_lines)])

    return chardet.detect(rawdata)['encoding']


def get_n_header(f, header_char='"'):
    '''Get the nummber of header rows in a Little Leonardo data file

    Args
    ----
    f : file stream
        File handle for the file from which header rows will be read
    header_char: str
        Character array at beginning of each header line

    Returns
    -------
    n_header: int
        Number of header rows in Little Leonardo data file
    '''

    n_header = 0
    reading_headers = True
    while reading_headers:
        line = f.readline()
        if line.startswith(header_char):
            n_header += 1
        else:
            reading_headers = False

    return n_header


def get_tag_params(tag_model):
    '''Load param strs and n_header based on model of tag model'''

    tag_model = tag_model.replace('-', '')
    tags = dict()
    tags['W190PD3GT'] = ['Acceleration-X', 'Acceleration-Y', 'Acceleration-Z',
                         'Depth', 'Propeller', 'Temperature']

    # Return tag parameters if found, else raise error
    if tag_model in tags:
        return tags[tag_model]
    else:
        raise KeyError('{} not found in tag dictionary'.format(tag_model))


def find_file(path_dir, search_str, file_ext):
    '''Find path of file in directory containing the search string'''
    import os

    file_path = None

    for file_name in os.listdir(path_dir):
        if (search_str in file_name) and (file_name.endswith(file_ext)):
            file_path = os.path.join(path_dir, file_name)
            break

    if file_path == None:
        raise SystemError('No file found containing string: '
                          '{}.'.format(search_str))

    return file_path


def posix_string(s):
    '''Return string in lower case with spaces and dashes as underscores

    Args
    ----
    s: str
        string to modify

    Returns
    -------
    s_mod: str
        string with ` ` and `-` replaced with `_`
    '''
    return s.lower().replace(' ','_').replace('-','_')


def nearest(items, pivot):
    '''Find nearest value in array, including datetimes

    Args
    ----
    items: iterable
        List of values from which to find nearest value to `pivot`
    pivot: int or float
        Value to find nearest of in `items`

    Returns
    -------
    nearest: int or float
        Value in items nearest to `pivot`
    '''
    return min(items, key=lambda x: abs(x - pivot))


def parse_experiment_params(name_exp):
    '''Parse experiment parameters from the data directory name

    Args
    ----
    name_exp: str
        Name of data directory with experiment parameters

    Returns
    -------
    tag_params: dict of str
        Dictionary of parsed experiment parameters
    '''
    if ('/' in name_exp) or ('\\' in name_exp):
        raise ValueError("The path {} appears to be a path. Please pass "
                         "only the data directory's name (i.e. the "
                         "experiment name)".format(name_exp))

    tag_params = dict()
    tag_params['experiment'] = name_exp
    tag_params['tag_model'] = (name_exp.split('_')[1]).replace('-','')
    tag_params['tag_id'] = name_exp.split('_')[2]
    tag_params['animal'] = name_exp.split('_')[3]
    tag_params['notes'] = name_exp.split('_')[4]

    return tag_params


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


def parse_tag_params(exp_name):
    '''Parse the tag and experiment parameters from the experiment name

    Args
    ----
    exp_name: str
        Name to be parsed (e.g. 20160418_W190PD3GT_34840_Skinny_2Neutral)

    Returns
    -------
    tag_params: OrderedDict
        Dictionary of parameters parsed from experiment name
        - tag_model (str): Model of Little Leonardo tag (e.g. W190PD3GT)
        - tag_id (float): Identification number of tag
        - animal (str): Animal tag was attached to
        - notes (str): Notes further identifying experiment
    '''
    from collections import OrderedDict

    tag_params = OrderedDict()

    # Parse data path name fields
    tag_params['experiment'] = exp_name
    tag_params['tag_model'] = exp_name.split('_')[1]
    tag_params['tag_id']    = exp_name.split('_')[2]
    tag_params['animal']    = exp_name.split('_')[3]
    tag_params['notes']     = exp_name.split('_')[4]

    return tag_params

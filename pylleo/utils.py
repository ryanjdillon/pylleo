
def get_versions():
    '''Return versions for repository and packages in requirements file'''
    from collections import OrderedDict
    import os

    import pylleo

    versions = OrderedDict()

    # Add git hash for pylleo to dict
    versions['pylleo'] = get_githash('long')

    # Get path to pylleo requirements file
    module_path = os.path.split(pylleo.__file__)[0]
    requirements = os.path.join(module_path, 'requirements.txt')

    # Add packages and versions to dictionary
    with open(requirements) as f:
        for l in f.readlines():
            package, version = l.strip().split('==')
            versions[package] = version

    return versions


def posix_string(s):
    'Return string in lower case with spaces and dashes as underscores'''
    return s.lower().replace(' ','_').replace('-','_')


def get_githash(hash_type):
    '''Add git commit for reference to code that produced data

    Args
    ----
    hash_type: str
        keyword determining length of has. 'long' gives full hash, 'short'
        gives 6 character hash

    Returns
    -------
    git_hash: str
        Git hash as a 6 or 40 char string depending on keywork `hash_type`
    '''
    import subprocess

    cmd = dict()
    cmd['long']  = ['git', 'rev-parse', 'HEAD']
    cmd['short'] = ['git', 'rev-parse', '--short', 'HEAD']

    return subprocess.check_output(cmd[hash_type]).decode('ascii').strip()

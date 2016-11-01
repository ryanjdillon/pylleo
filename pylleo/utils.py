
def posix_string(s):
    'Return string in lower case with spaces and dashes as underscores'''
    return s.lower().replace(' ','_').replace('-','_')


def get_githash(hash_type):
    '''Add git commit for reference to code that produced data

    hash_type: 'long' gives full hash, 'short' gives 6 character hash
    '''
    import subprocess

    cmd = dict()
    cmd['long']  = ['git', 'rev-parse', 'HEAD']
    cmd['short'] = ['git', 'rev-parse', '--short', 'HEAD']

    return subprocess.check_output(cmd[hash_type]).decode('ascii').strip()

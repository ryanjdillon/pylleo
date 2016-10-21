
def get_githash(hash_type):
    '''Add git commit for reference to code that produced data

    hash_type: 'long' gives full hash, 'short' gives 6 character hash
    '''
    import subprocess

    cmd = dict()
    cmd['long']  = ['git', 'rev-parse', 'HEAD']
    cmd['short'] = ['git', 'rev-parse', '--short', 'HEAD']

    return subprocess.check_output(cmd[hash_type]).decode('ascii').strip()

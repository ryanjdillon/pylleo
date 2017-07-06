def posix_string(s):
    'Return string in lower case with spaces and dashes as underscores'''
    return s.lower().replace(' ','_').replace('-','_')

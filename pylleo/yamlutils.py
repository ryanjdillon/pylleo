
import yaml
from collections import OrderedDict

def read_yaml(file_path, Loader=yaml.Loader, object_pairs_hook=OrderedDict):
    '''Read YAML file and return as python dictionary'''
    # http://stackoverflow.com/a/21912744/943773

    class OrderedLoader(Loader):
        pass

    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))

    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)

    with open(file_path, 'r') as f:

        return yaml.load(f, OrderedLoader)


def write_yaml(data, out_path, Dumper=yaml.Dumper, **kwds):
    '''Write python dict to YAML'''
    import errno
    import os

    class OrderedDumper(Dumper):
        pass
    def _dict_representer(dumper, data):
        return dumper.represent_mapping(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
            data.items())

    OrderedDumper.add_representer(OrderedDict, _dict_representer)

    # Make directory for calibration file if does not exist
    base_path, file_name = os.path.split(out_path)
    try:
        os.makedirs(base_path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(base_path):
            pass
        else: raise

    # Write dictionary to YAML
    with open(out_path, 'w') as f:
        return yaml.dump(data, f, OrderedDumper, default_flow_style=False, **kwds)

#!/usr/bin/env python3

import click

@click.command(help='Perform Little Leonardo accelerometer calibrations')
@click.option('--data-root', prompt=True, help='Data parent directory')

def calibrate_multiple(data_root):
    '''Run calibration on all child directories within `data_root`'''
    import os
    from bokeh.server.server import Server
    from pylleo.bokeh_calibration import Calibrate
    import subprocess
    #import time
    # NOTE This could generalize by using a normal app_path and having the
    # session get pushed to the server within this code, then an app_path and
    # data parent directory could be passed to run different apps on the data
    # directory.

    ## *nix solution: https://stackoverflow.com/a/13143013/943773
    #cmd = 'exec bokeh serve'
    #p = subprocess.Popen(cmd, stderr=subprocess.STDOUT, shell=True)
    ## Kill the Bokeh server process
    #p.kill()

    module_path = os.path.split(os.path.split(pylleo.__file__)[0])[0]
    script_path = os.path.join(module_path, 'bin', 'bokeh_calibration.py')

    # Process1 - Start a bokeh server process
    server = Server()
    server.run_until_shutdown()

    # Process2 -  Open directories within `data_root`
    child_paths_found = False
    i = 0
    for d in sorted(os.listdir(data_root)):
        data_path = os.path.join(data_root, d)
        if os.path.isdir(data_path):
            child_paths_found = True
            #time.sleep(2)

            session_id = 'session_{}'.format(i)
            calapp = Calibrate(data_path, sample_f=30)
            calapp.start(session_id=session_id)
            app_running = True
            while app_running:
                if session_id in server.get_sessions():
                    app_running = False
            i += 1

    server.stop()

    # If no sub-directories with data found in `data_root` raise error
    if child_paths_found is False:
        raise FileNotFoundError('No children data directories found in:\n'
                                '{}'.format(data_root))
    return None


def calibrate(data_path, sample_f=30):
    '''Run calibrations on multiple directory paths'''
    import os
    import subprocess

    import pylleo

    module_path = os.path.split(os.path.split(pylleo.__file__)[0])[0]
    script_path = os.path.join(module_path, 'bin', 'bokeh_calibration.py')


    # Assemble and run command calling Bokeh calibration application
    cmd = ['bokeh', 'serve', '--show', script_path, '--args', str(sample_f),
            data_path]

    output = subprocess.check_output(' '.join(cmd), stderr=subprocess.STDOUT,
                                     shell=True)
    print(output)

    return None


if __name__ == '__main__':
    calibrate_multiple()

'''
LeoADCA
Little Leonardo Accelerometer Data Calibration Application

This app will launch an window in your default broweser to visually identify
the times at which various axis of the lleo tag have been placed into +/-g
orientations.

Enter the start and end times of these orientation periods, then click 'save'
to write those to a calibration YAML file (cal.yml) in the data directory

Example
-------
bokeh serve --show bokeh_calibration.py

'''

def plot_triaxial(height, width, tools):
    '''Plot pandas dataframe containing an x, y, and z column'''
    import bokeh.plotting

    p = bokeh.plotting.figure(x_axis_type='datetime',
                              plot_height=height,
                              plot_width=width,
                              title=' ',
                              toolbar_sticky=False,
                              tools=tools,
                              active_drag=BoxZoomTool(),
                              output_backend='webgl')

    p.yaxis.axis_label = 'Acceleration (count)'
    p.xaxis.axis_label = 'Time (timezone as programmed)'

    # Plot accelerometry data as lines and scatter (for BoxSelectTool)
    colors = ['#1b9e77', '#d95f02', '#7570b3']
    axes = ['x', 'y', 'z']
    lines = [None,]*3
    scats = [None,]*3
    for i, (ax, c) in enumerate(zip(axes, colors)):
        lines[i] = p.line(y=ax, x='dt', color=c, legend=False, source=source)
        scats[i] = p.scatter(y=ax, x='dt', color=c, legend=False, size=1,
                             source=source)
    return p, lines, scats


def load_data(path_dir):
    '''Load data, directory parameters, and accelerometer parameter names

    Args
    ----
    path_dir: str
        Path to the data directory

    Returns
    -------
    data: pandas.DataFrame
        Experiment data
    params_tag: dict
        A dictionary of parameters parsed from the directory name
    params_data: list
        A list of the accelerometer parameter names
    '''
    import os
    import pylleo

    exp_name = os.path.split(path_dir)[1]
    params_tag = pylleo.utils.parse_experiment_params(exp_name)

    # Load the Little Leonardo tag data
    meta = pylleo.lleoio.read_meta(path_dir, params_tag['tag_model'],
                                   params_tag['tag_id'])
    data = pylleo.lleoio.read_data(meta, path_dir, sample_f=sample_f)

    # Get and curate the parameter names of the loaded dataframe
    params_data = pylleo.utils.get_tag_params(params_tag['tag_model'])
    params_data = [pylleo.utils.posix_string(p) for p in params_data]
    params_data = [p for p in params_data if p.startswith('acc')]

    return data, params_tag, params_data


def callback_parent(attr, old, new):
    '''Update data directories drop down with new parent directory'''
    import os

    # Remove accidental white space if copy/pasted
    new = new.strip()
    parent_input.value = new

    # Verify new parent path exists and update `datadirs_select` widget
    if os.path.exists(new):
        # Create sorted list of data directories, ignore files
        joinisdir = lambda parent, d: os.path.isdir(os.path.join(parent, d))
        options = sorted([d for d in os.listdir(new) if joinisdir(new, d)])

        # Update dropdown list of available data directories and select first
        datadirs_select.options = options
        datadirs_select.value = options[0]
        callback_datadirs('value', options[0], options[0])

    else:
        msg = '''
              The parent path `{}` does not exist.

              Check that you have entered the absolute path.
              '''.format(new)
        output_window.text = output_template.format(msg)

    return None


def callback_datadirs(attr, old, new):
    '''Update source and controls with data loaded from selected directory'''
    import os

    global data

    try:
        # Load data from new data directory
        path_dir = os.path.join(parent_input.value, new)
        data, params_tag, params_data = load_data(path_dir)

        # Make title with new data directory
        p.title.text = 'Calibrating {}'.format(params_tag['experiment'])

        # Update `source` data fields from dataframe
        dt_str = [dt.strftime(dt_fmt) for dt in data['datetimes']]
        source.data = dict(x      = list(data['acceleration_x']),
                           y      = list(data['acceleration_y']),
                           z      = list(data['acceleration_z']),
                           ind    = list(data.index),
                           dt     = list(data['datetimes']),
                           dt_str = dt_str)

        # Update values for control widgets
        param_checkbox.active = [0, 1, 2]
        param_select.options = params_data
        param_select.value = params_data[0]
        regions = ['lower', 'upper']
        region_select.options = regions
        region_select.value = regions[0]
        start_input.value = str(data.index[0])
        end_input.value = str(data.index[-1])
    except Exception as e:
        msg = '''
              Problem loading data directory `{}`.

              Please check that data exists in that directory.

              Details:
              {}
              '''.format(new, e)
        output_window.text = output_template.format(msg)


    return None


def callback_box_select(attr, old, new):
    '''Update TextInput start/end entries from BoxSelectTool selection'''

    # Get indices of selection
    ind = sorted(new['1d']['indices'])

    if new is None:
        start_input.value = '0'
        end_input.value = '0'
    else:
        start_input.value = str(source.data['ind'][ind[0]])
        end_input.value = str(source.data['ind'][ind[-1]])
        msg = '''
              New start and end index values set.
              '''
        output_window.text = output_template.format(msg)

    return None


def callback_checkbox(attr, old, new):
    '''Update visible data from parameters selectin in the CheckboxSelect'''
    import numpy

    for i in range(len(lines)):
        lines[i].visible = i in param_checkbox.active
        scats[i].visible = i in param_checkbox.active

    return None


def callback_save_indices():
    '''Save index from bokeh textinput'''
    import datetime
    import os
    import pylleo
    import yamlord

    if datadirs_select.value != 'None':
        path_dir = os.path.join(parent_input.value, datadirs_select.value)
        cal_yaml_path = os.path.join(path_dir, 'cal.yml')

        param = (param_select.value).lower().replace('-','_')
        region = region_select.value
        start = int(start_input.value)
        end   = int(end_input.value)

        msg = '''
              Updated calibration times for:<br>
              <b>{}/{}</b>
              <br>
              <br>
              star index: {}<br>
              end index:  {}<br>
              '''.format(param, region, start, end)
        output_window.text = output_template.format(msg)

        cal_dict = pylleo.lleocal.read_cal(cal_yaml_path)
        # Generalize for Class-ifying
        cal_dict = pylleo.lleocal.update(data, cal_dict, param, region, start, end)
        yamlord.write_yaml(cal_dict, cal_yaml_path)
    else:
        msg = '''
              You must first load data and select indices for calibration
              regions before you can save the indices to `cal.yml`
              '''
        output_window.text = output_template.format(msg)

    return None


def callback_save_poly():
    '''Perform polyfit once regions selected

    Globals: cal_fname, data (read-only, so no declaration)
    '''
    import datetime
    import pylleo
    import yamlord
    import itertools

    def _check_param_regions(param, regions, cal_dict):
        msg = '''
              <b>{}</b> was not found in the calibration dictionary.

              Process that parameter and then try saving the polyfit again.
              '''.format(param)

        params_present = True
        if param not in cal_dict['parameters']:
            params_present = False
            msg.format(param)
        else:
            for region in regions:
                if region not in cal_dict['parameters'][param]:
                    params_present = False
                    msg.format('{}/{}'.format(param, region))
                    output_window.text = output_template.format(msg)

        return params_present


    def _check_index_order(param, regions, cal_dict):
        '''Check that index positions exist for each calibration region'''

        indices_present = True
        for region in regions:
            start = cal_dict['parameters'][param][region]['start']
            end = cal_dict['parameters'][param][region]['end']
            # Check if start comes after end
            if int(start) > int(end):
                indices_present = False
                msg = '''
                      The start index ({}) comes after the end index ({}).

                      Please set new start/end indexes for <b>{}/{}</b>
                      '''.format(start, end, param, region)
                msg.format(start, end, param, region)
                output_window.text = output_template.format(msg)

        return indices_present


    if datadirs_select.value != 'None':
        path_dir = os.path.join(parent_input.value, datadirs_select.value)
        cal_yaml_path = os.path.join(path_dir, cal_fname)
        cal_dict = pylleo.lleocal.read_cal(cal_yaml_path)

        # Get currently selected parameter
        param = param_select.value
        regions = region_select.options

        # Check that index positions have been recorded in `cal.yml`
        if not _check_index_order(param, regions, cal_dict):
            return None

        # Check that index positions are in sequence
        if not _check_index_order(param, regions, cal_dict):
            return None

        param = (param_select.value).lower().replace('-','_')

        try:
            msg = '''
                  Saved polyfit for <b>{}</b> to <b>{}</b>.
                  '''.format(param, cal_fname)
            output_window.text = output_template.format(msg)

            lower, upper = pylleo.lleocal.get_cal_data(data, cal_dict, param)
            poly = list(pylleo.lleocal.fit1d(lower, upper))
            poly = [float(str(i)) for i in poly]

            cal_dict['parameters'][param]['poly'] = poly
            yamlord.write_yaml(cal_dict, cal_yaml_path)
        except Exception as e:
            msg = 'Problem saving polyfit: {}'.format(e)
            output_window.text = output_template.format(msg)
    else:
        msg = '''
              You must first load data and select indices for calibration
              regions before you can save to polyfit to `cal.yml`
              '''
        output_window.text = output_template.format(msg)

    return None


import datetime
import numpy
import os
import sys
import subprocess

from bokeh.layouts import widgetbox, column, row
from bokeh.models import ColumnDataSource
from bokeh.models import PanTool, WheelZoomTool, BoxZoomTool, HoverTool
from bokeh.models import BoxSelectTool
from bokeh.models.widgets import Div, PreText, CheckboxButtonGroup
from bokeh.models.widgets import Select, TextInput, Button
from bokeh.io import curdoc

# DATA
#------------------------------------------------------------------------------
cal_fname = 'cal.yml'
sample_f  = 30
dt_fmt = '%H:%M'

# Create Column Data Source that will be used by the plot
# use 6hr span to avoid straing xaxis labels
t0 = datetime.datetime.now()
t1 = t0 + datetime.timedelta(hours=6)
source = ColumnDataSource(data = dict(x = [0, 0],
                                      y = [0, 0],
                                      z = [0, 0],
                                      ind = [0, 0],
                                      dt = [t0, t1],
                                      dt_str = [t0.strftime(dt_fmt),
                                                t1.strftime(dt_fmt)],
                                      ))

# Input
#------------------------------------------------------------------------------
# Path for entering the parent directory of data directories
title = 'Parent directory:'
css = ['widthfix']
parent_input = TextInput(value='', title=title, css_classes=css)
parent_input.on_change('value', callback_parent)

# Dropdown list of data directories in parent to load data from
data_dirs = ['None']
title = 'Data directories:'
datadirs_select = Select(title=title, value=data_dirs[0], options=data_dirs)
datadirs_select.on_change('value', callback_datadirs)

# Select which axes to select calibration start/end points
param_checkbox_pre = PreText(text='Axes to display')
labels_ax = ['x', 'y', 'z']
active_ax = []
param_checkbox = CheckboxButtonGroup(labels=labels_ax, active=active_ax)
param_checkbox.on_change('active', callback_checkbox)

# Select with parameter to collect start/end times for and perform a data fit
params_data = ['None']
title = 'Parameter to calibrate:'
param_select = Select(title=title, value=params_data[0], options=params_data)

# Select upper or lower acceleration region to calibrate
regions = ['None']
title = 'Bound (lower = -g; upper = +g):'
region_select = Select(title=title, value=regions[0], options=regions)

# User input start end times, save to cal
start_input = TextInput(value='0', title='Start index:')
end_input = TextInput(value='0', title='End index:')

# Save the start end times selcted with BoxSelectTool (or manually entered)
button_save = Button(label='Save Index Values', button_type='success')
button_save.on_click(callback_save_indices)

# Perform a polyfit on the data points occuring between the start/end points
# for the parameter and region selected from the dropdown menus
button_poly = Button(label='Perform Polyfit', button_type='success')
button_poly.on_click(callback_save_poly)

# Print text output from callback/button routines in styled div container
output_template = ('<div style="display:inline-block; width:300px; '
                   'height:150px; padding: 10px; background-color:#f2f2f2; '
                   'border-radius:10px; overflow:scroll">{}</div>')
output_window = Div(text=output_template.format('Status updates display here'))


# Plotting
#------------------------------------------------------------------------------
# Format data to display when HoverTool activated
hover = HoverTool(tooltips=[('index', '@ind'),
                            ('acc', '$y'),
                            ('time', '@dt_str'),
                            ])

# Define plots tools and create plot object and glyph objects
tools = [PanTool(), WheelZoomTool(), BoxSelectTool(), BoxZoomTool(), hover]
p, lines, scats = plot_triaxial(height=300, width=800, tools=tools)
p.select(BoxSelectTool).select_every_mousemove = False

# Force run of callback to make dummy line not visible at init
callback_checkbox('active', active_ax, active_ax)

# Update start/end input text boxes with BoxSelectTool
for scat in scats:
    scat.data_source.on_change('selected', callback_box_select)


# Rendering
#------------------------------------------------------------------------------
# Bundle controls for inserting into the layout
controls = (param_checkbox_pre, param_checkbox, param_select, region_select,
            start_input, end_input, button_save, button_poly)

# Create layout
row1 = row(column(widgetbox(parent_input, datadirs_select)))
col1 = column(widgetbox(*controls), width=350)
# See `output_template for css sizing of window
vbuffer = row([], height=35)
col2 = column(vbuffer, widgetbox(output_window))
row2 = row(col1, col2)

layout = column(p, row1, row2, width=1100)

# Generate document from layout
curdoc().add_root(layout)

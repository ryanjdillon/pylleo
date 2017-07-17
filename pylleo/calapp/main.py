'''
LeoADCA
Little Leonardo Accelerometer Data Calibration Application

This app will launch an window in your default broweser to visually identify
the times at which various axis of the lleo tag have been placed into +/-g
orientations.

Enter the start and end times of these orientation periods, then click 'save'
to write those to a calibration YAML file (cal.yaml) in the data directory

Example
-------
bokeh serve --show bokeh_calibration.py --args  20 <data path>

'''

def plot_triaxial(height, width, tools, title=''):
    '''Plot pandas dataframe containing an x, y, and z column'''
    import bokeh.plotting

    p = bokeh.plotting.figure(x_axis_type='datetime',
                              plot_height=height,
                              plot_width=width,
                              title=title,
                              toolbar_sticky=False,
                              tools=tools,
                              active_drag=BoxZoomTool(),
                              output_backend='webgl')
    p.yaxis.axis_label = 'Acceleration (count)'
    p.xaxis.axis_label = 'Time (timezone as programmed)'

    # Static plot of accelerometry data
    colors = ['#1b9e77', '#d95f02', '#7570b3']
    axes = ['x', 'y', 'z']
    lines = [None,]*3
    scats = [None,]*3
    for i, (ax, c) in enumerate(zip(axes, colors)):
        lines[i] = p.line(y=ax, x='dt', color=c, legend=False, source=source)
        scats[i] = p.scatter(y=ax, x='dt', color=c, legend=False, size=1,
                             source=source)
    return p, lines, scats


def select_callback(attr, old, new):
    '''Update TextInput start/end entries from BoxSelectTool selection'''
    ind = sorted(new['1d']['indices'])

    if new is None:
        start_input.value = str(source.data.ind[0])
        end_input.value = str(source.data.ind[-1])
    else:
        start_input.value = str(source.data['ind'][ind[0]])
        end_input.value = str(source.data['ind'][ind[-1]])

    return None


def checkbox_callback(attr, old, new):
    '''Update visible data from parameters selectin in the CheckboxSelect'''
    import numpy

    for i in range(len(lines)):
        lines[i].visible = i in param_checkbox.active
        scats[i].visible = i in param_checkbox.active

    return None


def save_indices():
    '''Save index from bokeh textinput'''
    import datetime
    import os
    import pylleo
    import yamlord

    cal_yaml_path = os.path.join(data_path, 'cal.yaml')

    param = (param_select.value).lower().replace('-','_')
    bound = bound_select.value
    start = int(start_input.value)
    end   = int(end_input.value)

    msg = '''
          Updated calibration times for:<br>
          <b>{}/{}</b>
          <br>
          <br>
          star index: {}<br>
          end index:  {}<br>
          '''.format(param, bound, start, end)
    output_window.text = output_template.format(msg)

    cal_dict = pylleo.lleocal.read_cal(cal_yaml_path)
    # Generalize for Class-ifying
    cal_dict = pylleo.lleocal.update(data, cal_dict, param, bound, start, end)
    yamlord.write_yaml(cal_dict, cal_yaml_path)

    return None


def save_poly():
    '''Perform polyfit once bounds selected'''
    import datetime
    import pylleo
    import yamlord
    import itertools

    def missing_parameter(p):
        msg = '''
              <b>{}</b> was not found in the calibration dictionary.

              Process that parameter and then try saving the polyfit again.
              '''.format(p)
        output_window.text = output_template.format(msg)

    def indices_misordered(start, end, p, b):
        msg = '''
              The start index ({}) comes after the end index ({}).

              Please set new start/end indexes for <b>{}/{}</b>
              '''.format(start, end, p, b)
        output_window.text = output_template.format(msg)

    cal_fname = 'cal.yaml'
    cal_yaml_path = os.path.join(data_path, cal_fname)
    cal_dict = pylleo.lleocal.read_cal(cal_yaml_path)

    # Check that all necessary calibration parameters are present first
    params_present = True
    for p, b, idx in itertools.product(params_data, bounds, ['start', 'end']):
        if p not in cal_dict['parameters']:
            params_present = False
            missing_parameter(p)
            break
        elif b not in cal_dict['parameters'][p]:
            params_present = False
            missing_parameter('{}/{}'.format(p, b))
            break

        start = cal_dict['parameters'][p][b]['start']
        end = cal_dict['parameters'][p][b]['end']
        if start > end:
            params_present = False
            indices_misordered(start, end, p, b)
            break

    param = (param_select.value).lower().replace('-','_')

    if params_present:
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

    return None


def load_data(data_path):
    from bokeh.models import ColumnDataSource
    import pylleo

    params_tag = pylleo.utils.parse_tag_params(os.path.split(data_path)[1])

    # Load the Little Leonardo tag data
    meta = pylleo.lleoio.read_meta(data_path, params_tag['tag_model'],
                                   params_tag['tag_id'])
    data = pylleo.lleoio.read_data(meta, data_path, sample_f=sample_f)

    # Get and curate the parameter names of the loaded dataframe
    params_data = pylleo.lleoio.load_tag_params(params_tag['tag_model'])
    params_data = [pylleo.utils.posix_string(p) for p in params_data]
    params_data = [p for p in params_data if p.startswith('acc')]

    # Create Column Data Source that will be used by the plot
    dt_fmt = [dt.strftime('%H:%M') for dt in data['datetimes']]
    source = ColumnDataSource(data = dict(x = list(data['acceleration_x']),
                              y = list(data['acceleration_y']),
                              z = list(data['acceleration_z']),
                              ind = list(data.index),
                              dt = list(data['datetimes']),
                              dt_fmt = dt_fmt
                              ))

    return source, params_tag, params_data

import numpy
import os
import sys
import subprocess

from bokeh.layouts import widgetbox, column, row
from bokeh.models import PanTool, WheelZoomTool, BoxZoomTool, HoverTool
from bokeh.models import BoxSelectTool
from bokeh.models.widgets import Div, PreText, CheckboxButtonGroup
from bokeh.models.widgets import Select, TextInput, Button
from bokeh.io import curdoc

# DATA
#------------------------------------------------------------------------------

# Handle commandline arguments
args = sys.argv

if len(args) <= 1:
    print('Usage: bokeh serve --show bokeh_calibration.py '
          '--args <sample_f> <data_path>')
    sys.exit()

sample_f  = int(args[1])
data_path = args[2]

source, params_tag, params_data =  load_data(data_path)

# Input
#------------------------------------------------------------------------------

# Select which axes to select calibration start/end points
param_checkbox_pre = PreText(text='Axes to display')
param_checkbox = CheckboxButtonGroup(labels=["x", "y", "z"], active=[0, 1, 2])

# Select with parameter to collect start/end times for and perform a data fit
param_select = Select(title="Parameter to calibrate:", value=params_data[0],
                      options=params_data)

# Select upper or lower acceleration bound to calibrate
bounds = ['lower', 'upper']
bound_select = Select(title="Bound (lower = -g; upper = +g):", value='lower',
                      options=bounds)

# User input start end times, save to cal
start_input = TextInput(value='0', title='Start index:')
end_input = TextInput(value='0', title='End index:')

# Save the start end times selcted with BoxSelectTool (or manually entered)
button_save = Button(label='Save Index Values', button_type='success')
button_save.on_click(save_indices)

# Perform a polyfit on the data points occuring between the start/end points
# for the parameter and bound selected from the dropdown menus
button_poly = Button(label='Perform Polyfit', button_type='success')
button_poly.on_click(save_poly)

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
                            ('time', '@dt_fmt'),
                            ])

# Define plots tools and create plot object and glyph objects
tools = [PanTool(), WheelZoomTool(), BoxSelectTool(), BoxZoomTool(), hover]
title = 'Calibrating {}'.format(params_tag['experiment'])
p, lines, scats = plot_triaxial(height=300, width=800, tools=tools, title=title)
p.select(BoxSelectTool).select_every_mousemove = False

# Assign callback -  Update plot when acc axes selected/deselected
param_checkbox.on_change('active', checkbox_callback)

# Assign callback -  Update start/end input text boxes with BoxSelectTool
for scat in scats:
    scat.data_source.on_change('selected', select_callback)


# Rendering
#------------------------------------------------------------------------------
# Bundle controls for inserting into the layout
controls = (param_checkbox_pre, param_checkbox, param_select, bound_select,
            start_input, end_input, button_save, button_poly)

# Create layout
vbuffer = row(height=80)
inputs = row(widgetbox(*controls), width=350)
layout = column(p, row(inputs, column(output_window)),
                width=1100)

curdoc().add_root(layout)

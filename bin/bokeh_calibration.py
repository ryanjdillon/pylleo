'''
LeoADCA
Little Leonardo Accelerometer Data Calibration Application

This app will launch an window in your default broweser to visually identify
the times at which various axis of the lleo tag have been placed into +/-g
orientations.

Enter the start and end times of these orientation periods, then click 'save'
to write those to a calibration YAML file (cal.yaml) in the data directory
'''

def timestamp_to_epoch(timestamps):
    '''Convert collection of timestamps to epoch time (nanoseconds)'''
    import pandas
    import numpy

    indexes = pandas.DatetimeIndex(timestamps)
    epochs  = indexes.astype(numpy.int64)

    return epochs


def epoch_to_timestamp(epoch):
    '''Convert a single epoch date to a pandas timestamp'''
    import pandas

    return pandas.to_datetime(epoch, unit='ns')


def date_string_nano(timestamp):
    '''Convert pandas timestamp to string format with nanosecond precision'''
    from datetime import datetime

    dt = epoch_to_timestamp(timestamp).to_datetime()
    s = dt.strftime('%Y-%m-%d %H:%M:%S')
    s += '.{:.5}'.format(str(timestamp)[-9:])

    return s

# TODO get rid of data_df from passed params
def plot_triaxial(data_df, height, width, tools):
    '''Plot pandas dataframe containing an x, y, and z column'''
    import bokeh.plotting

    p = bokeh.plotting.figure(plot_height=height, plot_width=width, title='',
                              toolbar_sticky=False, tools=tools, webgl=True)

    # Static plot of accelerometry data
    x_line = p.line(y='x', x='date', color='#1b9e77', legend='x', source=source)
    y_line = p.line(y='y', x='date', color='#d95f02', legend='y', source=source)
    z_line = p.line(y='z', x='date', color='#7570b3', legend='z', source=source)

    lines = [x_line, y_line, z_line]

    return p, lines


def select_data(acc, acc_slider):
    '''Get data selection from plot controls'''

    slider_dt = epoch_to_timestamp(acc_slider.value)

    data = acc[(acc['datetimes'] == slider_dt)]

    return data


def update(attrname, old, new):
    '''Update plots from selected data'''
    import numpy

    data_selected = select_data(acc, acc_slider)

    vline.set(location=acc_slider.value)

    for i in range(len(lines)):
        lines[i].visible = i in param_checkbox.active

    #source.data['timestep'][0] = acc_slider.value

        # The following can be used to filter/update data,
        # but the amount of data makes this very cpu heavy

        #timesteps = list(data_df['datetime'])
        #x = list(data_df['acc_x']),
        #y = list(data_df['acc_y']),
        #z = list(data_df['acc_z']),

    return None


def save_times():
    '''Save index from bokeh textinput'''
    import datetime
    import os

    from pylleo.pylleo import lleocal
    from pylleo.pylleo import yamlutils

    cal_yaml_path = os.path.join(data_path, 'cal.yaml')

    param = (param_select.value).lower().replace('-','_')
    bound = bound_select.value
    start = int(start_input.value)
    end   = int(end_input.value)

    t_now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(t_now, 'UPDATE CAL TIMES: {}, {}'.format(param, bound))

    cal_dict = lleocal.read_cal(cal_yaml_path)
    cal_dict = lleocal.update(acc, cal_dict, param, bound, start, end)
    yamlutils.write_yaml(cal_dict, cal_yaml_path)

    return None


def save_poly():
    '''Perform polyfit once bounds selected'''
    import datetime

    from pylleo.pylleo import lleocal
    from pylleo.pylleo import yamlutils

    # TODO perhaps put check for bounds and message here
    cal_yaml_path = os.path.join(data_path, 'cal.yaml')
    cal_dict = lleocal.read_cal(cal_yaml_path)

    param = (param_select.value).lower().replace('-','_')

    try:
        t_now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(t_now, 'SAVE POLY: {}'.format(param))

        lower, upper = lleocal.get_cal_data(acc, cal_dict, param)
        poly = list(lleocal.fit1d(lower, upper))
        poly = [float(str(i)) for i in poly]

        cal_dict['parameters'][param]['poly'] = poly
        yamlutils.write_yaml(cal_dict, cal_yaml_path)
    except:
        print('Problem saving polyfit')

    return None


# save state to calibration field
import os
import numpy
import sys
import subprocess

#from bokeh.layouts import layout
from bokeh.layouts import widgetbox
from bokeh.models import WidgetBox, HBox
from bokeh.models import Span, Label
from bokeh.models import PanTool, WheelZoomTool, BoxZoomTool, HoverTool
from bokeh.models import ColumnDataSource
#from bokeh.models.widgets import Tabs, Panel
from bokeh.models.widgets import Button
from bokeh.models.widgets import CheckboxButtonGroup
from bokeh.models.widgets import Slider, Select, TextInput
from bokeh.io import curdoc

from pylleo.pylleo import lleoio
from pylleo.pylleo import utils

# DATA
#------------------------------------------------------------------------------

# Handle commanline arguments
args = sys.argv

if len(args) <= 1:
    print('Usage: bokeh serve --show bokeh_calibration.py '
          '--args <tag_model> <tag_id> <sample_f> <data_path>')
    sys.exit()

# bokeh serve --show bokeh_calibration.py --args W190PD3GT 34839 1 /home/ryan/Desktop/edu/01_PhD/projects/smartmove/data/lleo_coexist/Acceleration/20150311_W190-PD3GT_34839_Skinny_Control

tag_model = args[1]
tag_id    = args[2]
sample_f  = int(args[3])
data_path = args[4]

# TODO handle lleo mag, and other tags...
meta = lleoio.read_meta(data_path, tag_model, tag_id)
acc, depth, prop, temp = lleoio.read_data(meta, data_path, sample_f=sample_f)

param_strs = lleoio.load_tag_params(tag_model)
param_strs = [utils.posix_string(p) for p in param_strs]

# Timestamps in epoch time and strings to nanosecond
dates = timestamp_to_epoch(acc['datetimes'])
#dates_str = [date_string_nano(d) for d in dates]

# Create Column Data Source that will be used by the plot
source = ColumnDataSource(data=dict(x    = list(acc['acceleration_x'].values),
                                    y    = list(acc['acceleration_y'].values),
                                    z    = list(acc['acceleration_z'].values),
                                    date = list(dates),))
# Input
#------------------------------------------------------------------------------

# TODO use callback with BoxSelectTool to get indices rather than TextInput
# http://stackoverflow.com/a/34175864/943773

# Create Input controls
t_min = min(dates)
t_max = max(dates)
acc_slider = Slider(title='Timestep', start=t_min, end=t_max, value=t_min, step=1)

# TODO generalize this for plotting the lines too
param_checkbox = CheckboxButtonGroup(labels=["x", "y", "z"], active=[0, 1, 2])

param_select = Select(title="Calibrate Param:", value=param_strs[0],
                      options=param_strs)

bound_select = Select(title="Bound:", value='lower',
                      options=['lower', 'upper'])

# User input start end times, save to cal
start_input = TextInput(value='0', title='start:')
end_input = TextInput(value='0', title='end:')

button_save = Button(label='Save Times', button_type='success')
button_save.on_click(save_times)

button_poly = Button(label='Perform Polyfit', button_type='success')
button_poly.on_click(save_poly)

controls = [acc_slider, param_checkbox, param_select, bound_select,
            start_input, end_input, button_save, button_poly]


# Plotting
#------------------------------------------------------------------------------

# Axis labels
axis_map = {'Time': 't',
            'Acceleration': 'acc',}

x_axis = Select(title='X Axis', options=sorted(axis_map.keys()), value='Time')
y_axis = Select(title='Y Axis', options=sorted(axis_map.keys()), value='Acceleration')

hover = HoverTool(tooltips=[('index', '$index'),
                            ('acc', '$y'),
                            ('time', '@date'),
                            ])

#'pan,wheel_zoom,box_zoom,reset,hover'
tools = [PanTool(), WheelZoomTool(), BoxZoomTool(), hover]
p, lines = plot_triaxial(acc, 300, 800, tools)

# Add line for current video time
vline = Span(location=0, dimension='height', line_color='red', line_width=3)
p.renderers.extend([vline,])


# Rendering
#------------------------------------------------------------------------------

for control in controls:
    control.on_change('value', update)

inputs = HBox(widgetbox(*controls), width=800)

# initial load of the data
update(None, None, None)

#TODO update to widget, hbox depreciated
curdoc().add_root(HBox(p, inputs, width=1100))

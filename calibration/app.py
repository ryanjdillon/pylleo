'''
LeoADCA
Little Leonardo Accelerometer Data Calibration Application

Author: Ryan J. Dillon

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


def plot_triaxial(data_df, height, width, tools):
    '''Plot pandas dataframe containing an x, y, and z column'''
    import bokeh.plotting

    p = bokeh.plotting.figure(plot_height=height, plot_width=width, title='',
                              toolbar_sticky=False, tools=tools, webgl=True)

    # Static plot of accelerometry data
    p.line(y='x', x='date', color='#1b9e77', legend='x', source=source)
    p.line(y='y', x='date', color='#d95f02', legend='y', source=source)
    p.line(y='z', x='date', color='#7570b3', legend='z', source=source)

    return p


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
    from collections import OrderedDict
    import os

    from biotelem.acc import yaml_tools
    from biotelem.acc import lleo

    cal_yaml_path = os.path.join(data_path, 'cal.yaml')

    try:
        cal_dict = yaml_tools.read_yaml(cal_yaml_path)
    except:
        cal_dict = OrderedDict()

    param = str(param_select.value)
    bound = str(bound_select.value)

    # Create dictionary fields if not in meta dict
    if param not in cal_dict:
        cal_dict[param] = OrderedDict()
    if bound not in cal_dict[param]:
        cal_dict[param][bound] = OrderedDict()

    cal_dict[param][bound]['start'] = start_input.value
    cal_dict[param][bound]['end']   = end_input.value

    yaml_tools.write_yaml(cal_dict, cal_yaml_path)

    return cal_dict


# save state to calibration field
import os
import numpy
import sys

#from bokeh.layouts import layout
from bokeh.layouts import widgetbox
from bokeh.models import WidgetBox, HBox
from bokeh.models import Span, Label
from bokeh.models import PanTool, WheelZoomTool, BoxZoomTool, HoverTool
from bokeh.models import ColumnDataSource
#from bokeh.models.widgets import Tabs, Panel
from bokeh.models.widgets import Slider, Select, TextInput
from bokeh.models.widgets import Button
from bokeh.io import curdoc

from biotelem.acc import lleo

# DATA
#------------------------------------------------------------------------------

# Setup Accelerometer data
base_path = ('/home/ryan/Desktop/edu/01_PhD/projects/smartmove/data/'
             'lleo_coexist/Acceleration/')
exp_path = ('20150311_W190-PD3GT_34839_Skinny_Control')
exp_path = ('20150317_W190PD3GT_34839_Skinny_4Floats')
exp_path = ('20160418_W190PD3GT_34840_Skinny_2Neutral')
data_path = os.path.join(base_path, exp_path)

data_path = sys.argv[1]


# TODO handle lleo mag, and other tags...
param_strs = ['Acceleration-X', 'Acceleration-Y', 'Acceleration-Z', 'Depth',
              'Propeller', 'Temperature']

meta = lleo.read_meta(data_path, param_strs, n_header=10)
acc, depth, prop, temp = lleo.read_data(meta, data_path, n_header=10, sample_f=20)

# TODO make data output similar to dtag, remove this
A = acc[acc.keys()[1:]].values.astype(float)

# Timestamps in epoch time and strings to nanosecond
dates = timestamp_to_epoch(acc['datetimes'])
#dates_str = [date_string_nano(d) for d in dates]

# Create Column Data Source that will be used by the plot
source = ColumnDataSource(data=dict(x    = list(A[:,0]),
                                    y    = list(A[:,1]),
                                    z    = list(A[:,2]),
                                    date = list(dates),
                                    )
                                   )

# Input
#------------------------------------------------------------------------------

# TODO use callback with BoxSelectTool to get indices rather than TextInput
# http://stackoverflow.com/a/34175864/943773

# Create Input controls
t_min = min(dates)
t_max = max(dates)
acc_slider = Slider(title='Timestep', start=t_min, end=t_max, value=t_min, step=1)

param_select = Select(title="Param:", value=param_strs[0], options=param_strs)
bound_select = Select(title="Bound:", value='lower', options=['lower', 'upper'])

# User input start end times, save to cal
start_input = TextInput(value='0', title='start:')
end_input = TextInput(value='0', title='end:')

button_save = Button(label='Save Times', button_type='success')
button_save.on_click(save_times)

controls = [acc_slider, param_select, bound_select, start_input, end_input,
            button_save]


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
p = plot_triaxial(acc, 300, 800, tools)

# Add line for current video time
vline = Span(location=0, dimension='height', line_color='red', line_width=3)
p.renderers.extend([vline,])


# Rendering
#------------------------------------------------------------------------------

for control in controls:
    control.on_change('value', update)

inputs = HBox(widgetbox(*controls), width=800)

# TODO show each parameter to get calibration times as own tab

#l1 = layout([[p]], sizing_mode='fixed')
#l2 = layout([[p]],sizing_mode='fixed')
#
#tab1 = Panel(child=l1,title='This is Tab 1')
#tab2 = Panel(child=l2,title='This is Tab 2')
#
#tabs = Tabs(tabs=[ tab1, tab2 ])

# initial load of the data
update(None, None, None)

#TODO update to widget, hbox depreciated
curdoc().add_root(HBox(p, inputs, width=1100))
#curdoc().add_root(tabs)

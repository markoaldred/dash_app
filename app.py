# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import dash  # USE THIS IF RUNNING ON SERVER
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
#from jupyter_dash import JupyterDash # USE THIS IF RUNNING ON JUPYTER
import numpy as np

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server


#app = dash.Dash(__name__) # USE THIS IIF RUNNING ON SERVER
#app = JupyterDash(__name__) # USE THIS IF RUNNING ON JUPYTER

app.layout = html.Div([
    
    html.Div([
        html.Pre(children= " Length of Stay Histogram Plot",
                style={"text-align": "center", "font-size": "100%", "color":"black"})
    ]),
    
    dcc.Dropdown(
        id='my_dropdown',
        options=[
            {'label': 'Maternity', 'value': 'MT'},
            {'label': 'Delivery Suite', 'value': 'DS'},
            {'label': 'ICU', 'value': 'ICU'},
                ],
                 optionHeight=35,
                 value='MT',
                 disabled=False,
                 multi=False,
                 searchable=True,
                 search_value='',
                 placeholder='Please select... ',
                 clearable=True
                 #style={'width':"100%"},
                 #className='select_box',
                 #persistence=True,
                 #persistence_type='memory' #'session','local' 
                ),
    
    dcc.Graph(id='the_graph')
    
])

@app.callback(
    Output(component_id ='the_graph', component_property='figure'), 
    [Input(component_id ='my_dropdown', component_property='value')])
def update_graph(my_dropdown):
    plot_df = ideal_df
    plot_df = plot_df.loc[plot_df['Ward_Code'] == my_dropdown, :]
    fig = px.histogram(plot_df, x="LOS_hrs", nbins=50)
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
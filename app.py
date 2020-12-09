# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import pandas as pd
import datetime
import numpy as np
import time
import dash  # USE THIS IF RUNNING ON SERVER
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
#from jupyter_dash import JupyterDash # USE THIS IF RUNNING ON JUPYTER

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server


#app = dash.Dash(__name__) # USE THIS IIF RUNNING ON SERVER
#app = JupyterDash(__name__) # USE THIS IF RUNNING ON JUPYTER

mt_beds = 13 #Current Number of Beds Available in Maternity
ds_beds = 4  #Current Number of Beds Available in Delivery Suite

## Bring in Transfers data, update dates and remove uneeded columns
df = pd.read_csv('transfers.csv')
df = df.rename(columns = {'Start_Bed_Dttm':'Start', 'End_Bed_Dttm':'End'})
df = df.drop(columns=['Transfers', 'Bed_Code', 'Full Flow Code', 'Current Flow Code', '1st Level','PASID'])
date_cols = ['Start', 'End']
df[date_cols] = df[date_cols].apply(pd.to_datetime, format='%d/%m/%y %H:%M', errors='raise')
#df[date_cols] = df[date_cols].apply(lambda x: x.dt.strftime('%d/%m/%Y %H:%M:%S'))

#MATERNITY
## Make new dataframe patients entering Maternity Ward
mt_in_df= pd.DataFrame()
mt_in_df['Event'] = df.loc[df['Ward_Code'] == 'MT', 'Start']
mt_in_df['Patient_Change'] = 1
## make new dataframe with patients leaving room
mt_out_df= pd.DataFrame()
mt_out_df['Event'] = df.loc[df['Ward_Code'] == 'MT', 'End']
mt_out_df['Patient_Change'] = -1
## Concatenate the two datasets and sort by date to determin current patinet occupancies
mt_count_df = pd.concat([mt_in_df, mt_out_df])
mt_count_df.sort_values('Event', ascending = True, inplace=True)
mt_count_df['MT_Patients'] = mt_count_df['Patient_Change'].cumsum()
mt_count_df['Bed_Available'] = mt_count_df['MT_Patients'] <= mt_beds
mt_count_df.dropna(inplace = True)

# DELIVERY SUITE(DS)
## Make new dataframe patients entering room
ds_in_df = pd.DataFrame()
ds_in_df['Event'] = df.loc[df['Ward_Code'] == 'DS', 'Start']
ds_in_df['Patient_Change'] = 1
## make new dataframe with patients leaving room
ds_out_df= pd.DataFrame()
ds_out_df['Event'] = df.loc[df['Ward_Code'] == 'DS', 'End']
ds_out_df['Patient_Change'] = -1
## Concatenate the two datasets and sort by date to determin current patinet occupancies
ds_count_df = pd.concat([ds_in_df, ds_out_df])
ds_count_df.sort_values('Event', ascending = True, inplace=True)
ds_count_df['DS_Patients'] = ds_count_df['Patient_Change'].cumsum()
ds_count_df['Bed_Available'] = ds_count_df['DS_Patients'] <= mt_beds
ds_count_df.dropna(inplace = True)

# CLEAN DATA TO PRODUCE IDEAL PATIENT TRANSFERS
ideal_df = pd.DataFrame(df)
#CA, CL & HE Codes are converted to MT
ideal_df.loc[(ideal_df['Ward_Code'] == 'CA') | (ideal_df['Ward_Code'] == 'CL') | (ideal_df['Ward_Code'] == 'HE') , 'Ward_Code'] = 'MT' #Ward Code CA = MT
## Drop DPS from the new dataset
index_names = ideal_df.loc[(ideal_df['Ward_Code'] == 'DPS') | ((ideal_df['Ward_Code'] == 'ON'))].index
ideal_df.drop(index_names, inplace = True)
## Groupby the event code and with ward to summarise and finds any duplicates
events = ideal_df.groupby(['Link', 'Ward_Code'])
#events.get_group(('ADE-272865','MT'))
#get the min start date and max end date from the grouped results
ideal_df['min_start'] = events['Start'].transform('min')
ideal_df['max_end'] = events['End'].transform('max')
#Drop the Original start & end dates & rename the new calculated start & end
ideal_df.drop(columns=['Start', 'End'], inplace = True)
ideal_df.rename(columns= {'min_start':'Start', 'max_end': 'End'}, inplace = True)
ideal_df.sort_values(['Link', 'Ward_Code'], ascending = True, inplace = True)
ideal_df.drop_duplicates(keep='first', inplace = True)
#checks that there are no longer any duplicates
#ideal_df.loc[ideal_df.duplicated(keep=False), :]

# CALCULATE LENGTH OF STAY
ideal_df['LOS'] = (ideal_df['End'] - ideal_df['Start'])
ideal_df['LOS_hrs'] = ((ideal_df['End'] - ideal_df['Start']).dt.days * 24) + ((ideal_df['End'] - ideal_df['Start']).dt.seconds / (60*60))

# EXTRACT EVENTS DATA AND PUT IN THE IDEALISED DATA TABLE
events_df = pd.read_csv('exception_dates.csv')
#events_df.drop(columns=['Unnamed: 2'], inplace = True)
events_df.rename(columns = {'DATE':'Date', 'EVENT':'Event'}, inplace=True)
events_df['Date'] = events_df['Date'].apply(pd.to_datetime, format='%d/%m/%y', errors='raise')
events_df['Date'] = events_df['Date'].dt.date
events_df.sort_values(['Event', 'Date'])
## Combine all labels with the same date into the same field
grouped_events_df = events_df.groupby(['Date'])['Event'].apply(','.join).reset_index()
grouped_events_df.sort_values('Event', ascending=True)
## Delete erroneous Event Data
grouped_events_df = grouped_events_df.drop(grouped_events_df[grouped_events_df.Event == 'SCHOOL,SCHOOL'].index)
grouped_events_df = grouped_events_df.drop(grouped_events_df[grouped_events_df.Event == 'PUBLIC,SCHOOL,SCHOOL'].index)
## Merge data from the events table back into the Idealised data table
ideal_df['Date'] = ideal_df['Start'].dt.date
ideal_merged_df = pd.merge(grouped_events_df, ideal_df, how='right', on='Date')


## Dash App starts here
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
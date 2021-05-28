# -*- coding: utf-8 -*-
"""
Created on Tue May  4 14:20:40 2021

@author: Taneli Mäkelä
"""
import numpy as np
import pandas as pd
import datetime
import plotly.express as px
import plotly.offline
import jinja2



def plotlyplot_line(df1):
    color_map = ['#379f9b', '#f18931', '#006431', '#bd3429',
                 '#814494', '#d82e8a', '#74aa50', '#006aa7']
    x1 = df1.index[0]
    x2 = df1.index[-1] + datetime.timedelta(hours=3)
    df1 = df1.melt(ignore_index=False, var_name='variable', value_name='value')


    fig = px.line(df1, x=df1.index, y="value", color="variable", width=1000, height=700,
                  range_x=[x1, x2], template='ggplot2', color_discrete_sequence=color_map)

    fig.update_layout(legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.3,
        xanchor="right",
        x=0.95
    ))
    
    fig.update_traces(patch={"line": {'width':4, 'color': 'grey'}}, selector={'legendgroup': 'Makelankatu'})
    return fig

def plotlyplot_bar(df1):
    color_map = ['#379f9b', '#f18931', '#006431', '#bd3429',
                 '#814494', '#d82e8a', '#74aa50', '#006aa7']

    df1 = df1.melt(ignore_index=False, var_name='variable', value_name='value')

    fig = px.bar(df1, x=df1.index, y="value", color="variable", barmode = 'group', width=1000, height=700, 
                  template='ggplot2', color_discrete_sequence = color_map)

    fig.update_layout(legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.4,
        xanchor="right",
        x=0.95
    ))
    horizontal_x0 =df1.index[0] - datetime.timedelta(days=1)
    horizontal_x1 =df1.index[-1] + datetime.timedelta(days=1)
    
    fig.add_shape(type="line",
        x0=horizontal_x0, y0=50, x1=horizontal_x1, y1=50,
        line=dict(color="black", width=4, dash="dashdot"))
    return fig




def createTable(df):
    th_props = [('border-collapse', 'separate'),
                 ('border-spacing', '10px'),
                 ('font-size', '14px'),
                 ('text-align', 'center'),
                 #              ('font-weight', 'bold'),
                 ('color', '#6d6d6d'),
                 ('background-color', '#edf5f0'),
                 ('border-style', 'solid'),
                 ('border-width', '3px'),
                 ('border-color', '#edf5f0'),
                 ('padding', '5px'),
                 ('border-collapse', 'separate'),
                 ]

    # Set CSS properties for td elements in dataframe
    td_props = [('border-collapse', 'separate'),
                     ('border-spacing', '10px'),
                     ('font-size', '14px'),
                     ('text-align', 'center'),
                     ('border-style', 'solid'),
                     ('border-width', '1px'),
                     ('padding', '5px'),
                     ('background-color', 'white'),
                     ]
    
    
    styles = [dict(selector="th", props=th_props),
              dict(selector="td", props=td_props)]
    
    df.index.name = 'timestamp(date&time)'
    df_style = df.style.set_table_styles(styles).format("{:.1f}").set_precision(1)
    return df_style


def read_ilmanetcsv():
    def customDateTime(datestr):
        if '24:00' in datestr:
            datestr = datestr.replace('24:00', '00:00')
            return pd.to_datetime(datestr, format="%d.%m.%Y %H:%M") + datetime.timedelta(days=1)
        else:
            return pd.to_datetime(datestr, format="%d.%m.%Y %H:%M")
        
    data = pd.read_csv('http://ilmanlaatu.hsy.fi/data/ilmanet.csv', header=[0,1,2], parse_dates=True)
    data = data.drop(columns=data.filter(like='22').columns)
    data.columns = data.columns.droplevel(1)
    data.iloc[:,0] = data.iloc[:,0].apply(customDateTime)
    data = data.set_index(data.iloc[:,0])
    data.index = pd.to_datetime(data.index, format="%d.%m.%Y %H:%M")
    data = data.apply(pd.to_numeric, errors='coerce')
    data = data.rename(columns=str.lower).rename(columns={'pm2_5': 'pm25'})
    return data

def parse_station_data():
    data = read_ilmanetcsv()
    
    data.columns = ['_'.join(col) for col in data.columns.values]
    data[data==-9999] = np.nan
    return data

def loadTemplate(path, template):
    templateLoader = jinja2.FileSystemLoader(searchpath=path)
    templateEnv = jinja2.Environment(loader=templateLoader)
    TEMPLATE_FILE = template
    template = templateEnv.get_template(TEMPLATE_FILE)
    return template
    
    

def createReport(data_Aqt, savePath, template_folder, template_name, station_id=None, online=True, kartta='sensorikartta.html'):
    components = ['no2', 'no', 'co', 'o3', 'pm10', 'pm25', 'rh', 'temp']
    
    station_data = parse_station_data()
    
    
    data_dict = {}
    for component in components:
        data = data_Aqt[[component, 'sensor_id']]
        data = pd.pivot_table(data, values=component,
                              index=data.index, columns='sensor_id')
        if online:
            data = data.resample('H', label='right').mean().round(1)
        if station_id != None:
            if component in ['no', 'no2', 'pm10', 'pm25', 'o3']:
                refData = station_data.filter(like=f'{station_id}_')
                data = pd.concat([data, refData.loc[:, f'{station_id}_{component}'].rename('Makelankatu')],axis=1)
        data_dict[component] = data
        
    
    
    figs = {}
    figs_D = {}

    for component, data in data_dict.items():
        figs[component] = plotlyplot_line(data)
        figs_D[component] = plotlyplot_bar(data.resample('D', label='left').mean())  
        
    
    divs = {}
    divs_D = {}
    for component, fig in figs.items():
        divs[component] = plotly.offline.plot(fig, show_link=False, output_type='div')
        
    for component, fig in figs_D.items():
        divs_D[component] = plotly.offline.plot(fig, show_link=False, output_type='div')
    
    pm10 = station_data.filter(like='pm10').shift(periods=-1, freq='H')
    pm10 = pm10.resample('D', label='left').mean().iloc[1:, :].round(1)
    pm10 = pm10.dropna(how='all', axis=1)
    data_columns = {'1_pm10': 'Leppavaara','3_pm10':'PM_Tikkurila' ,'4_pm10':'Mannerheimintie' ,'5_pm10': 'Kallio','6_pm10': 'Vartiokyla',
                '7_pm10': 'Luukki','8_pm10': 'Tikkurila','9_pm10': 'Lohja','10_pm10': 'Toolontulli','11_pm10': 'Matinkyla',
                '12_pm10': 'Ruskeasanta','13_pm10': 'Katajanokka','14_pm10': 'Hyvinkaa','17_pm10': 'Ammassuo 2','18_pm10': 'Makelankatu',
                '20_pm10': 'Blominmaki'}
    pm10.rename(columns=data_columns, inplace = True)
    pm10_div = plotly.offline.plot(plotlyplot_bar(pm10), show_link=False, output_type='div')
                 
                 
    if online:
        aika = datetime.datetime.today().strftime("%Y-%m-%d %H:%M")
        template = loadTemplate(template_folder, template_name)
        outputText = template.render(aika=aika, divs = divs, divs_D = divs_D, pm10_div=pm10_div, kartta=kartta)
    if not online:
        template = loadTemplate(template_folder, template_name)
        outputText = template.render(divs = divs, divs_D = divs_D, pm10_div=pm10_div)
        
    with open(savePath, 'w') as report:
        report.write(outputText)
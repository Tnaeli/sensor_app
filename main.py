# -*- coding: utf-8 -*-
"""
Created on Tue May  4 14:58:50 2021

@author: Taneli Mäkelä
"""
import pandas as pd
import datetime
import folium
import dbqueries
import airqualitymap
import html_report


def query_data_for_report(session, days, legend):
    date1 = (pd.Timestamp(datetime.datetime.now() - 
                          datetime.timedelta(days=days, 
                            hours=datetime.datetime.now().hour,
                              minutes=datetime.datetime.now().minute)))
    date2 = pd.Timestamp(datetime.datetime.now())
    
    sensors = pd.read_sql_table('Sensor', con=session.bind).set_index('id')
    components = ['no2', 'no', 'co', 'o3', 'pm10', 'pm25']
    
    sensorLocations = pd.read_sql_table('Location', con=session.bind).set_index('id')
    
    data_all = dbqueries.queryBetweenDates(session, sensors, sensorLocations, date1, date2, legend=legend)
    if data_all.empty:
        dataframe_empty = True
    else:

        data_all = dbqueries.applyCorrection(sensors, data_all, components)
        dataframe_empty = False
        
    return data_all, dataframe_empty

def generate_map(session, data_all, hours, ini, m):
    stationLocations = pd.read_csv(ini.loc['stations'][0], sep=';', header=0)
    stationLocations = stationLocations[stationLocations.Active == 1]
    
    table_data = data_all.loc[datetime.datetime.today() - 
                              datetime.timedelta(hours=hours): datetime.datetime.today(), :].copy()

    
    
    airqualitymap.sensorsToMap(session, table_data, m)
    airqualitymap.stationsToMap(stationLocations, m)
    airqualitymap.addEnfuserLayers(m)
    
    folium.LayerControl().add_to(m)
    m.save(ini.loc["mapSavepath"][0])
    


def Main():
    # Create connector for database based on ini-file
    # -------------------------------------------------------------------------
    ini_file = r"C:\Koodit\sensor_app\IniFile.csv"
    ini = pd.read_csv(ini_file, sep= '\t', index_col=0)
    session = dbqueries.createSession(ini)
    
    # Poll data from Vaisala API and insert to database
    # -------------------------------------------------------------------------
    dbqueries.updateDatabase(session)
    
    # Query data from database (data_all) for report and map
    # -------------------------------------------------------------------------
    
    days = 4 # Number of days from current time for report
    data_all, dataframe_empty = query_data_for_report(session, days, 'location')
    if dataframe_empty:
        print('No data found between given date range')
    else:
        # data_colocation = data_all[data_all.sensor_id.isin(['HSYS001', 'HSYS002', 'HSYS004'])].copy()
        data_all = data_all[data_all.sensor_id != 'Supersite']

        
        
        # Generate map and save to file
        # ---------------------------------------------------------------------
        number_of_hours = 8
        m = folium.Map(location=[60.210731, 24.929990], tiles='cartodbpositron', zoom_start=11)
        
        generate_map(session, data_all, number_of_hours, ini, m)
    
        # Generate HTML report and save to file
        # ---------------------------------------------------------------------
        html_report.createReport(data_all, ini.loc["report_online"][0], ini.loc["report_template_folder"][0], ini.loc["report_template"][0], 18, True)
        # html_report.createReport(data_all, ini.loc["report_offline"][0], None, False)
        # html_report.create_colocation_report(data_colocation, r"C:\Users\Taneli\Documents\sensor_app\colocrap.html", ini.loc["report_template_folder"][0], 'template_colocation_report.html', 18)
        
        
Main()
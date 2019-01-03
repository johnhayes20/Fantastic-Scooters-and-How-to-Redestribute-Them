import pandas as pd
import datetime
import numpy as np
import json
import ast
import matplotlib.pyplot as plt
import folium
import folium.plugins as plugins


def add_rounded_time(df, interval=15):
    '''
    Adds a column with the rounded time to the interval specified.
    
    '''
    df['time_of_day'] = pd.to_datetime(df['time_group_seconds'], unit='s').dt.round('15min')  

    df_time = pd.to_datetime(df['time_of_day'])

    df['time_of_day'] = (pd.to_datetime(df['date']) - datetime.datetime(1970,1,1)).dt.total_seconds() + df_time.dt.hour*3600+df_time.dt.minute*60 + df_time.dt.second
    
    return df


def drop_repeated_data(df):
    '''
    Removes repeated data based on id and time_group_seconds - this should cut the data down by more than half
    '''
    
    df.drop_duplicates(subset=['id','time_of_day'], keep='first', inplace=True)
    
    return df



def add_lat_long(df):
    
    df["location"] = df.location.str.replace("'", "\"").map( lambda x: json.loads(x) )
    
    df["latitude"] = df["location"].map( lambda x:x["latitude"] )
    df["longitude"] = df["location"].map( lambda x:x["longitude"] )
    
    df.drop(['location'], axis=1, inplace=True)

    df['latitude'] = df['latitude'].round(5)
    df['longitude'] = df['longitude'].round(5)
    
    return df


def add_day_of_week(df):
    
    df['date'] = pd.to_datetime(df['time_of_day'], unit='s').dt.date
    
    #df['date'] = pd.to_datetime(df['time_of_day'], unit='s').dt.round("D")
    df['day_of_week'] = pd.to_datetime(df['date']).dt.day_name()
    
    return df



def create_map(data, map_name):
    
    '''
    data - str: the file path to the csv
    map_name - str: name of the file you would like to save map html in
    
    '''
    
    
    
    
    
    df = pd.read_csv(data)
    df.drop(['code', 'captive', 'battery_level', 'location_group'], axis=1, inplace=True)
    df['time_group_seconds'] =(pd.to_datetime(df['time_group']) - datetime.datetime(1970,1,1)).dt.total_seconds()
    df['date'] = pd.to_datetime(df['time_group']).dt.date
    df = add_rounded_time(df) 
    df = drop_repeated_data(df)
    df = add_lat_long(df)
    df['count'] = 1
    df['grid_location'] = 0
    df = add_day_of_week(df)
    df = add_rounded_time(df)



    thurs_df = df[df['day_of_week'] == 'Thursday'].copy()

    latlon_list = []
    thurs_df['latlong'] = list(map(list, zip(thurs_df['latitude'], thurs_df['longitude'])))
    for i in range(len(thurs_df['time_of_day'].unique())):
        latlon_list.append(thurs_df[thurs_df['time_of_day'] == thurs_df['time_of_day'].unique()[i]]['latlong'].tolist())


    for i in range(21):
        latlon_list += [latlon_list.pop(0)]


    index_list = ['4:00am, ' + str(len(latlon_list[0])) + ' scooters', '4:15am, ' + str(len(latlon_list[1])) + ' scooters', '4:30am, ' + str(len(latlon_list[2])) + ' scooters', '4:45am, ' + str(len(latlon_list[3])) + ' scooters', '5:00am, ' + str(len(latlon_list[4])) + ' scooters', '5:15am, ' + str(len(latlon_list[5])) + ' scooters', '5:30am, ' + str(len(latlon_list[6])) + ' scooters', '5:45am, ' + str(len(latlon_list[7])) + ' scooters', '6:00am, ' + str(len(latlon_list[8])) + ' scooters', '6:15am, ' + str(len(latlon_list[9])) + ' scooters', '6:30am, ' + str(len(latlon_list[10])) + ' scooters', '6:45am, ' + str(len(latlon_list[11])) + ' scooters', '7:00am, ' + str(len(latlon_list[12])) + ' scooters', '7:15am, ' + str(len(latlon_list[13])) + ' scooters', '7:30am, ' + str(len(latlon_list[14])) + ' scooters', '7:45am, ' + str(len(latlon_list[15])) + ' scooters', '8:00am, ' + str(len(latlon_list[16])) + ' scooters', '8:15am, ' + str(len(latlon_list[17])) + ' scooters', '8:30am, ' + str(len(latlon_list[18])) + ' scooters', '8:45am, ' + str(len(latlon_list[19])) + ' scooters', '9:00am, ' + str(len(latlon_list[20])) + ' scooters', '9:15am, ' + str(len(latlon_list[21])) + ' scooters', '9:30am, ' + str(len(latlon_list[22])) + ' scooters', '9:45am, ' + str(len(latlon_list[23])) + ' scooters', '10:00am, ' + str(len(latlon_list[24])) + ' scooters', '10:15am, ' + str(len(latlon_list[25])) + ' scooters', '10:30am, ' + str(len(latlon_list[26])) + ' scooters', '10:45am, ' + str(len(latlon_list[27])) + ' scooters', '11:00am, ' + str(len(latlon_list[28])) + ' scooters', '11:15am, ' + str(len(latlon_list[29])) + ' scooters', '11:30am, ' + str(len(latlon_list[30])) + ' scooters', '11:45am, ' + str(len(latlon_list[31])) + ' scooters', '12:00pm, ' + str(len(latlon_list[32])) + ' scooters', '12:15pm, ' + str(len(latlon_list[33])) + ' scooters', '12:30pm, ' + str(len(latlon_list[34])) + ' scooters', '12:45pm, ' + str(len(latlon_list[35])) + ' scooters', '1:00pm, ' + str(len(latlon_list[36])) + ' scooters', '1:15pm, ' + str(len(latlon_list[37])) + ' scooters', '1:30pm, ' + str(len(latlon_list[38])) + ' scooters', '1:45pm, ' + str(len(latlon_list[39])) + ' scooters', '2:00pm, ' + str(len(latlon_list[40])) + ' scooters', '2:15pm, ' + str(len(latlon_list[41])) + ' scooters', '2:30pm, ' + str(len(latlon_list[42])) + ' scooters', '2:45pm, ' + str(len(latlon_list[43])) + ' scooters', '3:00pm, ' + str(len(latlon_list[44])) + ' scooters', '3:15pm, ' + str(len(latlon_list[45])) + ' scooters', '3:30pm, ' + str(len(latlon_list[46])) + ' scooters', '3:45pm, ' + str(len(latlon_list[47])) + ' scooters', '4:00pm, ' + str(len(latlon_list[48])) + ' scooters', '4:15pm, ' + str(len(latlon_list[49])) + ' scooters', '4:30pm, ' + str(len(latlon_list[50])) + ' scooters', '4:45pm, ' + str(len(latlon_list[51])) + ' scooters', '5:00pm, ' + str(len(latlon_list[52])) + ' scooters', '5:15pm, ' + str(len(latlon_list[53])) + ' scooters', '5:30pm, ' + str(len(latlon_list[54])) + ' scooters', '5:45pm, ' + str(len(latlon_list[55])) + ' scooters', '6:00pm, ' + str(len(latlon_list[56])) + ' scooters', '6:15pm, ' + str(len(latlon_list[57])) + ' scooters', '6:30pm, ' + str(len(latlon_list[58])) + ' scooters', '6:45pm, ' + str(len(latlon_list[59])) + ' scooters', '7:00pm, ' + str(len(latlon_list[60])) + ' scooters', '7:15pm, ' + str(len(latlon_list[61])) + ' scooters', '7:30pm, ' + str(len(latlon_list[62])) + ' scooters', '7:45pm, ' + str(len(latlon_list[63])) + ' scooters', '8:00pm, ' + str(len(latlon_list[64])) + ' scooters', '8:15pm, ' + str(len(latlon_list[65])) + ' scooters', '8:30pm, ' + str(len(latlon_list[66])) + ' scooters', '8:45pm, ' + str(len(latlon_list[67])) + ' scooters', '9:00pm, ' + str(len(latlon_list[68])) + ' scooters']




    m = folium.Map([37.8044, -122.2711], tiles='stamentoner', zoom_start=13)

    hm = plugins.HeatMapWithTime(latlon_list, index = index_list)

    hm.add_to(m)
    m.save(map_name)

create_map('bird_data-nov24.csv', 'scooters_heat_test.html')
    
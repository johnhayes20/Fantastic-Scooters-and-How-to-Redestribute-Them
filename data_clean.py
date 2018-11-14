import json
import ast
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import folium
from folium.plugins import MarkerCluster
import datetime

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import TimeSeriesSplit


def get_data():

    df = pd.read_csv('bird_data.csv')
    df.drop(['code', 'captive'], axis=1, inplace=True)

    temp_df = df.head(100)

    new_df = add_lat_long(temp_df)
    new_df['count'] = 1
    new_df['grid_location'] = 0
    new_df.drop(['location'], axis=1, inplace=True)
    return new_df


def add_lat_long(df):
    loc_array = df['location']
    
    loc_list= []
    for i in loc_array:
        loc_list.append(ast.literal_eval(i))
    
    df = pd.concat([df, pd.DataFrame(loc_list)], axis=1)
    df['latitude'] = df['latitude'].round(5)
    df['longitude'] = df['longitude'].round(5)
    return df


def get_geojson_grid(upper_right, lower_left, n=6):
    """Returns a grid of geojson rectangles, and computes the exposure in each section of the grid based on the vessel data.

    Parameters
    ----------
    upper_right: array_like
        The upper right hand corner of "grid of grids" (the default is the upper right hand [lat, lon] of the USA).

    lower_left: array_like
        The lower left hand corner of "grid of grids"  (the default is the lower left hand [lat, lon] of the USA).

    n: integer
        The number of rows/columns in the (n,n) grid.

    Returns
    -------

    list
        List of "geojson style" dictionary objects   
    """

    all_boxes = []

    lat_steps = np.linspace(lower_left[0], upper_right[0], n+1)
    lon_steps = np.linspace(lower_left[1], upper_right[1], n+1)

    lat_stride = lat_steps[1] - lat_steps[0]
    lon_stride = lon_steps[1] - lon_steps[0]

    for lat in lat_steps[:-1]:
        for lon in lon_steps[:-1]:
            # Define dimensions of box in grid
            upper_left = [lon, lat + lat_stride]
            upper_right = [lon + lon_stride, lat + lat_stride]
            lower_right = [lon + lon_stride, lat]
            lower_left = [lon, lat]

            # Define json coordinates for polygon
            coordinates = [
                upper_left,
                upper_right,
                lower_right,
                lower_left,
                upper_left
            ]

            geo_json = {"type": "FeatureCollection",
                        "properties":{
                            "lower_left": lower_left,
                            "upper_right": upper_right
                        },
                        "features":[]}

            grid_feature = {
                "type":"Feature",
                "geometry":{
                    "type":"Polygon",
                    "coordinates": [coordinates],
                }
            }

            geo_json["features"].append(grid_feature)

            all_boxes.append(geo_json)

    return all_boxes


def add_grid_location(df, n=42):
    
    '''
    
    Assigns each data point to a location on the grid according to its lat/long
    
    '''
    
    
    top_right = [df['latitude'].max(), df['longitude'].max()]
    top_left = [df['latitude'].min(), df['longitude'].min()]
    
    grid = get_geojson_grid(top_right, top_left, n=42)
    
    for i, box in enumerate(grid):
        upper_right = box["properties"]["upper_right"]
        lower_left = box["properties"]["lower_left"]
    
        mask = (
            (df.latitude <= upper_right[1]) & (df.latitude >= lower_left[1]) &
            (df.longitude <= upper_right[0]) & (df.longitude >= lower_left[0])
           )
    
        column_name = 'grid_location'
        df.loc[mask, column_name] = i
    
    return df




def add_time_chunk(df):
    df['time_chunk'] = 0
    for i, time in enumerate(df['time'].unique()):
        df['time_chunk'][df['time'] == time] = i
    return df



def add_day_of_week(df):
    df['date'] = pd.to_datetime(df['time']).dt.round("D")
    df['day_of_week'] = df['date'].dt.day_name()
    
    return df


def add_rounded_time(df, interval=15):
    '''
    Adds a column with the rounded time to the interval specified.
    
    '''
    df['rounded_time'] = pd.to_datetime(df['time']).dt.round('15min')  
    #df['rounded_time'] = pd.to_datetime(df['time']).dt.round("Min").apply(lambda dt: datetime.datetime(dt.year, dt.month, dt.day, dt.hour,15*round((float(dt.minute) + float(dt.second)/60) / interval)))
    #df['rounded_time'] = pd.Series([val.time() for val in df['rounded_time']])
    
    df_time = pd.to_datetime(df["rounded_time"])

    df['rounded_time'] = df_time.dt.hour*60+df_time.dt.minute*60 + df_time.dt.second
    
    
    return df



def add_wait_time(df):
    '''
    Adds a column that tells how long a scooter has been waiting in a location
    
    '''
    final_df = pd.DataFrame()
    for i in range(len(df['id'].unique())):
        
        # set this df to all the data points with the same id
        temp_df = df[df['id'] == df['id'].unique()[i]]
        
        
        for j in range(len(temp_df['latitude'].unique())):
            
            # set this df to iterate through all of the unique lats from the temp data set
            same_lat_long_df = temp_df[temp_df['latitude'] == temp_df['latitude'].iloc[j]]
        
            # create new column 'wait_time' that is the difference in time between the first and last datapoints
            same_lat_long_df['wait_time'] = pd.to_datetime(same_lat_long_df['time']).iloc[-1] - pd.to_datetime(same_lat_long_df['time']).iloc[0]
            
            #append the new column to the output df
            final_df = final_df.append(same_lat_long_df)
    
    return final_df





def drop_repeated_data(df):
    '''
    Removes repeated data based on id and rounded_time - this should cut the data down by more than half
    '''
    
    df.drop_duplicates(subset=['id','rounded_time'], keep='first', inplace=True)
    return df


df = get_data()
df = add_day_of_week(df)
df = add_grid_location(df)
df = add_rounded_time(df)
df = add_wait_time(df)
df = drop_repeated_data(df)


def grid_count(df, n=42):
    '''
    For a given time, day of the week create df of number of scooters in each grid location
    '''
    
    new_df = pd.DataFrame()
    for unique_date in df['date'].unique():
        for unique_rounded_time in df['rounded_time'].unique():
            for unique_grid_location in range(n**2):
                if ((df['date'] == unique_date) & (df['rounded_time'] == unique_rounded_time) & (df['grid_location'] == unique_grid_location)).any():
                    continue
                else:
                    #print (unique_grid_location)
                    new_df = new_df.append({'rounded_time':unique_rounded_time, 'grid_location':unique_grid_location, 'date':unique_date}, ignore_index=True)
    new_df['grid_location'] = new_df['grid_location'].astype(int)                
    
    df3 = pd.concat([df,new_df])
    df3 = df3.fillna(0)
    df3 = df3.sort_values(by='grid_location')
    #for a given date and rounded time - check to see if there is a grid location, if not set count to 0.
    
    #df3 = df3.groupby(['rounded_time', 'grid_location', 'day_of_week', 'date']).size().reset_index(name='counts')
    #df = df.groupby(['grid_location']).agg(['count'])
    return df3



new_df = grid_count(df)
new_df
#df3 = pd.concat([df,new_df])
#df3.drop_duplicates(subset=['grid_location', 'col3'], inplace=True, keep='last')
new_df = new_df.groupby(['rounded_time', 'grid_location', 'date'], as_index=False)[['count']].sum()



def MMVP(df):
    '''
    even more mvp than mvp
    '''
    
    y = df['count']
    X = df.drop('count', axis=1)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, shuffle=False)
    
    
    linreg=LinearRegression()
    linreg.fit(X_train, y_train)
    
    y_pred = linreg.predict(X_test).reshape(-1,1)
    y_test = np.array(y_test).reshape(-1,1)
    
    #print(y_pred - y_test)
    #print (np.shape(y_pred), np.shape(y_test))
    
    return linreg.score(y_pred, y_test)


xdf = new_df.drop(['date'], axis=1)

MMVP(xdf)
import json
import ast
import pandas as pd
import numpy as np
import datetime

def get_data(n=40000):
    '''
    Gets data from a csv and cleans it
    
    '''
    
    
    df = pd.read_csv('bird_data-nov24.csv')
    df.drop(['code', 'captive', 'battery_level', 'location_group'], axis=1, inplace=True)
    print('date read in')
    #For testing so that everything will run quickly
    #df = df.head(n)
    
    #Remove repeated data
    df['time_group_seconds'] =(pd.to_datetime(df['time_group']) - datetime.datetime(1970,1,1)).dt.total_seconds()
    df['date'] = pd.to_datetime(df['time_group']).dt.date
    df = add_rounded_time(df) 
    df = drop_repeated_data(df)
    print('data dropped')
    #Add columns for lat, long, count, and grid_location
    
    df = add_lat_long(df)
    df['count'] = 1
    df['grid_location'] = 0

    
    #Applies a location based on a grid over Oakland to each scooter
    df = add_grid_location(df)
    #og_df = df
    #og_df = add_day_of_week(og_df)
    #og_df = add_rounded_time(og_df)
    
    #Reforms dataframe to calculate count of scooters in each grid location every 15 min
    df = grid_count(df)
    
    #add id list and day of week
    new_df = add_id_list(df, og_df)
    new_df = add_day_of_week(new_df)
    
    new_df = add_idle_and_turnover(new_df)
    
    return new_df#, og_df

def add_lat_long(df):
    
    df["location"] = df.location.str.replace("'", "\"").map( lambda x: json.loads(x) )
    
    df["latitude"] = df["location"].map( lambda x:x["latitude"] )
    df["longitude"] = df["location"].map( lambda x:x["longitude"] )
    
    df.drop(['location'], axis=1, inplace=True)

    df['latitude'] = df['latitude'].round(5)
    df['longitude'] = df['longitude'].round(5)
    
    return df

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

def add_grid_location(df, n=42):
    
    '''
    Assigns each data point to a location on the grid according to its lat/long
    '''
    
    top_right = [df['latitude'].max(), df['longitude'].max()]
    top_left = [df['latitude'].min(), df['longitude'].min()]
    
    grid = get_geojson_grid(top_right, top_left, n)
    
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

def grid_count(df, n=42):
    '''
    For a given time, day of the week create df of number of scooters in each grid location
    '''
    
    #COMBINE UNIQUE DATE AND UNIQUE ROUNDED TIME INTO 1 LOOP INSTEAD OF 2
    
    new_df = pd.DataFrame()
    for unique_rounded_time in df['time_of_day'].unique():
        for unique_grid_location in range(n**2):
            if ((df['time_of_day'] == unique_rounded_time) & (df['grid_location'] == unique_grid_location)).any():
                continue
            else:
                new_df = new_df.append({'time_of_day':unique_rounded_time, 'grid_location':unique_grid_location}, ignore_index=True)
    new_df['grid_location'] = new_df['grid_location'].astype(int)                
    
    df = df.groupby(['time_of_day', 'grid_location']).size().reset_index(name='counts')
    df3 = pd.concat([df,new_df], sort=False)
    df3.fillna(value=0, inplace=True)
    df3.sort_values(by=['grid_location', 'time_of_day'], inplace=True)
    #for a given date and rounded time - check to see if there is a grid location, if not set count to 0.
    
    #df = df.groupby(['grid_location']).agg(['count'])
    return df3

def add_day_of_week(df):
    
    df['date'] = pd.to_datetime(df['time_of_day'], unit='s').dt.date
    
    #df['date'] = pd.to_datetime(df['time_of_day'], unit='s').dt.round("D")
    df['day_of_week'] = pd.to_datetime(df['date']).dt.day_name()
    
    
    return df

def add_id_list(df, og_df):

    g = og_df.groupby(['grid_location', 'time_of_day'])['id'].apply(list).reset_index(name='id_list')

    merger_df = pd.merge(df, g, on=['grid_location', 'time_of_day'], how='outer')
    
    isnull = merger_df.id_list.isnull()

    merger_df.loc[isnull, 'id_list'] = [ [[]] * isnull.sum() ]
    
    return merger_df

def add_idle_and_turnover(merger_df):
    
    group1_master = pd.DataFrame()
    group2_master = pd.DataFrame()
    for grid_location in merger_df['grid_location'].unique():
        
        group1 = merger_df[merger_df['grid_location']==grid_location].iloc[:-1]
        group1.reset_index(inplace=True)
        group1_master = group1_master.append(group1, ignore_index=True)
        
        group2 = merger_df[merger_df['grid_location']==grid_location].iloc[1:]
        group2.reset_index(inplace=True)
        group2_master = group2_master.append(group2, ignore_index=True)

    df_id_list = group1_master.merge(group2_master, how='outer', left_index=True, right_index=True)
    
    df_id_list['idle'] = df_id_list.apply(lambda x: [i for i in x['id_list_x'] if i.lower() in x['id_list_y']], axis=1)
    
    df_id_list['turn_over'] = df_id_list.apply(lambda x: [i for i in x['id_list_y'] if i.lower() not in x['id_list_x']], axis=1)
    
    df_id_list['num_idle_15min'] = df_id_list['idle'].str.len()
    df_id_list['num_turn_over_15min'] = df_id_list['turn_over'].str.len()
    
    
    df_id_list['time'] = df_id_list['time_of_day_y'] - (pd.to_datetime(df_id_list['date_y']) - datetime.datetime(1970,1,1)).dt.total_seconds()
    
    df_id_list.drop(['index_x','time_of_day_x','grid_location_x','counts_x', 'id_list_x', 'date_x', 'day_of_week_x'], axis=1, inplace=True)
    df_id_list = df_id_list.rename(index=str, columns={"time_of_day_y": "time_of_day", "grid_location_y":"grid_location", "counts_y":"counts", "id_list_y":"id_list", "date_y":"date", "day_of_week_y":"day_of_week"})
    
    df_id_list = pd.concat([df_id_list, pd.get_dummies(df_id_list['day_of_week'])], axis=1)
    df_id_list.drop(['index_y','day_of_week','date','id_list','idle', 'turn_over'], axis =1, inplace=True)
    
    return df_id_list

df, og_df = get_data()





from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import TimeSeriesSplit
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import recall_score




def MVP(df):
    '''
    even more mvp than mvp
    '''
    
    y = df['counts']
    X = df.drop('counts', axis=1)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, shuffle=False)
    
    
    linreg=LinearRegression()
    linreg.fit(X_train, y_train)
    
    y_pred = linreg.predict(X_test).reshape(-1,1)
    y_test = np.array(y_test).reshape(-1,1)
    
    #print(y_pred - y_test)
    #print (np.shape(y_pred), np.shape(y_test))
    
    #print(recall_score(y_test, y_pred))
    
    #print(y_pred)
    print(linreg.coef_)
    
    return linreg.score(X_test, y_test)



df, og_df = get_data()
MVP(df)
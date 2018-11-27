import json
import ast
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import folium
from folium.plugins import MarkerCluster






scooter_df = pd.read_csv('individual_scooter_data.csv')
scooter_df.drop(['Unnamed: 0'], axis=1, inplace=True)
new_df = scooter_df[scooter_df['time_group_seconds']==scooter_df['time_group_seconds'].unique()[0]]



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





def add_lat_long(df):
    
    df["location"] = df.location.str.replace("'", "\"").map( lambda x: json.loads(x) )
    
    df["latitude"] = df["location"].map( lambda x:x["latitude"] )
    df["longitude"] = df["location"].map( lambda x:x["longitude"] )
    
    df.drop(['location'], axis=1, inplace=True)

    df['latitude'] = df['latitude'].round(5)
    df['longitude'] = df['longitude'].round(5)
    
    return df





def map():
    m = folium.Map(zoom_start = 13, location=[37.808136, -122.256303])

    # Generate GeoJson grid
    top_right = [new_df['latitude'].max(), new_df['longitude'].max()]
    top_left = [new_df['latitude'].min(), new_df['longitude'].min()]


    grid = get_geojson_grid(top_right, top_left, n=42)

    # Calculate exposures in grid
    popups = []
    regional_counts = []
    total_on_map = 0
    for i, box in enumerate(grid):
        upper_right = box["properties"]["upper_right"]
        lower_left = box["properties"]["lower_left"]

        mask = (
                (new_df.latitude <= upper_right[1]) & (new_df.latitude >= lower_left[1]) &
                (new_df.longitude <= upper_right[0]) & (new_df.longitude >= lower_left[0])
               )

        region_incidents = len(new_df[mask])
        regional_counts.append(region_incidents)

        total_vehicles = new_df[mask]['count'].sum()
        #total_casualties = accident_data[mask].Number_of_Casualties.sum()
        content = "scooters {:,.0f}".format(total_vehicles)
        popup = folium.Popup(content)
        popups.append(popup)

        column_name = 'grid_location'
        new_df.loc[mask, column_name] = i

        total_on_map += total_vehicles
    worst_region = max(regional_counts)

    # Add GeoJson to map
    for i, box in enumerate(grid):
        geo_json = json.dumps(box)

        color = plt.cm.BuPu(regional_counts[i] / (.1*worst_region))
        color = mpl.colors.to_hex(color)

        gj = folium.GeoJson(geo_json,
                            style_function=lambda feature, color=color: {
                                                                            'fillColor': color,
                                                                            'color':"black",
                                                                            'weight': .5,
                                                                            'dashArray': '5, 5',
                                                                            'fillOpacity': .5,
                                                                            'line_width': 0,
                                                                            'line_opacity': 0,
                                                                        })
        gj.add_child(popups[i])
        m.add_child(gj)

    # Marker clusters
    locations = list(zip(new_df.latitude, new_df.longitude))
    icons = [folium.Icon(icon="car", prefix="fa") for _ in range(len(locations))]

    # Create popups
    popup_content = []
    # for incident in accident_data.itertuples():
    #     number_of_vehicles = "Number of vehicles: {} ".format(incident.Number_of_Vehicles)
    #     number_of_casualties = "Number of casualties: {}".format(incident.Number_of_Casualties)
    #     content = number_of_vehicles + number_of_casualties
    #     popup_content.append(content)

    popups = [folium.Popup(content) for content in popup_content]

    cluster = MarkerCluster(locations=locations, icons=icons, popups=popups)
    m.add_child(cluster)

    m.save("scooters3.html")
    print (total_on_map)

map()
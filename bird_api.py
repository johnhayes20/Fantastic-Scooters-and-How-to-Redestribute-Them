import requests
import uuid
import json
import pandas as pd
import numpy as np
import datetime
from time import sleep


def access_bird_api():
    
    #Oakland center latitude
    lat = 37.808136
    #Oakland center longitude
    lon = -122.256303
    #width of squares
    r = 0.0155
    lat_long = np.array([[lat+(2*r), lon+(-2.5*r)], [lat+(2*r), lon+(-1.5*r)], [lat+(2*r), lon+(-.5*r)], [lat+(2*r), lon+(.5*r)], [lat+(2*r), lon+(1.5*r)], [lat+(2*r), lon+(2.5*r)],
                     [lat+(1*r), lon+(-2.5*r)], [lat+(1*r), lon+(-1.5*r)], [lat+(1*r), lon+(-.5*r)], [lat+(1*r), lon+(.5*r)], [lat+(1*r), lon+(1.5*r)], [lat+(1*r), lon+(2.5*r)],
                     [lat+(0*r), lon+(-2.5*r)], [lat+(0*r), lon+(-1.5*r)], [lat+(0*r), lon+(-.5*r)], [lat+(0*r), lon+(.5*r)], [lat+(0*r), lon+(1.5*r)], [lat+(0*r), lon+(2.5*r)],
                     [lat+(-1*r), lon+(-2.5*r)], [lat+(-1*r), lon+(-1.5*r)], [lat+(-1*r), lon+(-.5*r)], [lat+(-1*r), lon+(.5*r)], [lat+(-1*r), lon+(1.5*r)], [lat+(-1*r), lon+(2.5*r)],
                     [lat+(-2*r), lon+(-2.5*r)], [lat+(-2*r), lon+(-1.5*r)], [lat+(-2*r), lon+(-.5*r)], [lat+(-2*r), lon+(.5*r)], [lat+(-2*r), lon+(1.5*r)], [lat+(-2*r), lon+(2.5*r)]])

    #randomly generated number used in requests.get
    device_id = str(uuid.uuid4())
    
    #Open token.txt to grab api access token
    token_file = open('token.txt', 'r')
    token = 'Bird ' + token_file.readlines()[0]
    
    # first time, write with header
    g = requests.get(url= 'https://api.bird.co/bird/nearby?latitude='+str(lat_long[0][0])+'&longitude='+str(lat_long[0][1])+'&radius=1000',
                    headers= {'authorization': token, 'device-id':device_id, 'app-version':'4.7.3.1', 'location': '{"latitude":'+str(lat_long[0][0])+',"longitude":'+str(lat_long[0][1])+'}', 'radius':'1000'}
                    )

    #Add time column
    now = str(datetime.datetime.now())
    time_group = str(datetime.datetime.now())
    data = g.json()
    for j in range(len(data['birds'])):
        data['birds'][j]['time'] = now
        data['birds'][j]['time_group'] = time_group
        data['birds'][j]['location_group'] = 0

    bird_df = pd.DataFrame.from_records(data['birds'])
    with open('bird_data16.csv', mode='a') as f:
        f.write(bird_df.to_csv(header=True, index=False))
    
    
    # first time, write the next 29 without header 
    for i in range(len(lat_long)):
            sleep(15)
            if i == 0:
                continue
            g = requests.get(url= 'https://api.bird.co/bird/nearby?latitude='+str(lat_long[i][0])+'&longitude='+str(lat_long[i][1])+'&radius=1000',
                            headers= {'authorization': token, 'device-id':device_id, 'app-version':'4.7.3.1', 'location': '{"latitude":'+str(lat_long[i][0])+',"longitude":'+str(lat_long[i][1])+'}', 'radius':'1000'}
                            )

            #Add time column
            now = str(datetime.datetime.now())
            data = g.json()
            for j in range(len(data['birds'])):
                data['birds'][j]['time'] = now
                data['birds'][j]['time_group'] = time_group
                data['birds'][j]['location_group'] = i

            bird_df = pd.DataFrame.from_records(data['birds'])
            with open('bird_data16.csv', mode='a') as f:
                f.write(bird_df.to_csv(header=False, index=False))
            print ('location {} of the grid was written according to {} time group'.format(i, time_group))
    
    
    # main function, write without header
    while True:
        time_group = str(datetime.datetime.now())
        for i in range(len(lat_long)):
            sleep(15)
            g = requests.get(url= 'https://api.bird.co/bird/nearby?latitude='+str(lat_long[i][0])+'&longitude='+str(lat_long[i][1])+'&radius=1000',
                            headers= {'authorization': token, 'device-id':device_id, 'app-version':'4.7.3.1', 'location': '{"latitude":'+str(lat_long[i][0])+',"longitude":'+str(lat_long[i][1])+'}', 'radius':'1000'}
                            )

            #Add time column
            now = str(datetime.datetime.now())
            data = g.json()
            for j in range(len(data['birds'])):
                data['birds'][j]['time'] = now
                data['birds'][j]['time_group'] = time_group
                data['birds'][j]['location_group'] = i

            bird_df = pd.DataFrame.from_records(data['birds'])
            with open('bird_data16.csv', mode='a') as f:
                f.write(bird_df.to_csv(header=False, index=False))
            print ('location {} of the grid was written according to {} time group'.format(i, time_group))
        
access_bird_api()
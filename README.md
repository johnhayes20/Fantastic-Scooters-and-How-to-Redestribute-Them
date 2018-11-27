# Fantastic Scooters and Where to Redestribute Them
#### Powered Shared Scooter Location Prediction and Redistribution

### How to use this code:
- First you will need to edit the bird_api.py file to use your email address and access token. To get an access token use the following function:

INSERT GET REQUEST HERE

- Be sure to store your Bird access token in a .txt file the first time you run this code. Every time you ping the API your access token is renewed, not recreated.

- Once you have editedd the bird_api.py file with your information you will need to specify the lat and long in that file of where you would like the center of your API ping to be. The API will only return the scooters in a predetermined area around that location. If you want more than that use the for loop in bird_api.py, but be sure not to request access too often.

Mapping:
- If you want to make a map of your data stored in the csv, first run it through data_clean.py and then through map.py. This will require you to have a couple of libraries. You will need to pip install folium.








#### Sources: 



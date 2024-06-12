#!/usr/bin/env python

import requests
import numpy as np
import pandas as pd
from datetime import datetime, date

r=requests.get('https://api.openweathermap.org/data/2.5/onecall?lat=LATITUDE&lon=LONGITUDE&exclude=minutely,daily&appid=APIKEY')
data=r.json()

sunrise=str(datetime.fromtimestamp(data["current"]["sunrise"]).time())
sunset=str(datetime.fromtimestamp(data["current"]["sunset"]).time())
print("sunrise:"+sunrise+"  sunset:"+sunset)

hourly=np.array(data['hourly'])[:24]

times=[datetime.fromtimestamp(hour["dt"]).time() for hour in hourly]
temps=[round(hour["temp"]-273.15) for hour in hourly]
feels_likes=[round(hour["feels_like"]-273.15) for hour in hourly]
descs=[hour["weather"][0]['description'] for hour in hourly]
weather=pd.DataFrame(list(zip(times,temps,feels_likes,descs)),columns=["Time","Temp","Feels","Description"])

print(weather.to_string(index=False)+"\n")
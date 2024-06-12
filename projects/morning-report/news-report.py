#!/usr/bin/env python
# coding: utf-8

import feedparser
from datetime import datetime, date
from time import mktime
import requests
import numpy as np

urls=#LIST OF RSS FEED URLS

feeds=[]
for url in urls:
    feeds.append(feedparser.parse(url))

now=datetime.now()
for d in feeds:
    entries=[]
    for entry in d['entries']:
        ts=entry['published_parsed']
        #print(ts)
        delta=now-datetime.fromtimestamp(mktime(ts))
        days=delta.total_seconds()/60/60/24
        if(days<1):
            entries.append(entry['title'].replace('&#039;', "'"))
    if entries:
        print(d['feed']['title']+"---------------------------")
        for entry in entries:
            print(entry)

print("rockets:-----------------")
r=requests.get('https://fdo.rocketlaunch.live/json/launches/next/5')
data=np.array(r.json()['result'])[:2]
for launch in data:
    date=str(datetime.fromtimestamp(int(launch['sort_date'])))
    provider=launch['provider']['name']
    vehicle=launch['vehicle']['name']
    mission=launch['missions'][0]['name']
    print(date+": "+provider+" "+vehicle+". "+launch['missions'][0]['name'])

print("\x1BJ\xD8\x1BJ\xD8\x1BJ\x6C")
#!/usr/bin/env python
# coding: utf-8


from pyexcel_ods import get_data
import numpy as np
import pandas as pd
from datetime import datetime, date
from pytz import timezone
from icalendar import Calendar, Event
import requests
import recurring_ical_events
import calendar

current=datetime.now(timezone('UTC'))
print(str(current.date())+", "+calendar.day_name[current.weekday()]+"\n")

r=requests.get("[log url]")
with open("logv2.ods","wb") as f:
    f.write(r.content)

spread=get_data("logv2.ods")

data=spread['Sheet1']

columns=["D","WD","startutc","startlocal","activity","detail","people","super","spent","","subplace","place","city","country","spentint"]

df=pd.DataFrame(data,columns=columns)
df.drop([0],inplace=True)
df.drop([""],axis=1,inplace=True)
df.reset_index(inplace=True,drop=True)
df.drop(df.tail(2).index, inplace = True) #drop last 2 rows

df['activity'].replace('', np.nan, inplace=True)
df.dropna(subset=['activity'], inplace=True)

def get_n(threshold):
    length=len(df["startutc"])
    n=min(threshold*120,length-2)
    delta=df["startutc"][length-1]-df["startutc"][length-n]
    days=delta.total_seconds()/3600/24
    while(days>=threshold):
        n-=1
        delta=df["startutc"][length-1]-df["startutc"][length-n]
        days=delta.total_seconds()/3600/24
    return n

labels=["productive","fun","routine","waste"]
filters=[{LIST OF PRODUCTIVE STRINGS},
         {LIST OF FUN STRINGS},
         {LIST OF ROUTINE STRINGS},
         {LIST OF WASTE STRINGS}]

def get_times(n):
    i=n
    total=0
    times=np.zeros(4)
    total=0
    length=len(df["startutc"])
    for i in range(2,n+1):
        activity=df["activity"][length-i]
        time=df["spentint"][length-i]
        if activity != "sleep":
            total+=time
        for j in range (0, len(labels)):
            if activity in filters[j]:
                times[j]+=time

    times=times/total
    times=[round(t,3) for t in times]
#     for i in range(0,len(times)):
#         times[i]=round(times[i],3)
    return times

def output_times(days, timess):
    df=pd.DataFrame(timess.T,columns=days,index=labels)
    df.columns.name='past days'
    print(df)

def print_times(dayss):
    timess=[]
    for days in dayss:
        timess.append(get_times(get_n(days)))
    output_times(dayss,np.array(timess))

print_times([1,7,30,365,df['D'].iloc[-1]])

# # CAL

r=requests.get("[webDAV calendar URL]")
with open("cal.ics","wb") as f:
    f.write(r.content)


cal=Calendar.from_ical(open("cal.ics","rb").read())

recurring = recurring_ical_events.of(cal).at(date.today())
def eventcompare(e):
    return e["DTSTART"].dt
recurring.sort(key=eventcompare)

print("\nCALENDAR")
for component in recurring:
    start=component["DTSTART"].dt.time()
    end=component["DTEND"].dt.time()
    print(str(start)+"-"+str(end)+" "+component["SUMMARY"])
    
print("\nTODO")
def todocompare(e):
    return e["DUE"].dt
eventsort=[e for e in cal.walk() if e.name=="VTODO" and e["STATUS"]!="COMPLETED"]
eventsort.sort(key=todocompare)
for component in eventsort:
    if component.name=="VTODO" and component["STATUS"]!="COMPLETED":
        #print(component)
        dt=component["DUE"].dt
        print(str(dt.date())+" "+str(dt.time())+" "+component["SUMMARY"])
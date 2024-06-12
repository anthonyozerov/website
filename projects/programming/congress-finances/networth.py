#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import requests

r=requests.get("https://www.opensecrets.org/personal-finances/top-net-worth")
df=pd.DataFrame(pd.read_html(r.text)[0])

df["Average"] = df["Average"].replace('[\$,]', '', regex=True).astype(float)

dem=df[df['Name'].str.contains("D-")]
rep=df[df['Name'].str.contains("R-")]


print("Median for Democrat members of Congress:   $"+str(dem["Average"].median()))
print("Median for Republican members of Congress: $"+str(rep["Average"].median()))


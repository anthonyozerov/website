import requests
headers = {'Authorization': 'Bearer shr_o69HxjQ0BYrY2FPD9HxdirhJYcFDCeRolEd744Uj88e'}
url = 'https://api.density.io/v2/spaces/spc_863128347956216317/count'
count = requests.get(url, headers=headers).json()['count']
print(count)
# write current time (pacific time zone) and count to a file
from datetime import datetime
from pytz import timezone
with open('weightroom.csv', 'a') as f:
    dt = datetime.now().astimezone(timezone('US/Pacific')).strftime('%Y-%m-%d %H:%M:%S')
    f.write(f'{dt},{count}\n')

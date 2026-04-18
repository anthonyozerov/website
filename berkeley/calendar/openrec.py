from bs4 import BeautifulSoup
from datetime import datetime
import requests
from yaml import safe_load
from utils import parse_time_recwell, create_event, save_cal

with open('openrec.yaml', 'r') as config_file:
    sports = safe_load(config_file)

print(list(sports.keys()))

for name, sport in sports.items():
    print(name)
    try:
        html_content = requests.get(sport['url']).text
        soup = BeautifulSoup(html_content, 'html.parser')

        table = soup.find('table', class_='table')
        if not table:
            print(f'  No table found for {name}')
            continue

        cal_events = []
        for row in table.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) < 4:
                continue

            date_str = cells[0].get_text(strip=True)
            try:
                event_date = datetime.strptime(date_str, '%m/%d/%Y')
            except ValueError:
                print(f'  Could not parse date: {date_str}')
                continue

            times = [p.get_text(strip=True) for p in cells[2].find_all('p')]
            locations = [p.get_text(strip=True) for p in cells[3].find_all('p')]

            if not times:
                times = [cells[2].get_text(strip=True)]
            if not locations:
                locations = [cells[3].get_text(strip=True)]

            for i, time_str in enumerate(times):
                location = locations[i] if i < len(locations) else ''

                if 'exclude' in sport:
                    combined = (time_str + ' ' + location).lower()
                    if any(excl in combined for excl in sport['exclude']):
                        continue

                result = parse_time_recwell(event_date, time_str)
                if result is None:
                    print(f'  Skipping: {time_str}')
                    continue

                start_time, end_time = result
                cal_events.append(create_event(sport['name'], start_time, end_time, location, 'America/Los_Angeles'))

        print(f'  {len(cal_events)} events')
        save_cal(cal_events, name, sport['name'])
    except Exception as e:
        print(f'  ERROR: {e}')

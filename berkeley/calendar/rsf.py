import requests
from bs4 import BeautifulSoup
from utils import assign_year, parse_time, create_event, save_cal
from datetime import datetime

url = 'https://events.berkeley.edu/live/widget/33'
html_content = requests.get(url).text

soup = BeautifulSoup(html_content, 'html.parser')

cal_events = []

# Find all rows in the table
rows = soup.find_all('tr')

# Loop through each row to extract the data from the two columns
for row in rows:
    cols = row.find_all('td')  # Find all td elements (table cells)
    if len(cols) == 2:  # Ensure the row has two columns
        day = cols[0].text.strip()
        time = cols[1].text.strip()

        # Convert day header into date format
        try:
            event_date = datetime.strptime(day, '%A, %b. %d')
        except ValueError:
            event_date = datetime.strptime(day, '%A, %B %d')

        event_date = assign_year(event_date)

        start_time, end_time = parse_time(event_date, time)
        event = create_event('RSF Open', start_time, end_time, 'RSF', 'America/Los_Angeles')

        cal_events.append(event)

save_cal(cal_events, 'rsf', 'RSF Open')
from bs4 import BeautifulSoup
from datetime import datetime
import requests
from yaml import safe_load
from utils import assign_year, parse_time, create_event, save_cal

# Load configuration from YAML file
with open('openrec.yaml', 'r') as config_file:
    sports = safe_load(config_file)

print(sports.keys())

for name, sport in sports.items():
    print(name)
    html_content = requests.get(sport['url']).text

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')


    # Function to parse time strings into 24-hour format time tuples

    cal_events = []
    # Extract events from HTML
    for event_day in soup.find_all('div', class_='lw_events_day'):
        day_header = event_day.find('h4', class_='lw_events_header_date').text.strip()
        print(day_header)

        # Convert day header into date format (assuming event days are in December 2024)
        event_date = datetime.strptime(day_header, '%A, %b. %d')# .replace(year=datetime.now().year)
        # set the year to the closest year now for the date, dealing with the issue of december and january
        event_date = assign_year(event_date)

        print(event_date)

        # Process each event within the day
        events = event_day.find_all('div', class_='event row')
        for event in events:
            time_text = event.find('div', class_='time column').text.strip()
            location_text = event.find('div', class_='location column').text.strip()
            event_title = event.find('div', class_='event-title column').text.strip()

            # if the title contains anything in sport['exclude'], skip it
            if 'exclude' in sport:
                if any([excl in event_title.lower() for excl in sport['exclude']]):
                    continue

            event_title = event_title.replace('Event: ', '')
            location_text = location_text.replace('Location: ', '')

            print(time_text)

            # Parse time and location
            start_time, end_time = parse_time(event_date, time_text)
            # make calendar event
            event = create_event(event_title, start_time, end_time, location_text, 'America/Los_Angeles')

            # Add event to calendar
            cal_events.append(event)

    save_cal(cal_events, name, sport['name'])
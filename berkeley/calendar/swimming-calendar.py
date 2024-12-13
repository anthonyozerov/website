from bs4 import BeautifulSoup
from ics import Calendar, Event
from datetime import datetime
from dateutil.tz import gettz
import pytz
import requests

html_content = requests.get('https://events.berkeley.edu/live/widget/15/tag/Open Rec Swimming').text

# Parse the HTML content using BeautifulSoup
soup = BeautifulSoup(html_content, 'html.parser')

# Create a new calendar
calendar = Calendar()

# Function to parse time strings into 24-hour format time tuples
def parse_time(event_day, time_str):
    """Parse a time string like '4 - 9 p.m.' into a tuple of start and end times in 24-hour format"""

    time_str = time_str.lower().replace('time:', '').strip()
    time_parts = time_str.strip().split(' - ')
    start_time, end_time = time_parts[0], time_parts[1]
    end_pm = 'p.m.' in end_time
    if 'a.m.' in start_time:
        start_pm = False
    elif 'a.m.' not in start_time and end_pm:
        start_pm = True
    elif 'a.m.' not in start_time and not end_pm:
        start_pm = False

    def convert_to_24hr(ts, pm):
        print(ts, pm)
        if ts == 'noon':
            return 12, 0
        ts = ts.replace('a.m.', '').replace('p.m.', '').strip()
        if ':' in ts:
            hour, minute = map(int, ts.split(':'))
        else:
            hour = int(ts)
            minute = 0
        if pm:
            if hour != 12:
                hour += 12
        print(hour, minute)
        return hour, minute

    start_hour, start_minute = convert_to_24hr(start_time, start_pm)
    end_hour, end_minute = convert_to_24hr(end_time, end_pm)

    start_datetime = datetime(event_day.year, event_day.month, event_day.day, start_hour, start_minute, 0)
    end_datetime = datetime(event_day.year, event_day.month, event_day.day, end_hour, end_minute, 0)

    return start_datetime, end_datetime

cal_events = []
# Extract events from HTML
for event_day in soup.find_all('div', class_='lw_events_day'):
    day_header = event_day.find('h4', class_='lw_events_header_date').text.strip()
    print(day_header)

    # Convert day header into date format (assuming event days are in December 2024)
    event_date = datetime.strptime(day_header, '%A, %b. %d').replace(year=datetime.now().year)
    print(event_date)

    # Process each event within the day
    events = event_day.find_all('div', class_='event row')
    for event in events:
        time_text = event.find('div', class_='time column').text.strip()
        location_text = event.find('div', class_='location column').text.strip()
        event_title = event.find('div', class_='event-title column').text.strip()
        if 'no open rec swim' in event_title.lower():
            continue
        event_title = event_title.replace('Event: ', '')

        print(time_text)

        # Parse time and location
        start_time, end_time = parse_time(event_date, time_text)
        # make sure datetimes are Pacific WITHOUT shifting the time
        pt = gettz('America/Los_Angeles')
        start_time = start_time.replace(tzinfo=pt)
        end_time = end_time.replace(tzinfo=pt)
        print(pt)
        print(start_time, end_time)

        event_location = location_text

        # Create an iCalendar event
        event = Event(dtstamp=start_time)
        event.summary = event_title
        event.begin = start_time
        event.end = end_time
        print(event)
        event.location = event_location

        # Add event to calendar
        cal_events.append(event)

# Save the calendar to an ICS file

calendar = Calendar(events=cal_events)

cal_string = str(calendar.serialize())
with open('lapswim.ics', 'w') as ics_file:
    ics_file.write(cal_string)

exit()
# remove "Z" from all datetimes in file
with open('lapswim.ics', 'r') as ics_file:
    ics_lines = ics_file.readlines()
    ics_lines = [line.replace('Z', '') for line in ics_lines]

with open('lapswim.ics', 'w') as ics_file:
    ics_file.writelines(ics_lines)

print("ICS file created successfully!")

from datetime import datetime
from dateutil.tz import gettz
from ics import Event, Calendar, ContentLine

def assign_year(datetime):
    """Assign the year to the closest year now for the date, dealing with the issue of December and January"""
    year = datetime.now().year
    if datetime.month < datetime.now().month:
        return datetime.replace(year=year+1)
    else:
        return datetime.replace(year=year)

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

    start_hour, start_minute = convert_to_24hr(start_time, start_pm)
    end_hour, end_minute = convert_to_24hr(end_time, end_pm)

    start_datetime = datetime(event_day.year, event_day.month, event_day.day, start_hour, start_minute, 0)
    end_datetime = datetime(event_day.year, event_day.month, event_day.day, end_hour, end_minute, 0)

    return start_datetime, end_datetime

def convert_to_24hr(ts, pm):
    # print(ts, pm)
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
    # print(hour, minute)
    return hour, minute

def create_event(event_title, start_time, end_time, event_location, tz):
    """Create an iCalendar event"""

    tzinfo = gettz(tz)
    start_time = start_time.replace(tzinfo=tzinfo)
    end_time = end_time.replace(tzinfo=tzinfo)

    event = Event()
    event.summary = event_title
    event.begin = start_time
    event.end = end_time
    event.location = event_location
    return event

def save_cal(events, name, title):
    """Save the calendar to an ICS file"""

    calendar = Calendar(events=events)

    # add X-WR-CALNAME as display name
    calendar.extra.append(ContentLine(name='X-WR-CALNAME', value=title))

    cal_string = str(calendar.serialize())
    with open(f'{name}.ics', 'w') as ics_file:
        ics_file.write(cal_string)
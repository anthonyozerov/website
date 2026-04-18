import re
import requests
from bs4 import BeautifulSoup
from utils import parse_time, create_event, save_cal
from datetime import datetime, timedelta, date

url = 'https://recwell.berkeley.edu/facilities/recreational-sports-facility-rsf/rsf-hours/'
html_content = requests.get(url).text
soup = BeautifulSoup(html_content, 'html.parser')

TZ = 'America/Los_Angeles'

DAY_NAMES = {
    'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
    'friday': 4, 'saturday': 5, 'sunday': 6
}

def parse_days(day_str):
    """Parse 'Monday–Friday' or 'Saturday' into a list of weekday ints (0=Mon)."""
    s = day_str.lower()
    sep = '–' if '–' in s else ('-' if '-' in s else None)
    if sep:
        parts = s.split(sep)
        start = DAY_NAMES[parts[0].strip()]
        end = DAY_NAMES[parts[1].strip()]
        return list(range(start, end + 1))
    return [DAY_NAMES[s.strip()]]

def normalize_time(time_str):
    """Convert 'X a.m.–Y p.m.' to 'X a.m. - Y p.m.' for parse_time compatibility."""
    return time_str.replace('–', ' - ')

def parse_date_range(text):
    """Parse dates like 'RSF (3/23-3/27)' or 'RSF (3/28)' into a list of date objects."""
    m = re.search(r'\(([^)]+)\)', text)
    if not m:
        return []
    raw = m.group(1)
    year = datetime.now().year
    if '-' in raw:
        start_str, end_str = raw.split('-', 1)
        sm, sd = map(int, start_str.split('/'))
        em, ed = map(int, end_str.split('/'))
        start = date(year, sm, sd)
        end = date(year, em, ed)
        result, d = [], start
        while d <= end:
            result.append(d)
            d += timedelta(days=1)
        return result
    else:
        mo, dy = map(int, raw.split('/'))
        return [date(year, mo, dy)]

tables = soup.find_all('table', class_='table')

regular_hours = {}  # weekday int -> time_str
special_hours = {}  # date -> time_str

for table in tables:
    rows = table.find_all('tr')
    if not rows:
        continue
    first_header = rows[0].find('th')
    is_special = first_header and first_header.text.strip() != 'Facility'

    for row in rows[1:]:
        cols = row.find_all('td')
        if len(cols) != 3:
            continue
        facility_col = cols[0].text.strip()
        days_col = cols[1].text.strip()
        time_col = normalize_time(cols[2].text.strip())

        if is_special:
            for d in parse_date_range(facility_col):
                special_hours[d] = time_col
        else:
            for wd in parse_days(days_col):
                regular_hours[wd] = time_col

today = datetime.now().date()
cal_events = []

for offset in range(-7, 15):
    d = today + timedelta(days=offset)
    dt = datetime(d.year, d.month, d.day)

    if d in special_hours:
        time_str = special_hours[d]
    elif d.weekday() in regular_hours:
        time_str = regular_hours[d.weekday()]
    else:
        continue

    start_time, end_time = parse_time(dt, time_str)
    event = create_event('RSF Open', start_time, end_time, 'RSF', TZ)
    cal_events.append(event)

save_cal(cal_events, 'rsf', 'RSF Open')

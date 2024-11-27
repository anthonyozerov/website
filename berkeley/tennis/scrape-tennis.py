import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
import requests
from astral import LocationInfo
from astral.sun import sun
from yaml import safe_load


def parse_slots(slots):
    begintimes = []
    endtimes = []
    for slot in slots:
        if "Adult Res" not in slot["description"]:
            continue
        begin, end = slot["startDtm"], slot["endDtm"]
        begin = datetime.strptime(begin, "%Y-%m-%d %H:%M:%S")
        end = datetime.strptime(end, "%Y-%m-%d %H:%M:%S")
        begintimes.append(begin)
        endtimes.append(end)
    return begintimes, endtimes


def scrape(location_dict, date):

    name = location_dict["name"]
    with open("scraper.log", "a") as f:
        f.write(f"{name}\n")
    opens = location_dict["opens"]
    res_opens = location_dict["res_opens"]
    res_closes = location_dict["res_closes"]
    closes = location_dict["closes"]
    courts = location_dict["courts"]
    courts_id = location_dict["courts_id"]
    if "unreservable" in location_dict:
        unreservable = location_dict["unreservable"]
    else:
        unreservable = []
    begintimes = {}
    endtimes = {}

    url = "https://ca-berkeley.civicrec.com/CA/berkeley-ca/catalog"
    cookies = requests.get(url).cookies
    action = "getFacilityHours"

    for court, court_id in zip(courts, courts_id):
        # log court to scraper.log
        with open("scraper.log", "a") as f:
            f.write(f"{court}\n")
        slots = requests.get(
            f"{url}/{action}/1/{court_id}/1/{date.isoformat()}",
            cookies=cookies,
        )
        slots = slots.json()
        begintimes[court], endtimes[court] = parse_slots(slots["hours"])

    # read first and last as HH:MM (24h, e.g. 23:00) from opens and closes
    first = pd.to_datetime(f"{date} {opens}")
    last = pd.to_datetime(f"{date} {closes}") - pd.Timedelta("1h")
    first_res = pd.to_datetime(f"{date} {res_opens}")
    last_res = pd.to_datetime(f"{date} {res_closes}") - pd.Timedelta("1h")

    allbegintimes = pd.date_range(start=first, end=last, freq="1h")

    # create a table with 1hr blocks
    table = pd.DataFrame(index=allbegintimes, columns=courts + unreservable)
    for court in courts + unreservable:
        table[court] = "Available"
    for court in courts:
        table.loc[first_res:last_res, court] = "Reserved"
        for begin, end in zip(begintimes[court], endtimes[court]):
            table.loc[begin:(end-pd.Timedelta("1h")), court] = "Available"
    # make index just hour instead of datetime
    table.index = table.index.strftime("%H:%M")
    return table


def get_sunrise_sunset(city, date):
    s = sun(city.observer, date=date)
    sunrise = s["sunrise"]
    sunset = s["sunset"]
    sunrise = sunrise.astimezone(ZoneInfo(city.timezone))
    sunset = sunset.astimezone(ZoneInfo(city.timezone))
    sunrise = sunrise.strftime("%H:%M")
    sunset = sunset.strftime("%H:%M")
    return sunrise, sunset


def color(val):
    color = (
        "#FF7276"
        if val == "Reserved"
        else "lightgreen"
        if val == "Available"
        else "white"
    )
    return f"background-color: {color}"


if __name__ == "__main__":
    config_path = sys.argv[1]
    date = datetime.now().date()

    all_courts = safe_load(open(config_path))

    for k in all_courts:
        print(k)
        all_courts[k]["table"] = scrape(all_courts[k], date)

    # get sunrise and sunset times
    city = LocationInfo("Berkeley", "USA", "America/Los_Angeles", 37.8716, -122.2727)
    sunrise, sunset = get_sunrise_sunset(city, date)
    print(sunrise, sunset)

    # start writing all tables to an html file
    with open("data.html", "w") as f:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        f.write(f"Updated: {now}</h1>")
        f.write(f"<p>Sunrise: {sunrise}, Sunset: {sunset}</p>")
        for k in all_courts:
            data = all_courts[k]
            f.write(f"<h1>{data["name"]}</h1>")
            f.write(f"<p>Official hours: {data["opens"]}-{data["closes"]}</p>")
            infostring = "Has lights. " if data["lights"] else "No lights. "
            infostring += "Has practice wall." if data["wall"] else "No practice wall."
            f.write(f"<p>{infostring}</p>")
            tab_html = data["table"].style.map(color).to_html()
            f.write(tab_html)
            f.write("<br>")

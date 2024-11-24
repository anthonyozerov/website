import pandas as pd
import numpy as np
import sys

from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium import webdriver
from time import sleep
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from yaml import safe_load
from datetime import datetime
from astral import LocationInfo
from astral.sun import sun
from zoneinfo import ZoneInfo

options = FirefoxOptions()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

geckodriver_path = "/snap/bin/geckodriver"
driver_service = webdriver.firefox.service.Service(executable_path=geckodriver_path)
driver = webdriver.Firefox(options=options, service=driver_service)

config_path = sys.argv[1]


def parse_slots(slots):
    lines = slots.split("\n")
    lines = [line.strip() for line in lines if line.strip()]

    # date is today
    date = datetime.now().date()

    begintimes = []
    endtimes = []
    for i in range(2, len(lines)):
        time_slot = lines[i - 1]
        category = lines[i]
        # category string should contain 'Adult Res'
        if "Adult Res" not in category:
            continue
        # print(time_slot)
        begin, end = time_slot.split(" to ")
        # convert to 24 hour time
        begin = datetime.strptime(begin, "%I:%M %p")
        # make it today
        begin = begin.replace(year=date.year, month=date.month, day=date.day)
        end = datetime.strptime(end, "%I:%M %p")
        end = end.replace(year=date.year, month=date.month, day=date.day)
        # print(begin, end)
        begintimes.append(begin)
        endtimes.append(end)
    return begintimes, endtimes


def scrape(location_dict):
    name = location_dict["name"]
    with open("scraper.log", "a") as f:
        f.write(f"{name}\n")
    opens = location_dict["opens"]
    res_opens = location_dict["res_opens"]
    res_closes = location_dict["res_closes"]
    closes = location_dict["closes"]
    courts = location_dict["courts"]
    if "unreservable" in location_dict:
        unreservable = location_dict["unreservable"]
    else:
        unreservable = []
    begintimess = {}
    endtimess = {}
    slotshtml = []
    for court in courts:
        # log court to scraper.log
        with open("scraper.log", "a") as f:
            f.write(f"{court}\n")

        driver.get(
            "https://ca-berkeley.civicrec.com/CA/berkeley-ca/catalog/index/3f7512b8da9e19d57dfa847ce86b85eb"
        )
        # wait until it loads

        elm1 = '//*[@title="Tennis Court Reservation"]'
        elm2 = '//*[contains(text(), "' + name + '")]'
        elm3 = '//*[contains(text(), "' + court + '")]'
        elm4 = "reservation-slots-available"

        print("waiting for elm1")
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, elm1))
        )
        driver.find_element(By.XPATH, elm1).click()

        print("waiting for elm2")
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, elm2))
        )
        driver.find_element(By.XPATH, elm2).click()

        print("waiting for elm3")
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, elm3))
        )
        driver.find_element(By.XPATH, elm3).click()

        print("waiting for elm4")
        WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.CLASS_NAME, elm4))
        )
        # sleep(1)
        slots = driver.find_element(By.CLASS_NAME, elm4)

        slotshtml.append(slots.get_attribute("outerHTML"))
        slots = slots.text
        # print(slots)
        begintimes, endtimes = parse_slots(slots)
        begintimess[court] = begintimes
        endtimess[court] = endtimes

    # first = min([min(begintimes) for begintimes in begintimess.values() if len(begintimes) > 0])
    # last = max([max(endtimes) for endtimes in endtimess.values() if len(endtimes) > 0 ]) - pd.Timedelta('1h')

    # read first and last as HH:MM (24h, e.g. 23:00) from opens and closes
    first = pd.to_datetime(opens)
    last = pd.to_datetime(closes) - pd.Timedelta("1h")
    first_res = pd.to_datetime(res_opens)
    last_res = pd.to_datetime(res_closes) - pd.Timedelta("1h")

    allbegintimes = pd.date_range(start=first, end=last, freq="1h")

    # create a table with 1hr blocks
    table = pd.DataFrame(index=allbegintimes, columns=courts + unreservable)
    for court in courts + unreservable:
        table[court] = "Available"
    for court in courts:
        table.loc[first_res:last_res, court] = "Reserved"
        for begin, end in zip(begintimess[court], endtimess[court]):
            table.loc[begin:end, court] = "Available"
    # make index just hour instead of datetime
    table.index = table.index.strftime("%H:%M")
    return table


all_courts = safe_load(open(config_path))


for k in all_courts:
    print(k)
    all_courts[k]["table"] = scrape(all_courts[k])


def color(val):
    color = (
        "#FF7276"
        if val == "Reserved"
        else "lightgreen"
        if val == "Available"
        else "white"
    )
    return f"background-color: {color}"


# get sunrise and sunset times

city = LocationInfo("Berkeley", "USA", "America/Los_Angeles", 37.8716, -122.2727)
s = sun(city.observer, date=datetime.now().date())
sunrise = s["sunrise"]
sunset = s["sunset"]
# convert to PT

sunrise = sunrise.astimezone(ZoneInfo(city.timezone))
sunset = sunset.astimezone(ZoneInfo(city.timezone))
sunrise = sunrise.strftime("%H:%M")
sunset = sunset.strftime("%H:%M")
print(sunrise, sunset)


# start writing all tables to an html file
with open("data.html", "w") as f:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    f.write(f"Updated: {now}</h1>")
    f.write(f"<p>Sunrise: {sunrise}, Sunset: {sunset}</p>")
    for k in all_courts:
        data = all_courts[k]
        f.write(f'<h1>{data['name']}</h1>')
        f.write(f'<p>Official hours: {data["opens"]}-{data["closes"]}</p>')
        infostring = "Has lights. " if data["lights"] else "No lights. "
        infostring += "Has practice wall. " if data["wall"] else "No practice wall."
        f.write(f"<p>{infostring}</p>")
        tab_html = data["table"].style.map(color).to_html()
        f.write(tab_html)
        f.write("<br>")

driver.quit()

"""Show free-play times using Berkeley's date-specific reservation schedules."""

import argparse
import json
import logging
import re
import tempfile
from datetime import date, datetime, timedelta
from html import unescape
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from astral import LocationInfo
from astral.sun import sun
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from yaml import safe_load


CATALOG = "https://ca-berkeley.civicrec.com/CA/berkeley-ca/catalog"
TIMEZONE = ZoneInfo("America/Los_Angeles")
CITY = LocationInfo("Berkeley", "USA", str(TIMEZONE), 37.8716, -122.2727)
TIMEOUT = (5, 15)
HOUR = timedelta(hours=1)
DATA_ERRORS = (requests.RequestException, ValueError, KeyError, TypeError)
LOGGER = logging.getLogger(__name__)


def local_time(day, value):
    return datetime.combine(day, datetime.strptime(value, "%H:%M").time(), TIMEZONE)


def validate_config(locations):
    seen_ids = set()
    for location in locations.values():
        if not isinstance(location["courts"], dict) or not location["courts"]:
            raise ValueError(f"Expected court names mapped to IDs for {location['name']}")
        for court_id in location["courts"].values():
            if court_id is None:  # Designated walk-up court; no API request needed.
                continue
            if not isinstance(court_id, str) or not court_id.isdigit() or court_id in seen_ids:
                raise ValueError(f"Invalid or duplicate court ID: {court_id}")
            seen_ids.add(court_id)
        opens = datetime.strptime(location["opens"], "%H:%M")
        closes = datetime.strptime(location["closes"], "%H:%M")
        if opens >= closes:
            raise ValueError(f"Invalid park hours for {location['name']}")


def start_session(session):
    response = session.get(CATALOG, timeout=TIMEOUT)
    response.raise_for_status()
    match = re.search(r'\bdata-page-data="([^"]+)"', response.text)
    if match is None:
        raise ValueError("CivicRec catalog data is missing")
    key = json.loads(unescape(match[1]))["checkoutData"]["key"]
    if not isinstance(key, str) or not re.fullmatch(r"[a-f0-9]{32}", key):
        raise ValueError("CivicRec session key is missing")
    return key


def fetch_list(session, path, name):
    response = session.get(f"{CATALOG}/{path}", timeout=TIMEOUT)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict) or data.get("errors") or data.get("error"):
        raise ValueError(f"CivicRec returned an error for {name}")
    if not isinstance(data.get(name), list):
        raise ValueError(f"CivicRec {name} list is missing")
    return data[name]


def merge_intervals(intervals):
    merged = []
    for begin, end in sorted(intervals):
        if merged and begin <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((begin, end))
    return merged


def parse_rates(rates, day):
    """Rate dates mark the season; apply their daily times to the requested day."""
    windows = {}
    for rate in rates:
        if str(rate["account_flag"]) != "0":  # Exclude restricted discount rates.
            continue
        if str(rate["rental_type_id"]) != "2":
            raise ValueError("Expected hourly tennis court rates")
        begin = datetime.fromisoformat(rate["from_dtm"])
        end = datetime.fromisoformat(rate["to_dtm"])
        if not begin.date() <= day <= date.fromisoformat(rate["recurrence_end"]):
            raise ValueError("Rate schedule does not cover the requested date")
        if begin.date() != end.date() or begin.time() >= end.time():
            raise ValueError("Invalid daily reservation window")
        rate_id = str(rate["id"])
        if not rate_id.isdigit() or rate_id in windows:
            raise ValueError("Invalid or duplicate rate ID")
        windows[rate_id] = (
            datetime.combine(day, begin.time(), TIMEZONE),
            datetime.combine(day, end.time(), TIMEZONE),
        )
    if not windows:
        # Missing rates may mean a closure or booking restriction, not free play.
        raise ValueError("No general-public reservation schedule for this date")
    return windows


def parse_slots(slots, rate_id, window):
    available = []
    for slot in slots:
        # Even a request for one rate returns slots for other rate types.
        if str(slot["rateType"]["id"]) != rate_id:
            continue
        begin = datetime.fromisoformat(slot["startDtm"]).replace(tzinfo=TIMEZONE)
        end = datetime.fromisoformat(slot["endDtm"]).replace(tzinfo=TIMEZONE)
        if not window[0] <= begin < end <= window[1]:
            raise ValueError("Available slot is outside its reservation schedule")
        available.append((begin, end))
    return available


def scrape_court(session, key, court_id, day):
    rates = fetch_list(session, f"getFacilityRates/{key}/{court_id}/{day}", "rates")
    windows = parse_rates(rates, day)
    available = []
    for rate_id, window in windows.items():
        path = f"getFacilityHours/{key}/{court_id}/{rate_id}/{day}"
        slots = fetch_list(session, path, "hours")
        available.extend(parse_slots(slots, rate_id, window))
    return {"windows": merge_intervals(windows.values()), "available": merge_intervals(available)}


def scrape(locations, day):
    courts = {
        court_id: f"{location['name']} {name}"
        for location in locations.values()
        for name, court_id in location["courts"].items()
        if court_id is not None
    }
    results = dict.fromkeys(courts)  # None means unknown, never available.
    with requests.Session() as session:
        try:
            key = start_session(session)
        except DATA_ERRORS as exc:
            LOGGER.error("Could not initialize CivicRec: %s", exc)
            return results
        for court_id, name in courts.items():
            try:
                results[court_id] = scrape_court(session, key, court_id, day)
            except DATA_ERRORS as exc:
                LOGGER.error("%s: %s", name, exc)
    return results


def format_intervals(intervals):
    return ", ".join(f"{begin:%H:%M}–{end:%H:%M}" for begin, end in intervals)


def availability(court, begin, end):
    """Combine bookable intervals with time outside the reservation windows."""
    if court is None:
        return "unknown", "Unknown"
    free = list(court["available"])
    cursor = begin
    for left, right in court["windows"]:
        if cursor < left:
            free.append((cursor, left))
        cursor = max(cursor, right)
    if cursor < end:
        free.append((cursor, end))
    free = merge_intervals(
        (max(left, begin), min(right, end)) for left, right in free if left < end and begin < right
    )
    if free == [(begin, end)]:
        return "available", "Available"
    if free:
        return "partial", "Available " + format_intervals(free)
    return "reserved", "Reserved / blocked"


def daylight_status(begin, end, sunrise, sunset):
    if end <= sunrise or begin >= sunset:
        return "Dark"
    if begin < sunrise or end > sunset:
        return "Partial daylight"
    return "Daylight"


def render_page(locations, results, day, updated):
    sunlight = sun(CITY.observer, date=day, tzinfo=TIMEZONE)
    parks = []
    for location in locations.values():
        hours = {}
        for name, court_id in location["courts"].items():
            if court_id is not None:
                court = results[court_id]
                hours[name] = (
                    format_intervals(court["windows"])
                    if court is not None
                    else "Unknown; check the city website."
                )
        rows = []
        begin = local_time(day, location["opens"])
        closing = local_time(day, location["closes"])
        while begin < closing:
            end = min(begin + HOUR, closing)
            cells = [
                availability(results[court_id], begin, end)
                if court_id is not None
                else ("available", "Available")
                for court_id in location["courts"].values()
            ]
            light = daylight_status(begin, end, sunlight["sunrise"], sunlight["sunset"])
            rows.append((format_intervals([(begin, end)]), light, cells))
            begin = end
        parks.append({**location, "hours": hours, "rows": rows})
    templates = Environment(
        loader=FileSystemLoader(Path(__file__).parent), autoescape=True, undefined=StrictUndefined
    )
    return templates.get_template("availability.html.j2").render(
        parks=parks,
        day=day,
        updated=updated,
        sunlight=sunlight,
        failed=any(court is None for court in results.values()),
    )


def atomic_write(path, content):
    """An interrupted refresh must not leave a half-written page."""
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
    ) as output:
        temporary = Path(output.name)
        try:
            output.write(content)
            output.close()
            temporary.chmod(0o644)
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    parser.add_argument(
        "--date", type=date.fromisoformat, help="YYYY-MM-DD; defaults to today in Berkeley"
    )
    parser.add_argument("--output", type=Path, default=Path("data.html"))
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    locations = safe_load(args.config.read_text())
    validate_config(locations)
    updated = datetime.now(TIMEZONE)
    day = args.date or updated.date()
    results = scrape(locations, day)
    failed = sum(court is None for court in results.values())
    LOGGER.info("Checked %d courts; %d failed", len(results), failed)
    atomic_write(args.output, render_page(locations, results, day, updated))
    return int(failed > 0)


if __name__ == "__main__":
    raise SystemExit(main())

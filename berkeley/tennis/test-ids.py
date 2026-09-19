from pathlib import Path

import requests
from yaml import safe_load

config_path = Path(__file__).with_name("tennis-courts.yaml")
all_courts = safe_load(config_path.read_text())
url = "https://ca-berkeley.civicrec.com/CA/berkeley-ca/catalog/viewFacilityRules"

with requests.Session() as session:
    for value in all_courts.values():
        name = value["name"]
        for court, court_id in value["courts"].items():
            if court_id is None:
                continue
            response = session.get(f"{url}/{court_id}", timeout=(5, 15))
            response.raise_for_status()
            res = response.json()
            if res.get("errors") or res.get("title") != f"{name} {court} Rules":
                raise ValueError(f"Court ID {court_id} does not match {name} {court}")
            print(f"Verified: {name} {court} ({court_id})")

import requests
from yaml import safe_load

config_path = "tennis-courts.yaml"
all_courts = safe_load(open(config_path))
url = "https://ca-berkeley.civicrec.com/CA/berkeley-ca/catalog/viewFacilityRules"

for value in all_courts.values():
    name = value["name"]
    for court, court_id in zip(value["courts"], value["courts_id"]):
        res = requests.get(f"{url}/{court_id}").json()
        assert res["title"] == f"{name} {court} Rules"

"""
Dans un terminal :

$ export DATA_ECO_API_KEY=<my API Key>

Modifiez les variables DATASET_ID, START, END

python stats.py
"""

import calendar
import csv
import os
from datetime import datetime

import requests

DATASET_ID = ""
START = 2024, 5
END = 2025, 5

if len(DATASET_ID) == 0:
    raise Exception("Ajoutez un jeu de données cible")


def get_month_start_end_dates(start_year, start_month, end_year, end_month):
    dates = []
    current_year = start_year
    current_month = start_month
    while (current_year < end_year) or (
        current_year == end_year and current_month <= end_month
    ):
        start_date = datetime(current_year, current_month, 1)
        last_day = calendar.monthrange(current_year, current_month)[1]
        end_date = datetime(current_year, current_month, last_day)
        dates.append((start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))
        if current_month == 12:
            current_month = 1
            current_year += 1
        else:
            current_month += 1
    return dates


def generate_url(start, end):
    url = f"https://data.economie.gouv.fr/api/explore/v2.1/monitoring/datasets/ods-api-monitoring/records"
    params = {
        "where": f'dataset_id = "{DATASET_ID}" AND timestamp >= "{start}" AND timestamp <= "{end}"',
        "select": "count(*) as calls",
        "group_by": "dataset_id",
    }
    return {"url": url, "params": params}


HEADERS = {"Authorization": f"Apikey {os.environ['DATA_ECO_API_KEY']}"}

month_dates = get_month_start_end_dates(*START, *END)

with open(
    f"{datetime.now().strftime('%Y-%m-%d')}-{DATASET_ID}-api-calls-count.csv", "w"
) as file:
    writer = csv.DictWriter(file, fieldnames=["timestamp", "dataset_id", "calls"])
    writer.writeheader()
    for start, end in month_dates:
        data = generate_url(start, end)
        response = requests.get(**data, headers=HEADERS)
        data = response.json()["results"][0]
        data["timestamp"] = start
        print(start, data)
        writer.writerow(data)

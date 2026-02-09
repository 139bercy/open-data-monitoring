import argparse
import json
import os
import sys
from datetime import date

import requests
from dotenv import load_dotenv

from logger import logger

load_dotenv(".env")
DATE = date.today()

# Config
API_KEY = os.environ["DATA_ECO_API_KEY"]
ODS_DOMAIN = os.environ["ODS_DOMAIN"]
HEADERS = {"Authorization": f"Apikey {API_KEY}", "Accept": "application/json"}


def file_is_not_empty(filepath):
    return os.path.isfile(filepath) and os.path.getsize(filepath) > 0


def get_source_uid(dataset_uid):
    url = f"https://{ODS_DOMAIN}/api/automation/v1.0/datasets/{dataset_uid}/resources"
    response = requests.get(url, headers=HEADERS)
    data = response.json()
    if data["total_count"] > 0:
        result = data["results"][0]["uid"]
        logger.debug(f"STATS - Dataset has one resource: {result}")
        return result
    return


def delete_resource(dataset_uid, resource_uid):
    url = f"https://{ODS_DOMAIN}/api/automation/v1.0/datasets/{dataset_uid}/resources/{resource_uid}/"
    requests.delete(url, headers=HEADERS)
    logger.debug(f"STATS - Resource {resource_uid} deleted. ")


def upload_file(filepath, dataset_uid):
    url = f"https://{ODS_DOMAIN}/api/automation/v1.0/datasets/{dataset_uid}/resources/files/"
    with open(filepath, "rb") as f:
        files = {"file": (os.path.basename(filepath), f, "text/csv")}
        response = requests.post(url, headers=HEADERS, files=files)
        response.raise_for_status()
        result = response.json()
        logger.info("STATS - Upload complete:")
        logger.debug(result)
        return result["uid"]


def add_resource(filepath, dataset_uid):
    url = f"https://{ODS_DOMAIN}/api/automation/v1.0/datasets/{dataset_uid}/resources"

    metadata = {
        "type": "csvfile",
        "title": os.path.basename(filepath),
        "params": {
            "doublequote": True,
            "encoding": "utf-8",
            "first_row_no": 1,
            "headers_first_row": True,
            "separator": ",",
        },
        "datasource": {"type": "uploaded_file", "file": {"uid": filepath}},
    }

    response = requests.post(url, headers=HEADERS, json=metadata)
    logger.info(f"STATS - Resource {filepath} has been created")
    logger.debug(json.dumps(response.json()))
    response.raise_for_status()
    return response.json()


def publish_dataset(dataset_uid):
    url = f"https://{ODS_DOMAIN}/api/automation/v1.0/datasets/{dataset_uid}/publish"
    response = requests.post(url, headers=HEADERS)
    response.raise_for_status()
    data = response.json()
    if "error" in data:
        logger.error(f"STATS - ❌ Publishing error: {data}")
        sys.exit(1)
    logger.info("STATS - 🚀 Dataset published successfully!")


def execute(file, dataset_uid):
    if not file_is_not_empty(file):
        logger.error(f"STATS - ❌ File '{file}' is empty or does not exist. Aborting.")
        sys.exit(1)

    logger.info(f"STATS - ✅  File '{file}' is ready for upload.")
    source_uid = get_source_uid(dataset_uid=dataset_uid)
    if source_uid is not None:
        delete_resource(dataset_uid=dataset_uid, resource_uid=source_uid)
    upload_file(filepath=file, dataset_uid=dataset_uid)
    add_resource(filepath=file, dataset_uid=dataset_uid)
    publish_dataset(dataset_uid=dataset_uid)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload a CSV file to a data.gouv.fr dataset")
    parser.add_argument("--file", required=True, help="Path to the CSV file to upload")
    parser.add_argument("--dataset_uid", required=True, help="Target dataset UID")

    args = parser.parse_args()

    execute(file=args.file, dataset_uid=args.dataset_uid)

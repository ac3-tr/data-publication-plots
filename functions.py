#!/usr/bin/env python
"""
| *author*: Johannes Röttenbacher
| *created*: 22.11.2024

Description of script
"""
import json
import logging
import requests

log = logging.getLogger(__name__)

# Query Zenodo API and return all records of one community
def query_zenodo(community, page=1, size=100, base_url='https://zenodo.org/api/records/'):
    all_records = []
    while True:
        params = {
            "communities": community,
            "page": page,
            "size": size
        }
        response = requests.get(base_url, params=params)
        if response.status_code != 200:
            log.error(f"Failed to fetch data from Zenodo. Status code: {response.status_code}")
            break

        data = response.json()
        records = data.get("hits", {}).get("hits", [])
        all_records.extend(records)

        log.info(f"Fetched {len(records)} records from page {page}.")

        # Check if there are more pages
        if len(records) < size:
            break

        page += 1

    return all_records


def get_pangaea_usage_statistics(doi):
    r = requests.get('https://doi.pangaea.de/'+doi+'?format=statistics')
    try:
        j = json.loads(r.text)
    except:
        print('Problem with get_usgae_statistics(', doi, ')')
        j = {}
    return j


def extract_single_value(x):
    # If x is a list with exactly one item, return the item, otherwise return the value as is
    if isinstance(x, list) and len(x) == 1:
        return x[0]
    return x



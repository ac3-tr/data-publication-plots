#!/usr/bin/env python
"""
| *author*: Johannes Röttenbacher
| *created*: 22.11.2024

Description of script
"""
import json
import logging
import requests
from sickle import Sickle
from tqdm import tqdm

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


def get_metadata_from_repository(oai_url, set_name, output_file, metadata_prefix='oai_dc'):
    """
    Retrieves OAI-PMH metadata from an OAI-PMH provider given a `oai_url` and a `set_name`.
    Writes all retrieved metadata for all data sets into one JSON file.
    Sickle can officially only handle the `oai_dc` (Dublin Core) metadata standard.
    Other metadata prefixes are generally possible but are not guaranteed to work.

    :param oai_url: URL to the OAI-PMH provider.
    :param set_name: Set to subset the returned data sets by.
    :param output_file: Name of JSON file.
    :param metadata_prefix: (oai_dc) other metadata prefixes are possible but not guaranteed to work.
    :return: Writes a JSON file to the current working directory.
    """
    sickle = Sickle(oai_url)
    # Storage for results
    datasets = []

    # Fetch records
    logging.info(f'\N{DOWNWARDS BLACK ARROW} Starting dataset retrieval from {oai_url}...')
    try:
        records = sickle.ListRecords(metadataPrefix=metadata_prefix, set=set_name)
        for record in tqdm(records, 'Records', unit=' records'):
            # Extract metadata from the record
            if record.deleted:  # if the record is deleted continue to next one
                continue
            metadata = record.metadata
            # give sensible defaults if no value is found for a key to avoid raising an error
            dataset = {
                'doi': metadata.get('identifier', 'No doi')[0],
                'authors': metadata.get('creator', []),
                'title': metadata.get('title', 'No title'),
                'date': metadata.get('date', 'No date'),
                'format': metadata.get('format', 'No format'),
                'type': metadata.get('type', 'No type'),
                'coverage': metadata.get('coverage', 'No coverage'),
                'rights': metadata.get('rights', 'No rights'),
                'relation': metadata.get('relation', 'No relation'),
                'description': metadata.get('description', 'No description'),
                'publisher': metadata.get('publisher', 'No publisher'),
            }

            # Ensure multivalued fields are stored as lists
            for key, value in dataset.items():
                if not isinstance(value, list):
                    dataset[key] = [value]

            datasets.append(dataset)
            logging.debug(f'Processed dataset: {dataset['title']}')

        logging.info(f'Dataset retrieval complete. Total records: {len(datasets)}')

    except Exception as e:
        logging.error(f'An error occurred during dataset retrieval: {e}')

    # Export results to JSON
    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(datasets, file, ensure_ascii=False, indent=4)

    logging.info(f'Data exported to {output_file}')


def get_pangaea_usage_statistics(doi):
    r = requests.get('https://doi.pangaea.de/'+doi+'?format=statistics')
    try:
        j = json.loads(r.text)
    except:
        print('Problem with get_usage_statistics(', doi, ')')
        j = {}
    return j


def extract_single_value(x):
    # If x is a list with exactly one item, return the item, otherwise return the value as is
    if isinstance(x, list) and len(x) == 1:
        return x[0]
    return x



#!/usr/bin/env python
"""
| *author*: Johannes Röttenbacher
| *created*: 10.12.2024

Retrieve metadata from repositories and write them to a JSON file for each repository.
"""
import functions as fn
import time

date = time.strftime("%Y%m%d", time.localtime())

oai_urls = ['https://zenodo.org/oai2d', 'https://ws.pangaea.de/oai/provider']
set_names = ['user-crc172-ac3', 'query~cHJvamVjdDpsYWJlbDpBQzM']
output_files = [f'{date}-datasets_ac3_zenodo.json', f'{date}-datasets_ac3_pangaea.json']
for oai_url, set_name, output_file in zip(oai_urls, set_names, output_files):
    fn.get_metadata_from_repository(oai_url, set_name, output_file)
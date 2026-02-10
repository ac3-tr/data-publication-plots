#!/usr/bin/env python
"""
| *created*: 10.02.26
| *author*: Johannes Röttenbacher

Get usage statistics from Zenodo and PANGAEA and plot a pie chart from it
"""
from os import WCONTINUED

import functions as fn
import json
import logging
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd
from pathlib import Path
import requests
import time
from tqdm import tqdm

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(message)s')
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger(__name__).addHandler(console)

date = 20260210
# %% Get Zenodo stats
zenodo_stats_path = Path(f'./data/{date}_usage_stats_zenodo.json')
if zenodo_stats_path.exists():
    print('File already exists.')
    with open(zenodo_stats_path, 'r', encoding='utf-8') as f:
        stats_zenodo = json.load(f)
else:
    logging.info("\N{book} Get views and downloads from Zenodo...")
    community = 'crc172-ac3'
    records = fn.query_zenodo(community)
    total_views = 0
    total_downloads = 0

    stats_zenodo = dict(doi=[], metadata_views=[], data_views=[], downloads=[])
    for record in records:
        stats = record.get('stats', {})
        total_views += stats.get('unique_views', 0)
        total_downloads += stats.get('unique_downloads', 0)
        stats_zenodo['doi'].append(record.get('doi_url', ''))
        stats_zenodo['metadata_views'].append(0)
        stats_zenodo['data_views'].append(stats.get('unique_views', 0))
        stats_zenodo['downloads'].append(stats.get('unique_downloads', 0))

    with open(zenodo_stats_path, 'w') as f:
        json.dump(stats_zenodo, f)

zenodo_df = pd.DataFrame(stats_zenodo)
zenodo_df['publisher'] = 'Zenodo'

# %% Get PANGAEA stats
stats_path = Path(f'./data/{date}_usage_stats_pangaea.json')
if stats_path.exists():
    print('File already exists.')
    with open(stats_path, 'r', encoding='utf-8') as f:
        stats_dict = json.load(f)
else:
    logging.info("\N{book} Get views and downloads from PANGAEA...")
    # get all ac3 datasets from latest metadata harvest
    with open(f'./data/{date}-datasets_ac3_pangaea.json', 'r', encoding='utf-8') as p_file:
        pangaea_data = json.load(p_file)

    # Create a DataFrame
    df = pd.DataFrame(pangaea_data)
    # get values out of a single valued lists
    df = df.map(fn.extract_single_value)

    stats = []
    stats_dict = dict(doi=[], metadata_views=[], data_views=[], downloads=[])
    # Query the PANGAEA website
    for doi in tqdm(df['doi']):
        r = requests.get(doi + '?format=statistics')
        try:
            j = json.loads(r.text)
        except:
            print('Problem with get_usage_statistics(', doi, ')')
            j = {}
        stats_dict['doi'].append(doi)
        stats_dict['metadata_views'].append(j.get('metadata_views', 0))
        stats_dict['data_views'].append(j.get('data_views', 0))
        stats_dict['downloads'].append(j.get('downloads', 0))
        stats.append(j)
        time.sleep(0.1)

    # save to json file for reuse
    with open(f'./data/{date}_usage_stats_pangaea.json', 'w') as outfile:
        json.dump(stats_dict, outfile)

pangaea_df = pd.DataFrame(stats_dict)
pangaea_df['publisher'] = 'PANGAEA'

# %% merge data frames
df = pd.concat([pangaea_df, zenodo_df])

# %% create pie and bar charts
cm = 1/2.54
fmt_dict = dict(presentation=
                dict(figsize=(15 * cm, 15 * cm),
                     lw=2,
                     fontsize=12,
                     legendfontsize=10),
                )
mode = 'presentation'
fmt = fmt_dict[mode]
plt.rc('font', size=fmt['fontsize'])
# Funktion zum Erzeugen eines Pie-Charts
def create_pie_chart(df, title):
    sums = df[['metadata_views', 'data_views', 'downloads']].sum()
    labels = ['Metadata Views', 'Data Views', 'Downloads']
    plt.figure(figsize=fmt['figsize'], dpi=300)
    plt.pie(sums,
            labels=labels,
            labeldistance=0.6,
            pctdistance=0.5,
            autopct=lambda p: f'{int(p * sum(sums) / 100):,}',
            startangle=140
            )
    plt.title(title)


def create_bar_chart(df, title):
    sums = df[['metadata_views', 'data_views', 'downloads']].sum()
    labels = ['Metadata Views', 'Data Views', 'Downloads']
    plt.figure(figsize=fmt['figsize'], dpi=300, constrained_layout=True)
    bars = plt.bar(labels, sums, color=['tab:blue', 'tab:orange', 'tab:green'])
    plt.ylabel('Count')
    formatter = ticker.FuncFormatter(lambda x, p: format(int(x), ','))
    plt.gca().yaxis.set_major_formatter(formatter)
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, yval, f'{int(yval):,}', ha='center', va='bottom')
    plt.title(title)

# Pie-Chart für PANGAEA
pangaea_df = df[df['publisher'] == 'PANGAEA']
create_pie_chart(pangaea_df, 'PANGAEA Publications')
plt.savefig(f'./figures/{date}_usage_statistics_pangaea_pie.png', dpi=300)
plt.show()
create_bar_chart(pangaea_df, 'PANGAEA Publications')
plt.savefig(f'./figures/{date}_usage_statistics_pangaea_bar.png', dpi=300)
plt.show()

# Pie-Chart für Zenodo (falls vorhanden)
zenodo_df = df[df['publisher'] == 'Zenodo']
if not zenodo_df.empty:
    create_pie_chart(zenodo_df, 'Zenodo Publications')
    plt.savefig(f'./figures/{date}_usage_statistics_zenodo_pie.png', dpi=300)
    plt.show()
    create_bar_chart(zenodo_df, 'Zenodo Publications')
    plt.savefig(f'./figures/{date}_usage_statistics_zenodo_bar.png', dpi=300)
    plt.show()

# Pie-Chart für alle Publikationen
create_pie_chart(df, 'All Publications on PANGAEA and Zenodo')
plt.savefig(f'./figures/{date}_usage_statistics_pie.png', dpi=300)
plt.show()
create_bar_chart(df, 'All Publications on PANGAEA and Zenodo')
plt.savefig(f'./figures/{date}_usage_statistics_bar.png', dpi=300)
plt.show()
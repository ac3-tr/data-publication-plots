#!/usr/bin/env python
"""
| *author*: Johannes Röttenbacher
| *created*: 20.11.2024

Figures and facts for the poster at the SFB INF workshop on Cologne 2 - 3 December 2024

- Data publications per year from PANGAEA and Zenodo
- Metadataviews, downloads, ... from both repositories
"""
# %% import packages
import argparse
from PIL import Image
from wordcloud import WordCloud, STOPWORDS
import datetime as dt
import json
import logging
import functions as fn
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import sys
import time

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(message)s')
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger(__name__).addHandler(console)

# %% set date of metadata retrieval
def get_args(debug=False, date=None):
    parser = argparse.ArgumentParser(
        description="Harvest metadata from Zenodo and PANGAEA for the (AC)³ community"
    )
    parser.add_argument("date",
                        help="Date (yyyymmdd) for which the plots should be made.",
                        default=time.strftime("%Y%m%d", time.localtime()),
                        nargs='?')

    if debug:
        # Simulate command-line input
        sys.argv = ['script.py', date or '20251022']
        args = parser.parse_args()
    else:
        args = parser.parse_args()

    return args

# Debug mode
# args = get_args(debug=True, date="20251022")

args = get_args()
date = args.date

# %% Get views and downloads from Zenodo
logging.info("\N{book} Get views and downloads from Zenodo...")
community = 'crc172-ac3'
records = fn.query_zenodo(community)
total_views = 0
total_downloads = 0

for record in records:
    stats = record.get('stats', {})
    total_views += stats.get('unique_views', 0)
    total_downloads += stats.get('unique_downloads', 0)

logging.info(f'Total Views from Zenodo: {total_views}')
logging.info(f'Total Downloads from Zenodo: {total_downloads}')

# %% Load JSON files with all AC3 publications and do some preprocessing
with open(f'./data/{date}-datasets_ac3_zenodo.json', 'r', encoding='utf-8') as z_file:
    zenodo_data = json.load(z_file)

with open(f'./data/{date}-datasets_ac3_pangaea.json', 'r', encoding='utf-8') as p_file:
    pangaea_data = json.load(p_file)

# Merge the datasets
all_data = zenodo_data + pangaea_data

# Create a DataFrame
df = pd.DataFrame(all_data)
# get values out of a single valued lists
df = df.map(fn.extract_single_value)

# Convert date to actual dates
dates = []
for date in df['date']:
    if date == 'No date':
        dates.append(pd.NaT)
        continue
    try:
        dates.append(pd.to_datetime(date))
    except:
        dates.append(pd.to_datetime(date, format='%Y'))

df['date'] = dates

# drop rows with no dates -> data set is still in review
df = df.dropna(subset='date')

# create categorical columns
categorical_columns = ['type', 'publisher']  # Modify this based on your data
df[categorical_columns] = df[categorical_columns].apply(lambda x: x.astype('category') if x.name in categorical_columns else x)

# %% remove dataset collections
df = df[~df.type.isin(['dataset bundled publication', 'dataset bibliography', 'dataset publication series'])]

# %% keep only the latest version of each Zenodo data set
df_sub = df[df.publisher == 'Zenodo']
df_sub = df_sub.sort_values(by='title').reset_index(drop=True)

# Extract the last relation as the common DOI
df_sub['common_doi'] = df_sub['relation'].apply(lambda x: x[-1] if isinstance(x, list) and x else None)

# Sort by 'created' and keep only the latest version per common DOI
latest_versions = df_sub.sort_values('date').groupby('common_doi', as_index=False).last()

# %% add cleaned zenodo df to df
df = pd.concat([df[df['publisher'] == 'PANGAEA'], latest_versions.drop('common_doi', axis=1)]).reset_index(drop=True)

# %% Add year column
df['year'] = df['date'].dt.year

# Calculate the number of publications per year
yearly_publications = df.groupby(['year', 'publisher'], observed=False).size().reset_index(name='count')

# Calculate cumulative publications
yearly_publications['cumulative_count'] = yearly_publications['count'].cumsum()
publisher_sel = yearly_publications['publisher'] == 'Zenodo'
yearly_publications['cumulative_count_zenodo'] = yearly_publications[publisher_sel]['count'].cumsum()
yearly_publications['cumulative_count_pangaea'] = yearly_publications[~publisher_sel]['count'].cumsum()

# %% Formatting for plots
cm = 1 / 2.54
fmt_dict = dict(presentation=
                dict(figsize=(15 * cm, 7.5 * cm),
                     lw=2,
                     fontsize=12,
                     legendfontsize=10),
                poster=
                dict(figsize=(40 * cm, 15 * cm),
                     lw=6,
                     fontsize=40,
                     legendfontsize=24
                     )
                )

# %% Create mask for wordcloud
from matplotlib.patches import Ellipse

ellipse = Ellipse((0, 0), 8, 4, angle=0)
_, ax = plt.subplots()
ax.set(xlim=(-4.2, 4.2), ylim=(-2.2, 2.2))  # , aspect="equal")
ax.add_artist(ellipse)
plt.savefig('./figures/ellipse_mask.png')
# plt.show()
plt.close()

# %% Generate and plot a wordcloud made out of the most common words in the data sets
titles = df['title'].to_list()
mask = np.array(Image.open('figures/ellipse_mask.png'))

logging.info(f'\N{cloud} Number of titles for word cloud: {len(titles)}')

titles_combined = ''

for t in titles:
    t1 = t
    for rr in ['Ny-Ålesund', 'Ny-Alesund']:
        t1 = t1.replace(rr, 'NyÅlesund')
    for rr in ['in situ', 'in-situ']:
        t1 = t1.replace(rr, 'InSitu')
    for rr in ['measurements']:
        t1 = t1.replace(rr, 'measurement')
    t1 = ' ' + t1
    titles_combined += t1

stopwords = set(STOPWORDS)
stopwords.add('borne')
stopwords.add('tethered')
stopwords.add('VISSS')
stopwords.add('Situ')
stopwords.add('Snowfall')
stopwords.add('Sensor')
stopwords.add('Hyytiäla')
stopwords.add('Video')

wordcloud = WordCloud(mask=mask, collocations=True,
                      stopwords=stopwords, max_words=100,
                      collocation_threshold=50,
                      background_color=None,
                      max_font_size=60, relative_scaling=0.2,
                      contour_width=0, mode='RGBA')

wordcloud = wordcloud.generate(titles_combined)

fig, ax = plt.subplots(1)
ax.imshow(wordcloud, interpolation='bilinear')
ax.axis('off')
fig.savefig('figures/wordcloud_ellipse_{date}.png', dpi=300, transparent=False)
plt.show()

# %% Plot cumulative publications and yearly publications
mode = 'presentation'
fmt = fmt_dict[mode]
plt.rc('font', size=fmt['fontsize'])
yearly_publications = yearly_publications[(yearly_publications['year'] >= 2016) &
                                          (yearly_publications['year'] < 2028)]
fig, ax = plt.subplots(figsize=fmt['figsize'], layout='constrained')
# Plot the bar chart for yearly publications
sns.barplot(data=yearly_publications, x='year', y='count', hue='publisher')

# Plot the line chart for cumulative publications
sns.pointplot(data=yearly_publications, x='year', y='cumulative_count',
             marker='o', label='Cumulative\npublications',
             color='orange', lw=fmt['lw'],
             ax=ax)

# Get x-axis categorical positions
x_positions = range(len(yearly_publications['year'].unique()))

# Loop through points to annotate
y_pubs = pd.DataFrame(yearly_publications.groupby('year')['count'].sum())
y_pubs['cumsum'] = y_pubs.cumsum()
for x, y, label in zip(x_positions, y_pubs['cumsum'], y_pubs['cumsum']):
    ax.text(x, y + 0.2, str(label), ha='right', fontsize=fmt['legendfontsize'])

# Add labels and title
ax.set(
    # title='Yearly Publications and Cumulative Publications',
    title='',
    xlabel='Year',
    ylabel='Count',
)
ax.legend(fontsize=fmt['legendfontsize'])
ax.tick_params(axis='x', rotation=45)  # Rotates the x-axis tick labels by 45 degrees
ax.yaxis.set_major_locator(plt.MultipleLocator(base=500))

plt.savefig(f'./figures/{date}_yearly_cumulative_publications_{mode}.png', dpi=300)
plt.show()
plt.close()

# %% Plot cumulative publications and yearly publications separated by repository
mode = 'presentation'
fmt = fmt_dict[mode]
plt.rc('font', size=fmt['fontsize'])

# Filter data
yearly_publications = yearly_publications[
    (yearly_publications['year'] >= 2016) &
    (yearly_publications['year'] < 2028)
    ]

# Create figure with two rows (one per publisher)
fig, axes = plt.subplots(
    2, 1, figsize=fmt['figsize'], layout='constrained'
)

# Set up the barplot and pointplot for each publisher
publishers = yearly_publications['publisher'].unique()
for i, publisher in enumerate(publishers):
    # Filter data for this publisher
    df_pub = yearly_publications[yearly_publications['publisher'] == publisher]

    # Bar plot (yearly count)
    sns.barplot(
        data=df_pub,
        x='year',
        y='count',
        ax=axes[i],
        color='steelblue',
        alpha=0.8
    )

    # Point plot (cumulative count)
    sns.pointplot(
        data=df_pub,
        x='year',
        y=f'cumulative_count_{publisher.lower()}',
        marker='o',
        color='orange',
        lw=fmt['lw'],
        ax=axes[i],
        label='Cumulative publications',
        legend=None,
    )

    # Annotate cumulative values
    y_pubs = df_pub.groupby('year')['count'].sum().cumsum()
    for x, y in enumerate(y_pubs):
        axes[i].text(x, y + 0.2, str(int(y)), ha='center', fontsize=fmt['legendfontsize'])

    # Labels and formatting
    axes[i].set(
        xlabel='Year',
        ylabel='Count',
        title=f'{publisher}',
    )

# Adjust legend (only one needed)
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, loc='upper left',
           bbox_to_anchor=(0.15, 0.9),
           fontsize=fmt['legendfontsize'])
# First row
axes[0].set(
    xlabel='',
    xticklabels=''
)
axes[0].yaxis.set_major_locator(plt.MultipleLocator(base=500))
# Second row
axes[1].tick_params(axis='x', rotation=45)
axes[1].yaxis.set_major_locator(plt.MultipleLocator(base=10))

# Save and show
plt.savefig(f'./figures/{date}_yearly_cumulative_publications_per_repo_{mode}.png',
            dpi=300,
            bbox_inches='tight')
plt.show()
plt.close()

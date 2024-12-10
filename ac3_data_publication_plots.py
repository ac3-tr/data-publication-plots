#!/usr/bin/env python
"""
| *author*: Johannes Röttenbacher
| *created*: 20.11.2024

Figures and facts for the poster at the SFB INF workshop on Cologne 2 - 3 December 2024

- Data publications per year from PANGAEA and Zenodo
- Metadataviews, downloads, ... from both repositories
"""
# %% import packages
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
import time

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger('').addHandler(console)

# %% Get views and downloads from Zenodo
community = "crc172-ac3"
records = fn.query_zenodo(community)
total_views = 0
total_downloads = 0

for record in records:
    stats = record.get('stats', {})
    total_views += stats.get('unique_views', 0)
    total_downloads += stats.get('unique_downloads', 0)

print(f"Total Views: {total_views}")
print(f"Total Downloads: {total_downloads}")

# %% Load JSON files with all AC3 publications and do some preprocessing
with open('./data/datasets_ac3_zenodo.json', 'r', encoding='utf-8') as z_file:
    zenodo_data = json.load(z_file)

with open('./data/datasets_ac3_pangaea.json', 'r', encoding='utf-8') as p_file:
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
yearly_publications = df.groupby(['year', 'publisher']).size().reset_index(name='count')

# Calculate cumulative publications
yearly_publications['cumulative_count'] = yearly_publications['count'].cumsum()


# %% Generate and plot a wordcloud made out of the most common words in the data sets
titles = df['title'].to_list()
mask = np.array(Image.open('figures/ellipse_mask.png'))

print(len(titles))

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
ax.axis("off")
fig.savefig('figures/wordcloud_ellipse_' + dt.datetime.now().strftime('%Y%m%d') + '.png', dpi=300, transparent=False)
plt.show()

# %% Plot cumulative publications and yearly publications
cm = 1 / 2.54
plt.rc('font', size=30)
figsize = (40 * cm, 15 * cm)
yearly_publications = yearly_publications[yearly_publications['year'] >= 2016]
fig, ax = plt.subplots(figsize=figsize, layout='constrained')
# Plot the bar chart for yearly publications
sns.barplot(data=yearly_publications, x='year', y='count', hue='publisher')

# Plot the line chart for cumulative publications
sns.pointplot(data=yearly_publications, x='year', y='cumulative_count',
             marker='o', label='Cumulative\npublications',
             color='orange', lw=6,
             ax=ax)

# Get x-axis categorical positions
x_positions = range(len(yearly_publications['year'].unique()))

# Loop through points to annotate
y_pubs = pd.DataFrame(yearly_publications.groupby('year')['count'].sum())
y_pubs['cumsum'] = y_pubs.cumsum()
for x, y, label in zip(x_positions, y_pubs['cumsum'], y_pubs['cumsum']):
    ax.text(x, y + 0.2, str(label), ha='right', fontsize=24)

# Add labels and title
ax.set(
    # title='Yearly Publications and Cumulative Publications',
    title='',
    xlabel='Year',
    ylabel='Count',
)
ax.legend(fontsize=24)
ax.tick_params(axis='x', rotation=45)  # Rotates the x-axis tick labels by 45 degrees
ax.yaxis.set_major_locator(plt.MultipleLocator(base=500))

now = pd.to_datetime(time.time(), unit='s').strftime('%Y-%m-%d')
plt.savefig(f'./figures/{now}_yearly_cumulative_publications.png', dpi=300)
plt.show()
plt.close()





# (AC)³ - Data publication plots

This repository holds a function in `functions.py`, which queries a repository via the Open Archives Initiative Protocol for Metadata Harvesting (OAI-PMH) to retrieve metadata from the given subset of data.

Currently tested for [PANGAEA](https://wiki.pangaea.de/wiki/OAI-PMH) and [Zenodo](https://developers.zenodo.org/#oai-pmh).

The set for PANGAEA can be a virtual set and can be created from a search term at https://ws.pangaea.de/oai/ .

The set for Zenodo can be a community set of the form `user-<identifier>`, where `<identifier>` is a valid community identifier.

The (AC)³ specific set names are `user-crc172-ac3`for Zenodo and `query~cHJvamVjdDpsYWJlbDpBQzM` for PANGAEA.

Zenodo also offers simple access via HTTPS and one can retrieve all data sets from a community.
`functions.py` has the function `query_zenodo()` for that purpose.
It does need an Access Token for request with `size > 25`, which can be supplied via a .env file.
You can create such a token in your [Zenodo user account](https://zenodo.org/account/settings/applications/tokens/new/). 

Given a DOI from PANGAEA we can also retrieve usage statistics of this individual data set with `get_usage_statistics.py`

## How to use

Clone the repository and create the folders `data` and `figures`. 

Create your venv or conda env using `requirements.txt` or `enviornment.yml` respectively.
Or using pixi, run `pixi install`.

### pixi tasks

`pixi run harvest`

Runs `metadata_harvest.py` to create json files of the metadata from PANGAEA and Zenodo.
They are saved in `data`.

`pixi run plot`

Runs `ac3_data_publication_plots.py` and saves plots in `figures`.
Adjust the plots to your liking in the script.
You can enter an interactive/debug mode by uncommenting the line after `# Debug mode`.
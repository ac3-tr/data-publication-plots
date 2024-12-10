# (AC)³ - Data publication plots

This repository holds a function in `functions.py`, which queries a repository via the Open Archives Initiative Protocol for Metadata Harvesting (OAI-PMH) to retrieve metadata from the given subset of data.

Currently tested for [PANGAEA](https://wiki.pangaea.de/wiki/OAI-PMH) and [Zenodo](https://developers.zenodo.org/#oai-pmh).

The set for PANGAEA can be a virtual set and can be created from a search term at https://ws.pangaea.de/oai/ .

The set for Zenodo can be a community set of the form `user-<identifier>`, where `<identifier>` is a valid community identifier.

The (AC)³ specific set names are `user-crc172-ac3`for Zenodo and `query~cHJvamVjdDpsYWJlbDpBQzM` for PANGAEA.

Zenodo also offers simple access via HTTP and one can retrieve all data sets from a community. `functions.py` has the function `query_zenodo()` for that purpose.

Given a DOI from PANGAEA we can also retrieve usage statistics of this individual data set with `get_usage_statistics.py`
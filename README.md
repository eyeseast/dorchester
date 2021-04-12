# dorchester

[![PyPI](https://img.shields.io/pypi/v/dorchester.svg)](https://pypi.org/project/dorchester/)
[![Changelog](https://img.shields.io/github/v/release/eyeseast/dorchester?include_prereleases&label=changelog)](https://github.com/eyeseast/dorchester/releases)
[![Tests](https://github.com/eyeseast/dorchester/workflows/Test/badge.svg)](https://github.com/eyeseast/dorchester/actions?query=workflow%3ATest)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/eyeseast/dorchester/blob/master/LICENSE)

## Caveat emptor

This is very alpha right now. Use at your own risk and evaluate any editorial usage of this of this library before publishing.

A toolkit for making dot-density maps in Python (eventually).

## Installation

Install this tool using `pip`:

    $ pip install dorchester

## Usage

The main command is `dorchester plot`. That takes an input file, an output file and one or more property keys to extract population counts.

```sh
dorchester plot --help
Usage: dorchester plot [OPTIONS] SOURCE DEST

  Generate data for a dot-density map. Input may be any GIS format readable
  by Fiona (Shapefile, GeoJSON, etc).

Options:
  -k, --key TEXT              Property name for a population. Use multiple to
                              map different population classes.

  -f, --format [csv|geojson]  Output format. If not given, will guess based on
                              output file extension.

  -m, --mode [w|a|x]          File mode for destination.
  --help                      Show this message and exit
```

Input can be in any format readable by [Fiona](https://fiona.readthedocs.io/en/stable/index.html), such as Shapefiles and GeoJSON. The input file needs to contain both population data and boundaries. You may need to join different files together before plotting with `dorchester`.

Output format (`--format`) can be CSV or GeoJSON (more formats coming soon). For GeoJSON, the output will be a stream of newline-delimited `Point` features, like this:

```json
{"type": "Feature", "geometry": {"type": "Point", "coordinates": [76, 38]}, "properties": {"group": "population", "fid": 1}}
{"type": "Feature", "geometry": {"type": "Point", "coordinates": [77, 39]}, "properties": {"group": "population", "fid": 1}}
{"type": "Feature", "geometry": {"type": "Point", "coordinates": [78, 37]}, "properties": {"group": "population", "fid": 1}}
```

This will be _big_ files, because we are creating a point for every individual. Massachusetts, for example, had a population of 6.631 million in 2010, which means a dot density CSV file will be 6,336,107 lines long and 305 mb.

Each key (`--key`) should correspond to a property on each feature whose value is a whole number. In a block like this, use `--key POP10` to extract population:

```json
{
  "geometry": {
    "coordinates": [...],
    "type": "Polygon"
  },
  "id": "0",
  "properties": {
    "BLOCKCE": "4023",
    "BLOCKID10": "250010112004023",
    "COUNTYFP10": "001",
    "HOUSING10": 16,
    "PARTFLG": "N",
    "POP10": 12,
    "STATEFP10": "25",
    "TRACTCE10": "011200"
  },
  "type": "Feature"
}
```

You can pass multiple `--key` options to create different groups that will be layered together. This is how you would create a map showing different racial groups, for example.

Finally, the `--mode` option controls how the output file is opened:

- `w` will create or overwrite the output file
- `a` will append to an existing file
- `x` will try to create a new file and fail if that file already exists

## About the name

[Dorchester](https://en.wikipedia.org/wiki/Dorchester,_Boston) is the largest and most diverse neighborhood in Boston, Mass, and is often referred to as Dot.

The name is also a nod to [Englewood](https://github.com/newsapps/englewood), built by the Chicago Tribune News Apps team. This is, hopefully, a worthy successor.

## Development

To contribute to this tool, first checkout the code. Then create a new virtual environment:

    cd dorchester
    python -m venv .venv
    source .venv/bin/activate

Or if you are using `pipenv`:

    pipenv shell

Now install the dependencies and tests:

    pip install -e '.[test]'

To run the tests:

    pytest

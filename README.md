This programs compares OSM walking route data to that of other data sets.

It as extension of the tool by Friso Smit (https://github.com/fwsmit/osm-knooppunten/releases/latest)

New:
- analysis of the network (routes from node to node)
- analysis of changes in routedatabank for two timestamps
- reading of geojson file of OSM data
- new categories: medium distance moved, added double, removed double

# Goals

The main goal for this tool is to help importing walking and cycling route data
into OpenStreetMap.

- Analyze differences in walking and cycling routes
- Categorize changes in helpful categories
- Make these things available in a simple graphical tool

# Current state

This tool is still under active development. Currently it can analyze
walking nodes+network & cycling nodes (no network). It's built with the dataset from Routedabank.nl in mind, but it
can be expanded for other datasets in the future.

# Installation

Make sure to install python on your system. This program depends on the
following libraries:

- python geojson for package for importing geojson data
- pyside6 for the Qt GUI
- scipy for spatial datastructure KD tree
- rijksdriehoek for converting RD coordinates to wgs

Open a command prompt and install with:
	
	pip install geojson pyside6 scipy rijksdriehoek

Then download the code repository from github. You can dowload the latest
release (recommended) or the latest git version.

To download the [latest release](https://github.com/Wolderik/osm-knooppunten-netwerken)
and unzip it to a directory of your choice. Then you can proceed to running it.

# Running

It's easy to run this program with it's graphical interface. Simply run the
file `knooppunten.py` that you just unzipped in python. To do this, right click
the file in your file manager and select "Run with" and choose python. The
application should open.

## Selecting data

The proram needs two data files to compare. In the section "Getting the data"
you can learn more about how to aquire the data. There are
some example data files provided for the region Groningen.
Let's move on, assuming you have the right data.

The first step is selecting the OSM data. Press the "Select button" to select
an OSM data file (.geojson or .osm).

Then you can select a data file to compare against. This file has to be of the
geojson format.

Lastly you can filter the import data by region. This is recommended
to make the computing time reasonable. Also make sure the OSM data is also of
the same region to minimize the number of false positives.

## Running analysis

If you're done selecting the data, click the "run" button to start the
analysis. This will open a new window that will eventually display the results.

## Interpreting results

The results window shows a table of different node categories. All nodes from
the import dataset have been categorized in one of the following categories:

- `Renamed`: Node is still in the same place, but has a different number
- `Minor rename`: Same as rename, but used for minor renames. This is when node
  differs in name by only a few letters.
- `Removed`: Node is not present in import dataset, but is in OSM
- `Added`: Node is not present in OSM, but is in the import dataset
- `No change`: Nothing is different between the OSM and import node
- `Moved short distance`: Node moved a distance of <20m
- `Moved medium distance`: Node moved a distance of 20-100m
- `Moved long distance`: Node moved a distance of 100-1000m
- `Added double`: Node is not present in OSM, but is in the import dataset as double node
- `Removed double`: Node is not present in import dataset, but is in OSM as double node
- `Other`: Could not be determined to be in one of the above categories

All results are exported to geojson in result directory. You can open them in JOSM to analyze them
further and make changes to OSM. All nodes in the export have metadata tagged
to thme with their node numbers in the import dataset.

For the network the same categories are used. Short distance is edge distance < 50 m. Medium distance 50 to 100 m. Results are exported to results/netwerk directory.

# Data sources

This tool is written for comparing the data from OpenStreetMap and Routedatabank in mind.

## OSM data

Below are instructions for gathering data from the overpass API.

- Go to overpass-turbo.eu
- Use the wizard to create a query with your region of choice.
	- For hiking nodes and network this would be: `((network=rwn and network:type=node_network and type:relation) or (rwn_ref=* and network:type=node_network and type:node)) in Noord-Brabant`
	- For cycling nodes: `rcn_ref=* and network:type=node_network and type:node in Nederland`

- Run the query and export the results as geojson

You now have succesfully created a dataset that can be used by this program.

## Routedatabank

This data is not downloadable without account. But the comparison results are added in this repository (only for OSM purposes).

# Command line interface

You can also run the analyzer using a command line interface. This currently has
the similar functionality to the graphical application. Instructions for running
it are below.

Open a terminal in this project's directory. 

## Comparing hiking nodes and network: OSM vs Routedatabank

The program can be run with the following command for analyzing nodes and network in which OSMFILE contains both nodes and network:

	python knooppunten-cli.py [-h] --osmfile OSMFILE --importfile_nodes IMPORTFILE_NODES --importfile_network IMPORTFILE_NETWORK [--region REGION]

Examples:

python knooppunten-cli.py --osmfile "D:\Downloads\ZuidOostBrabant_wandelen_20_aug_2023.geojson" --importfile_network "D:\Downloads\Route_data_bank\18_augustus_2023\Wandelnetwerken (wgs84).json" --importfile_nodes "D:\Downloads\Route_data_bank\18_augustus_2023\Wandelknooppunten (wgs84).json" --region "Noord-Brabant"

python knooppunten-cli.py --osmfile "D:\Downloads\OSM_Nederland_14_jan_2024.geojson" --importfile_network "D:\Downloads\Route_data_bank\2_jan_2024\Wandelnetwerken (wgs84).json" --importfile_nodes "D:\Downloads\Route_data_bank\2_jan_2024\Wandelknooppunten (wgs84).json"

## Comparing hiking nodes and network: Routedatabank vs Routedatabank

The program can be run with the following command for comparing nodes/network from Routedatabank with different timestamp:

	python knooppunten-cli.py [-h] --osmfile OSMFILE_NODES --osmfile_network OSMFILE_NETWORK --importfile_nodes IMPORTFILE_NODES --importfile_network IMPORTFILE_NETWORK [--region REGION]

Example:

python knooppunten-cli.py --osmfile "D:\Downloads\Route_data_bank\30_juli_2023\Wandelknooppunten (wgs84).json" --osmfile_network "D:\Downloads\Route_data_bank\30_juli_2023\Wandelnetwerken (wgs84).json" --importfile_network "D:\Downloads\Route_data_bank\2_jan_2024\Wandelnetwerken (wgs84).json" --importfile_nodes "D:\Downloads\Route_data_bank\2_jan_2024\Wandelknooppunten (wgs84).json"

## Comparing cycling nodes: OSM vs Routedatabank

The program can be run with the following command for analyzing nodes:

	python knooppunten-cli.py [-h] --osmfile OSMFILE --importfile_nodes IMPORTFILE [--region REGION]

Where you replace the arguments in capital letters with your own arguments. For example for Windows users:

        python knooppunten-cli.py --osmfile "D:\Downloads\OSM_Nederland_fietsen_14_jan_2024.geojson" --importfile_nodes "D:\Downloads\Route_data_bank\21_jan_2024\Fietsknooppunten (open data).json"

## Comparing cycling nodes: Routedatabank vs Routedatabank

The program can be run with the following command for comparing nodes from Routedatabank with different timestamp:

	python knooppunten-cli.py [-h] --osmfile OSMFILE_NODES --importfile_nodes IMPORTFILE_NODES [--region REGION]

Example:

python knooppunten-cli.py --osmfile "D:\Downloads\Route_data_bank\30_juli_2023\Fietsknooppunten (open data).json" --importfile_nodes "D:\Downloads\Route_data_bank\21_jan_2024\Fietsknooppunten (open data).json"

For more detail about the arguments, run:

	python knooppunten-cli.py -h

# Testing

To run the unit tests, use the following command (from the main directory):

        python -m tests.runner

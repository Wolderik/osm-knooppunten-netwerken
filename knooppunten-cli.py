import sys
import argparse as arg
from _version import __version__
from analyze import do_analysis

def main():
    parser = arg.ArgumentParser()
    parser.add_argument("--osmfile", type=str, required=True, help="File with OSM data")
    parser.add_argument("--osmfile_network", type=str, required=False, help="File with network OSM data")
    parser.add_argument("--importfile_nodes", type=str, required=True, help="File with node import data")
    parser.add_argument("--importfile_network", type=str, required=False, help="File with network import data")
    parser.add_argument("--region", type=str, help="Compare the OSM data only to the import data from this region")
    parser.add_argument("--province", type=str, help="Compare the OSM data only to the import data from this province")
    parser.add_argument('--version', action='version', version='%(prog)s {version}'.format(version=__version__))

    try:
        args = parser.parse_args()
    except IOError as er:
        print(er)
        sys.exit(1)

    print("Analyzing differences between datasets")

    #do_analysis(args.osmfile, args.importfile, args.region, args.province, None)
    do_analysis(args.osmfile, args.importfile_nodes, args.osmfile_network, args.importfile_network, args.region, args.province, None)

if __name__ == "__main__":
    main()

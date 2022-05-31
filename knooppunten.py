from import_osm import import_osm
from import_geojson import import_geojson
from compare import find_matching_point

def main():
    nodes_osm = import_osm("data/best.osm")
    nodes_ext = import_geojson("data/groningen.geojson")

    #  print("OSM nodes")
    #  for n in nodes_osm:
        #  print(n.__geo_interface__)

    #  print("Geojson nodes")
    #  for n in nodes_ext:
        #  print(n.__geo_interface__)

    find_matching_point(nodes_ext[1], nodes_osm);

    print("Done")

if __name__ == "__main__":
    main()



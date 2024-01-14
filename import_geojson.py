import geojson
import os
import math
import sys
from node import Node
from compare import dist_complicated
from osm_knooppunten import helper
from export import ExportFile
from edge import Edge

def import_geojson_netwerken(filename, rwn_name = None, rcn_name = None, filter_regio = None, filter_province = None):
    try:
        with open(filename, 'r', encoding="utf8") as file:
            data = geojson.load(file)
    except IOError as er:
        print(er)
        sys.exit(1)

    edges = []
    invalid_edges = []

    for edge_data in data['features']:
        #print(edge_data['properties'])

        rwn_ref_id = None

        regio = edge_data['properties'].get("regio")
        if filter_regio and regio and regio != filter_regio:
            continue

        province = edge_data['properties'].get("provincie")
        if filter_province and province and province != filter_province:
            continue

        if edge_data['geometry']['type'] != "LineString":
            continue

        #if rwn_name:
        #    if rwn_name in edge_data['properties']:
        #        rwn_ref_id = edge_data['properties'][rwn_name]

        #rcn_ref_id = None
        #if rcn_name:
        #    if rcn_name in edge_data['properties']:
        #        rcn_ref_id = edge_data['properties'][rcn_name]
        
        ref = edge_data['properties'].get("ref")

        ref_start = None
        ref_end = None

        if ref:
            ind = ref.find('-')
            ref_start = ref[0:ind]
            ref_end = ref[ind+1:]

        if edge_data['geometry']:
            coords = edge_data['geometry']['coordinates']
            coord_lon = coords[0]
            coord_lat = coords[1]
        else:
            coord_lon = None
            coord_lat = None

        rwn_ref_id=''
        rcn_ref_id=''
        edge = Edge(coords=coords, ref_start=ref_start, ref_end = ref_end)
        if (edge.ref_start and not helper.is_number_valid(edge.ref_start)) or (edge.ref_end and not helper.is_number_valid(edge.ref_end)):
            invalid_edges.append(edge)
        else:
            edges.append(edge)

    return edges, invalid_edges

def import_geojson_combined(filename, rwn_name = None, rcn_name = None, filter_regio = None, filter_province = None):
    try:
        with open(filename, 'r', encoding="utf8") as file:
            data = geojson.load(file)
    except IOError as er:
        print(er)
        sys.exit(1)

    nodes = []
    invalid_nodes = []

    edges = []
    invalid_edges = []

    for node_edge_data in data['features']:
        #print(edge_data['properties'])

        rwn_ref_id = None

        regio = node_edge_data['properties'].get("regio")
        if filter_regio and regio and regio != filter_regio:
            continue

        province = node_edge_data['properties'].get("provincie")
        if filter_province and province and province != filter_province:
            continue

        if node_edge_data['geometry']['type'] == "Point":

            id_found = False

            rwn_ref_id = None
            if rwn_name:
                if rwn_name in node_edge_data['properties']:
                    rwn_ref_id = node_edge_data['properties'][rwn_name]
                    id_found = True
                    #if rwn_ref_id != "11":
                    #    continue

            rcn_ref_id = None
            if rcn_name:
                if rcn_name in node_edge_data['properties']:
                    rcn_ref_id = node_edge_data['properties'][rcn_name]
                    id_found = True

            if 'rwn_ref' in node_edge_data['properties']:
                rwn_ref_id = node_edge_data['properties']['rwn_ref']
                id_found = True

            if 'rcn_ref' in node_edge_data['properties']:
                rcn_ref_id = node_edge_data['properties']['rcn_ref']
                id_found = True

            if not id_found:
                 continue

            if node_edge_data['geometry']:
                coords = node_edge_data['geometry']['coordinates']
                coord_lon = coords[0]
                coord_lat = coords[1]
            else:
                coord_lon = None
                coord_lat = None

            node = Node(lon=coord_lon, lat=coord_lat, rwn_ref=rwn_ref_id, rcn_ref=rcn_ref_id)
            if not helper.is_number_valid(node.rwn_ref) and not helper.is_number_valid(node.rcn_ref):
                invalid_nodes.append(node)
            else:
                nodes.append(node)


        if node_edge_data['geometry']['type'] == "LineString":

            ref = node_edge_data['properties'].get("ref")

            ref_start = None
            ref_end = None

            if ref:
                ind = ref.find('-')
                ref_start = ref[0:ind]
                ref_end = ref[ind+1:]

            if node_edge_data['geometry']:
                coords = node_edge_data['geometry']['coordinates']
            else:
                coords = None

            edge = Edge(coords=coords, ref_start=ref_start, ref_end = ref_end)
            if (edge.ref_start and not helper.is_number_valid(edge.ref_start)) or (edge.ref_end and not helper.is_number_valid(edge.ref_end)):
                invalid_edges.append(edge)
            else:
                edges.append(edge)

    return nodes, invalid_nodes, edges, invalid_edges


def import_geojson(filename, rwn_name = None, rcn_name = None, filter_regio = None, filter_province = None):
    try:
        with open(filename, 'r', encoding="utf8") as file:
            data = geojson.load(file)
    except IOError as er:
        print(er)
        sys.exit(1)

    nodes = []
    invalid_nodes = []

    for node_data in data['features']:
        rwn_ref_id = None

        regio = node_data['properties'].get("regio")
        if filter_regio and regio and node_data['properties']["regio"] != filter_regio:
            continue

        province = node_data['properties'].get("provincie")
        if filter_province and province and node_data['properties']["provincie"] != filter_province:
            continue

        rwn_ref_id = None
        if rwn_name:
            if rwn_name in node_data['properties']:
                rwn_ref_id = node_data['properties'][rwn_name]
                #if rwn_ref_id != "11":
                #    continue


        rcn_ref_id = None
        if rcn_name:
            if rcn_name in node_data['properties']:
                rcn_ref_id = node_data['properties'][rcn_name]

        if 'rwn_ref' in node_data['properties']:
             rwn_ref_id = node_data['properties']['rwn_ref']

        if 'rcn_ref' in node_data['properties']:
             rcn_ref_id = node_data['properties']['rcn_ref']

        if node_data['geometry']:
            coords = node_data['geometry']['coordinates']
            coord_lon = coords[0]
            coord_lat = coords[1]
        else:
            coord_lon = None
            coord_lat = None

        node = Node(lon=coord_lon, lat=coord_lat, rwn_ref=rwn_ref_id, rcn_ref=rcn_ref_id)
        if not helper.is_number_valid(node.rwn_ref) and not helper.is_number_valid(node.rcn_ref):
            invalid_nodes.append(node)
        else:
            nodes.append(node)

    return nodes, invalid_nodes

def export_geojson(nodes, filename):
    print("Exporting to", filename)
    features = []
    for node in nodes:
        if node.closest_match_dist:
            closest_distance = node.closest_match_dist
        else:
            closest_distance = -1

        point = geojson.Point((node.lon, node.lat))

        if node.renamed_from:
            properties_dict = {"rwn_ref": node.rwn_ref, "rcn_ref": node.rcn_ref, "distance closest node": closest_distance, "old_name": node.renamed_from}
        else:
            properties_dict = {"rwn_ref": node.rwn_ref, "rcn_ref": node.rcn_ref, "distance closest node": closest_distance}

        feature = geojson.Feature(geometry=point, properties=properties_dict)
        features.append(feature)

        matched_node = node.matched_node
        if matched_node and not node.renamed_from:
           #route_line = geojson.LineString(matched_edge.coords)
           point = geojson.Point((matched_node.lon, matched_node.lat))
           #properties_dict = {"ref_start": matched_edge.ref_start, "ref_end": matched_edge.ref_end, "distance closest node": closest_distance, "osm":True}
           properties_dict = {"rwn_ref": node.rwn_ref, "rcn_ref": node.rcn_ref, "distance closest node": closest_distance, "osm":True}
           feature = geojson.Feature(geometry=point, properties=properties_dict)
           features.append(feature)           

    dump = geojson.dumps(features)

    resultsdir = "results"
    try:
        os.mkdir(resultsdir)
    except FileExistsError:
        pass # The directory already exists, move on

    filepath = os.path.join(resultsdir, filename)

    try:
        with open(filepath, 'w') as f:
            f.write(dump)
        return ExportFile(filename=filename, filepath=filepath, n_nodes=len(nodes))
    except IOError as er:
        print(er)
        sys.exit(1)


def export_geojson_edges(edges, filename):
    print("Exporting to", filename)
    features = []
    for edge in edges:
        if edge.closest_match_dist:
            closest_distance = edge.closest_match_dist
        else:
            closest_distance = -1

        route_line = geojson.LineString(edge.coords)

        #if edge.renamed_from:
        #    properties_dict = {"rwn_ref": node.rwn_ref, "rcn_ref": node.rcn_ref, "distance closest node": closest_distance, "old_name": node.renamed_from}
        #else:
        #    properties_dict = {"rwn_ref": node.rwn_ref, "rcn_ref": node.rcn_ref, "distance closest node": closest_distance}

        properties_dict = {"ref_start": edge.ref_start, "ref_end": edge.ref_end, "distance closest node": closest_distance}

        feature = geojson.Feature(geometry=route_line, properties=properties_dict)
        features.append(feature)

        matched_edge = edge.matched_edge
 
        if matched_edge:
           route_line = geojson.LineString(matched_edge.coords)
           properties_dict = {"ref_start": matched_edge.ref_start, "ref_end": matched_edge.ref_end, "distance closest node": closest_distance, "osm":True}
           feature = geojson.Feature(geometry=route_line, properties=properties_dict)
           features.append(feature)           

    dump = geojson.dumps(features)

    #resultsdir = "results"
    resultsdir = os.path.join('results','netwerk')
    try:
        os.mkdir(resultsdir)
    except FileExistsError:
        pass # The directory already exists, move on

    filepath = os.path.join(resultsdir, filename)

    try:
        with open(filepath, 'w') as f:
            f.write(dump)
        return ExportFile(filename=filename, filepath=filepath, n_nodes=len(edges))
    except IOError as er:
        print(er)
        sys.exit(1)


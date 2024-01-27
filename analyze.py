import math
from enum import Enum
from compare import find_closest_node, dist_complicated
from import_osm import import_osm
from import_geojson import import_geojson, export_geojson, import_geojson_netwerken, export_geojson_edges, import_geojson_combined
from compare import find_matching_point, dist_complicated, find_closest_node, find_matching_nodes, create_tree, find_closest_node_using_tree, find_matching_nodes_using_tree
from osm_knooppunten.helper import is_small_rename
from _version import __version__
import os
from scipy.spatial import KDTree
import numpy as np
import copy

class ChangeType(Enum):
    # No significant change
    NO = 1

    # Exists in OSM dataset, but does not exist in import dataset and is not renamed
    REMOVED = 2

    # Does not exist in OSM dataset, but does exist in import dataset and is not renamed
    ADDED = 3

    # Close to node in other dataset with a different name. The other node
    # doesn't have a matching node either. Minor renames are classified as RENAMED_MINOR
    RENAMED = 4

    # Same as renamed, but used for minor renames. This is used when the
    # difference is just a couple of letters. When it's a different number,
    # it's classified as a normal rename.
    RENAMED_MINOR = 5

    # Matches with a node in the other dataset with distance 1-20m
    MOVED_SHORT = 6

    # Matches with a node in the other dataset with distance 20-100m
    MOVED_MEDIUM = 7

    # Matches with a node in the other dataset with distance 100-1000m
    MOVED_LONG = 8

    # Matches with a node in the other dataset with distance < 60 however another node also matches with smaller distance
    ADDED_DOUBLE = 9

    # Matches with a node in the other dataset with distance > 60 and < 500 however another node also matches with smaller distance
    ADDED_DOUBLE_LONG = 10

    # Matches with a node in the other dataset with distance < 60 however that node does not match with it
    REMOVED_DOUBLE = 11

    # Matches with a node in the other dataset with distance > 60 and < 500 however that node does not match with it
    REMOVED_DOUBLE_LONG = 12

    # None of the others
    OTHER = 13

    def __str__(self):
        if self == ChangeType.NO:
            return "No change"

        if self == ChangeType.REMOVED:
            return "Removed"

        if self == ChangeType.ADDED:
            return "Added"

        if self == ChangeType.RENAMED:
            return "Renamed"

        if self == ChangeType.RENAMED_MINOR:
            return "Minor rename"

        if self == ChangeType.MOVED_SHORT:
            return "Moved short distance"

        if self == ChangeType.MOVED_MEDIUM:
            return "Moved medium distance"

        if self == ChangeType.MOVED_LONG:
            return "Moved long distance"

        if self == ChangeType.ADDED_DOUBLE:
            return "Added double"

        if self == ChangeType.REMOVED_DOUBLE:
            return "Removed double"

        if self == ChangeType.ADDED_DOUBLE_LONG:
            return "Added double long distance"

        if self == ChangeType.REMOVED_DOUBLE_LONG:
            return "Removed double long distance"

        if self == ChangeType.OTHER:
            return "Other"

        return "Unknown enum value: {}".format(self.value)

def get_node_change_type_ext(node_ext, nodes_osm, nodes_ext):
    closest_match = node_ext.closest_match_node
    if (closest_match):
        closest_match_dist = node_ext.closest_match_dist
        one_to_one_match = (closest_match.closest_match_node == node_ext)
    else:
        closest_match_dist = math.inf
    
    # TODO: Should find next closest node if closest node has a match
    if closest_match_dist > 1000:
        #print("closest_match_dist: "+str(closest_match_dist))
        # closest_node = find_closest_node(node_ext, nodes_osm)
        closest_node = node_ext.closest_node

        if closest_node:
            #closest_node_dist = dist_complicated(closest_node.lat, closest_node.lon, node_ext.lat, node_ext.lon)
            closest_node_dist = node_ext.closest_dist

            closest_match_of_closest_node = closest_node
            if closest_match_of_closest_node:
                 closest_match_dist_of_closest_node = closest_match_of_closest_node.closest_match_dist
                 if closest_match_dist_of_closest_node == None:
                     closest_match_dist_of_closest_node = math.inf
            else:
                 closest_match_dist_of_closest_node = math.inf 
        else:
            closest_node_dist = math.inf
            closest_match_dist_of_closest_node = math.inf

        #print(closest_node_dist)
        if closest_node_dist < 40 and closest_match_dist_of_closest_node > 1000:
            if node_ext.rwn_ref:
                print("rename")
                print(node_ext.rwn_ref)
                print(closest_node.rwn_ref)
                node_ext.renamed_from = closest_node.rwn_ref
                if is_small_rename(node_ext.rwn_ref, closest_node.rwn_ref):
                    return ChangeType.RENAMED_MINOR, closest_node
                else:
                    return ChangeType.RENAMED, closest_node

            if node_ext.rcn_ref:
                node_ext.renamed_from = closest_node.rcn_ref
                if is_small_rename(node_ext.rcn_ref, closest_node.rcn_ref):
                    return ChangeType.RENAMED_MINOR, closest_node
                else:
                    return ChangeType.RENAMED, closest_node

    if not closest_match:
        return ChangeType.ADDED, None

    if closest_match_dist > 1000:
        return ChangeType.ADDED, None

    if not one_to_one_match and closest_match_dist < 60:
        return ChangeType.ADDED_DOUBLE, None

    if not one_to_one_match and closest_match_dist < 500:
        return ChangeType.ADDED_DOUBLE_LONG, None

    if not one_to_one_match:
        return ChangeType.ADDED, None

    if closest_match_dist > 100 and closest_match_dist < 1000:
        return ChangeType.MOVED_LONG, closest_match

    if closest_match_dist > 20 and closest_match_dist <= 100:
        return ChangeType.MOVED_MEDIUM, closest_match

    if closest_match_dist > 1 and closest_match_dist <= 20:
        return ChangeType.MOVED_SHORT, closest_match

    if closest_match_dist < 1:
        return ChangeType.NO, closest_match

    return ChangeType.OTHER, None

def is_node_removed_osm(node_osm, nodes_osm, nodes_ext):
    all_matching_nodes = node_osm.matching_nodes
    all_matching_nodes.extend(node_osm.bad_matching_nodes)

    closest_match = find_closest_node(node_osm, all_matching_nodes)
    if (closest_match):
        closest_match_dist = dist_complicated(closest_match.lat, closest_match.lon, node_osm.lat, node_osm.lon)
    else:
        closest_match_dist = math.inf

    if not all_matching_nodes or len(all_matching_nodes) == 0 or closest_match_dist > 1000:
        return True

def do_analysis_internal(nodes_osm, nodes_ext, nodes_osm_invalid, nodes_ext_invalid, progress):

    use_kd_tree = True
    #use_kd_tree = False

    if use_kd_tree:
        tree_osm = create_tree(nodes_osm)
        tree_ext = create_tree(nodes_ext)

        for node_ext in nodes_ext:
            #closest_node = find_closest_node(node_ext, nodes_osm)
            closest_node = find_closest_node_using_tree(node_ext, nodes_osm, tree_osm)
            node_ext.closest_node = closest_node
            node_ext.closest_dist = dist_complicated(closest_node.lat, closest_node.lon, node_ext.lat, node_ext.lon)

            if 0 and closest_node != closest_node_tree:
                 print("different")
                 print(closest_node.lat)
                 print(closest_node_tree.lat)
                 print(closest_node.lon)
                 print(closest_node_tree.lon)
                 print(dist_complicated(closest_node.lat, closest_node.lon, node_ext.lat, node_ext.lon))
                 print(dist_complicated(closest_node_tree.lat, closest_node_tree.lon, node_ext.lat, node_ext.lon))

    print("start match");
    if use_kd_tree:
        find_matching_nodes_using_tree(nodes_osm, nodes_ext, tree_osm, tree_ext)
    else:
        find_matching_nodes(nodes_osm, nodes_ext)

    #nodes_osm_copy = copy.deepcopy(nodes_osm)
    #nodes_ext_copy = copy.deepcopy(nodes_ext)

    print("eind match");

    node_changes_dict = dict()
    for key in ChangeType:
        node_changes_dict[key] = []

    i = 0;
    for node in nodes_ext:
        #print("Node", i)
        #print("Node_ext: "+node.rwn_ref)
        change_type, matched_node = get_node_change_type_ext(node, nodes_osm, nodes_ext)
        if matched_node and matched_node.matched_node:
        
            # The matched node was already matched to some other node
            # TODO give better warning here
            print("ERROR: Node was matched twice")
            if node.rwn_ref:
                print(node.rwn_ref)
                print(matched_node.rwn_ref)
                print(matched_node.matched_node.rwn_ref)

        node.change_type = change_type
        if matched_node:
            matched_node.matched_node = node
            matched_node.change_type = change_type
            node.matched_node = matched_node

        node_changes_dict[change_type].append(node)
        i += 1
        #progress.emit("Analyzing nodes {}/{}".format(i, len(nodes_ext)))

    for node in nodes_osm:
        if not node.matched_node:
            if node.closest_match_dist:
                if node.closest_match_dist < 60:
                    node.change_type = ChangeType.REMOVED_DOUBLE
                    node_changes_dict[ChangeType.REMOVED_DOUBLE].append(node)
                else:
                    if node.closest_match_dist < 500:
                        node.change_type = ChangeType.REMOVED_DOUBLE_LONG
                        node_changes_dict[ChangeType.REMOVED_DOUBLE_LONG].append(node)
                    else:
                        node.change_type = ChangeType.REMOVED
                        node_changes_dict[ChangeType.REMOVED].append(node)
            else:
                node.change_type = ChangeType.REMOVED
                node_changes_dict[ChangeType.REMOVED].append(node)

    print('')
    print('*** Nodes ***')
    for key in node_changes_dict:
        print("{}: {}".format(key, len(node_changes_dict[key])))

    #progress.emit("Exporting results")
    exported_files = []
    export_file = export_geojson(nodes_osm_invalid, "Invalid_osm.geojson")
    exported_files.append(export_file)
    export_file = export_geojson(nodes_ext_invalid, "Invalid_ext.geojson")
    exported_files.append(export_file)

    for key in ChangeType:
        if key == ChangeType.REMOVED or key == ChangeType.REMOVED_DOUBLE:
            export_file = export_geojson(node_changes_dict[key], "{}_osm.geojson".format(key))
        else:
            export_file = export_geojson(node_changes_dict[key], "{}_ext.geojson".format(key))
        exported_files.append(export_file)
    #progress.emit("Done")
    return exported_files

def create_tree_start_edge(edges):
        n = len(edges)
        #print(n)
        xy_points=np.zeros((n,2))
        i=0
        for edge in edges:
            i=i+1
            xy_points[i-1][0]=edge.coords_in_m[0][0]
            xy_points[i-1][1]=edge.coords_in_m[0][1]
        tree = KDTree(xy_points)
        return tree

def create_tree_end_edge(edges):
        n = len(edges)
        #print(n)
        xy_points=np.zeros((n,2))
        i=0
        for edge in edges:
            i=i+1
            xy_points[i-1][0]=edge.coords_in_m[-1][0]
            xy_points[i-1][1]=edge.coords_in_m[-1][1]
        tree = KDTree(xy_points)
        return tree

def find_neighbors_in_tree(x, y, tree, k, max_distance):

    n = tree.n

    dd, ii = tree.query([[x, y]], k = k, distance_upper_bound=max_distance)
        
    ii_tmp = ii[0]
    ii_ind = np.where(ii_tmp < n)[0]
    ii_short = ii_tmp[ii_ind]

    return ii_short

def get_stepped_coords(coords, step_distance, coords_org):
    n = len(coords)

    stepped_coords = []

    total_dist = 0

    for i in range(1,n):

        x_1 = coords_org[i-1][0]
        y_1 = coords_org[i-1][1]
    
        x_2 = coords_org[i][0]
        y_2 = coords_org[i][1]

        d_12_org = dist_complicated(y_1, x_1, y_2, x_2)

        x_1 = coords[i-1][0]
        y_1 = coords[i-1][1]
    
        x_2 = coords[i][0]
        y_2 = coords[i][1]

        d_12 = math.sqrt((x_2-x_1)**2 + (y_2-y_1)**2)

        #print("d12_org: "+str(d_12_org)+" d12: "+str(d_12))

        total_dist = total_dist + d_12

        nr_steps = 1 + int(d_12/step_distance)

        #print("nr steps: "+str(nr_steps))

        for j in range(nr_steps):
            x_step = x_1 + j / nr_steps * (x_2 - x_1)
            y_step = y_1 + j / nr_steps * (y_2 - y_1)

            stepped_coords.append((x_step,y_step))

    stepped_coords.append((x_2,y_2))

    #print("total_dist: "+str(total_dist))

    return stepped_coords

def calculate_edge_to_edge_distance(edge_a, edge_b):

    #print("edge: "+ edge_a.ref_start + " " + edge_a.ref_end)
    
    step_distance_in_m = 10    

    stepped_coords_a = get_stepped_coords(edge_a.coords_in_m, step_distance_in_m, edge_a.coords)
    stepped_coords_b = get_stepped_coords(edge_b.coords_in_m, step_distance_in_m, edge_b.coords)

    stepped_coord_array_a = np.array(stepped_coords_a)
    stepped_coord_array_b = np.array(stepped_coords_b)

    tree_a = KDTree(stepped_coord_array_a)

    method_a = False

    if method_a:

        max_dist = 0
        for point in stepped_coords_b:        
            dd, ii = tree_a.query(point, k = 1)
            if dd > max_dist:
                max_dist = dd

    else:
        dd, ii = tree_a.query(stepped_coords_b, k = 1)
        max_dist = max(dd)

    max_dist_b = max_dist
    #print("max dist b: "+str(max_dist))

    tree_b = KDTree(stepped_coord_array_b)

    if method_a:
        max_dist = 0
        for point in stepped_coords_a:        
            dd, ii = tree_b.query(point, k = 1)
            if dd > max_dist:
                max_dist = dd
    else:
        dd, ii = tree_b.query(stepped_coords_a, k = 1)
        max_dist = max(dd)

    max_dist_a = max_dist
    #print("max dist a: "+str(max_dist))

    #if abs(max_dist_a-max_dist_b)>100:
    #    print("edge: "+ edge_a.ref_start + " " + edge_a.ref_end)
    #    print("max dist a: "+str(max_dist_a))
    #    print("max dist b: "+str(max_dist_b))

    return max(max_dist_a, max_dist_b)

def do_analysis_edges(edges_osm, edges_ext, edges_osm_invalid, edges_ext_invalid, invalid_edges_osm, invalid_edges_ext, progress):

    print("match ext")

    tree_osm_start=create_tree_start_edge(edges_osm)
    tree_osm_end=create_tree_end_edge(edges_osm)

    max_distance = 1000

    k = 10

    for edge_ext in edges_ext:

        x_start = edge_ext.coords_in_m[0][0]
        y_start = edge_ext.coords_in_m[0][1]

        x_end = edge_ext.coords_in_m[-1][0]
        y_end = edge_ext.coords_in_m[-1][1]

        ii_start_start = find_neighbors_in_tree(x_start, y_start, tree_osm_start, k, max_distance)
        ii_end_end = find_neighbors_in_tree(x_end, y_end, tree_osm_end, k, max_distance)

        ii_start_end = find_neighbors_in_tree(x_start, y_start, tree_osm_end, k, max_distance)
        ii_end_start = find_neighbors_in_tree(x_end, y_end, tree_osm_start, k, max_distance)

        match_ind_1 = np.intersect1d(ii_start_start, ii_end_end)
        match_ind_2 = np.intersect1d(ii_start_end, ii_end_start)

        match_ind = np.union1d(match_ind_1, match_ind_2)

        nr_matches_edge = 0
        for ii in match_ind:
             edge_osm = edges_osm[ii]
             if (edge_ext.ref_start == edge_osm.ref_start and edge_ext.ref_end == edge_osm.ref_end) or (edge_ext.ref_start == edge_osm.ref_end and edge_ext.ref_end == edge_osm.ref_start):
                 #print(edge_ext.ref_start)
                 #print(edge_ext.ref_end)
                 dist = calculate_edge_to_edge_distance(edge_ext, edge_osm)
                 if edge_ext.closest_match_dist != None:
                     if dist < edge_ext.closest_match_dist:
                         edge_ext.closest_match_edge = edge_osm
                         edge_ext.closest_match_dist = dist
                         nr_matches_edge = nr_matches_edge + 1
                 else:
                     edge_ext.closest_match_edge = edge_osm
                     edge_ext.closest_match_dist = dist
                     nr_matches_edge = nr_matches_edge + 1
                 
        #print("nr_matches_edge: "+str(nr_matches_edge))
        #if nr_matches_edge > 1:
        #    print("nr_matches_edge: "+str(nr_matches_edge))
        #    print(edge_ext.ref_start)
        #    print(edge_ext.ref_end)

        #if match_ind.size == 1:
        #    #print("alt:")
        #    #print(match_ind)
        #    edge_ext.closest_match_edge = edges_osm[match_ind[0]]

    print("match osm")

    tree_ext_start=create_tree_start_edge(edges_ext)
    tree_ext_end=create_tree_end_edge(edges_ext)

    for edge_osm in edges_osm:

        x_start = edge_osm.coords_in_m[0][0]
        y_start = edge_osm.coords_in_m[0][1]

        x_end = edge_osm.coords_in_m[-1][0]
        y_end = edge_osm.coords_in_m[-1][1]

        ii_start_start = find_neighbors_in_tree(x_start, y_start, tree_ext_start, k, max_distance)
        ii_end_end = find_neighbors_in_tree(x_end, y_end, tree_ext_end, k, max_distance)

        ii_start_end = find_neighbors_in_tree(x_start, y_start, tree_ext_end, k, max_distance)
        ii_end_start = find_neighbors_in_tree(x_end, y_end, tree_ext_start, k, max_distance)

        match_ind_1 = np.intersect1d(ii_start_start, ii_end_end)
        match_ind_2 = np.intersect1d(ii_start_end, ii_end_start)

        match_ind = np.union1d(match_ind_1, match_ind_2)

        nr_matches_edge = 0
        for ii in match_ind:
             edge_ext = edges_ext[ii]
             if (edge_ext.ref_start == edge_osm.ref_start and edge_ext.ref_end == edge_osm.ref_end) or (edge_ext.ref_start == edge_osm.ref_end and edge_ext.ref_end == edge_osm.ref_start):

                 dist = calculate_edge_to_edge_distance(edge_osm, edge_ext)
                 if edge_osm.closest_match_dist != None:
                     if dist < edge_osm.closest_match_dist:
                         edge_osm.closest_match_edge = edge_ext
                         edge_osm.closest_match_dist = dist
                         nr_matches_edge = nr_matches_edge + 1
                 else:
                     edge_osm.closest_match_edge = edge_ext
                     edge_osm.closest_match_dist = dist
                     nr_matches_edge = nr_matches_edge + 1

        #if nr_matches_edge > 1:
        #    print("nr_matches_edge: "+str(nr_matches_edge))

        #if match_ind.size == 1:
        #    #print("alt:")
        #    #print(match_ind)
        #    edge_osm.closest_match_edge = edges_ext[match_ind[0]]
        
    edge_changes_dict = dict()
    for key in ChangeType:
        edge_changes_dict[key] = []

    i = 0;
    for edge_ext in edges_ext:
        closest_match = edge_ext.closest_match_edge
        if (closest_match):
            one_to_one_match = (closest_match.closest_match_edge == edge_ext)
     
            if one_to_one_match:

                dist = edge_ext.closest_match_dist

                if dist > 100:
                    change_type = ChangeType.MOVED_LONG
                else:
                    if dist > 50:
                        change_type = ChangeType.MOVED_MEDIUM
                    else:
                        if dist > 1:
                            change_type = ChangeType.MOVED_SHORT
                        else:
                            change_type = ChangeType.NO
                
                edge_ext.matched_edge = closest_match
                edge_ext.change_type = change_type
                #edge_ext.closest_match_dist = dist
                closest_match.change_type = change_type
                closest_match.matched_edge = edge_ext
                edge_changes_dict[change_type].append(edge_ext)

            else:
                change_type = ChangeType.ADDED_DOUBLE
                #edge_ext.matched_edge = closest_match
                edge_ext.matched_edge = None
                #edge_ext.change_type = change_type
                #closest_match.change_type = change_type
                #closest_match.matched_edge = edge_ext
                edge_changes_dict[change_type].append(edge_ext)

        else:
                change_type = ChangeType.ADDED
                edge_ext.matched_edge = None
                edge_ext.change_type = change_type
                edge_changes_dict[change_type].append(edge_ext)

    for edge in edges_osm:
        if not edge.matched_edge:
            if edge.closest_match_edge:
                if edge.closest_match_dist < 50:
                    edge.change_type = ChangeType.REMOVED_DOUBLE
                    edge_changes_dict[ChangeType.REMOVED_DOUBLE].append(edge)
                else:
                    edge.change_type = ChangeType.REMOVED
                    edge_changes_dict[ChangeType.REMOVED].append(edge)
            else:
                edge.change_type = ChangeType.REMOVED
                edge_changes_dict[ChangeType.REMOVED].append(edge)
                
    print('')
    print('*** Edges ***')
    for key in edge_changes_dict:
        print("{}: {}".format(key, len(edge_changes_dict[key])))

    exported_files = []
    export_file = export_geojson_edges(edges_osm_invalid, "Invalid_osm.geojson")
    exported_files.append(export_file)
    export_file = export_geojson_edges(edges_ext_invalid, "Invalid_ext.geojson")
    exported_files.append(export_file)

    export_file = export_geojson_edges(invalid_edges_osm, "Unmatched_to_nodes_osm.geojson")
    exported_files.append(export_file)
    export_file = export_geojson_edges(invalid_edges_ext, "Unmatched_to_nodes_ext.geojson")
    exported_files.append(export_file)

    for key in ChangeType:
        if key == ChangeType.REMOVED or key == ChangeType.REMOVED_DOUBLE:
            export_file = export_geojson_edges(edge_changes_dict[key], "{}_osm.geojson".format(key))
        else:
            export_file = export_geojson_edges(edge_changes_dict[key], "{}_ext.geojson".format(key))
        exported_files.append(export_file)

    return exported_files       

def add_nodes_to_edges (nodes, edges):
    tree_nodes = create_tree(nodes)
    
    max_distance = 20

    k = 2

    for edge in edges:
        if edge.ref_start == None:
            x_start = edge.coords_in_m[0][0]
            y_start = edge.coords_in_m[0][1]

            ii = find_neighbors_in_tree(x_start, y_start, tree_nodes, k, max_distance)
          
            if (ii.size == 1) or (ii.size > 1 and nodes[ii[0]].rwn_ref == nodes[ii[0]].rwn_ref):                
                node = nodes[ii[0]]
                if node.rwn_ref:
                    edge.ref_start = node.rwn_ref
                if node.rcn_ref:
                    edge.ref_start = node.rcn_ref
            #else:
            #    if ii.size > 1 and nodes[ii[0]].rwn_ref != nodes[ii[0]].rwn_ref:
            #        edge.ref_start="abc"
            #        print("add nodes to edges:")
            #        #   print(edge.coords)
            #        for i in ii:
            #            print("rwn: "+nodes[i].rwn_ref)                  

        if edge.ref_end == None:
            x_end = edge.coords_in_m[-1][0]
            y_end = edge.coords_in_m[-1][1]

            ii = find_neighbors_in_tree(x_end, y_end, tree_nodes, k, max_distance)
          
            if (ii.size == 1) or (ii.size > 1 and nodes[ii[0]].rwn_ref == nodes[ii[0]].rwn_ref):
                node = nodes[ii[0]]
                if node.rwn_ref:
                    edge.ref_end = node.rwn_ref
                if node.rcn_ref:
                    edge.ref_end = node.rcn_ref

    #for edge in edges:
        #if edge.ref_start == None and edge.ref_end != None:
            #print("only ref_end: "+edge.ref_end)
        #if edge.ref_start != None and edge.ref_end == None:
            #print("only ref_start: "+edge.ref_start)

    valid_edges = []
    invalid_edges = []
    for edge in edges:
         if edge.ref_start and edge.ref_end:
             valid_edges.append(edge)
         else:
             invalid_edges.append(edge)

    return valid_edges, invalid_edges

def modify(l):
    output_list = []
    # remove consecutive duplicates
    last = None
    for e in l:
        #print(e)
        #print(last)
        #if np.all(e,last):
        if not np.array_equal(e, last):
            output_list.append(e)

        last = e
    return output_list

def check_single_lines(edges):
    single_lines = True

    for edge in edges:
        c = edge.coords
        c_array_org = np.array(c)
        # remove consecutive duplicates
        #c_array.loc[c_array.shift() != c_array]
        #c_array[np.diff(c_array, prepend=np.nan).astype(bool)]
        #print(c_array_org)
        #print(modify(c_array_org))
        #print(np.array(modify(c_array_org)))
        c_array = np.array(modify(c_array_org))
        # find unique points
        c_unique, indices = np.unique(c_array, axis=0, return_inverse=True)
        if c_unique.shape != c_array.shape:
            single_lines = False
            print('edge contains loop')
            #print(c_array.shape)
            #print(c_unique.shape)
            #print(indices)
            #print(c_array_org)
            #print(modify(c_array_org))
            #print(c_array)
            #print(c_unique)
    #print(single_lines)
    return single_lines

def do_analysis(osmfilename, importfilename_nodes, osmfile_network, importfilename_network, filter_region, filter_province, progress):
    #progress.emit("Importing data")

    nodes_osm = None
    nodes_ext = None

    edges_osm = None
    edges_ext = None

    file_name_osm, file_extension_osm = os.path.splitext(osmfilename)

    #print("file_extension", file_extension_osm);

    if osmfilename:
       if file_extension_osm == '.osm':
           nodes_osm = import_osm(osmfilename)
       else:
           #nodes_osm, nodes_osm_invalid = import_geojson(osmfilename, rwn_name="knooppuntnummer", rcn_name="knooppuntnr", filter_regio=filter_region, filter_province=filter_province)
           nodes_osm, nodes_osm_invalid, edges_osm, edges_osm_invalid = import_geojson_combined(osmfilename, rwn_name="knooppuntnummer", rcn_name="knooppuntnr", filter_regio=filter_region, filter_province=filter_province)           

    if osmfile_network:
        edges_osm, edges_osm_invalid = import_geojson_netwerken(osmfile_network, rwn_name="knooppuntnummer", rcn_name="knooppuntnr", filter_regio=filter_region, filter_province=filter_province)

    print("Import OSM done: nodes "+str(len(nodes_osm))+" edges "+str(len(edges_osm))+ " invalid nodes "+str(len(nodes_osm_invalid))+" invalid edges "+str(len(edges_osm_invalid)))

    nodes_ext, nodes_ext_invalid = import_geojson(importfilename_nodes, rwn_name="knooppuntnummer", rcn_name="knooppuntnr", filter_regio=filter_region, filter_province=filter_province)

    if importfilename_network:
        edges_ext, edges_ext_invalid = import_geojson_netwerken(importfilename_network, rwn_name="knooppuntnummer", rcn_name="knooppuntnr", filter_regio=filter_region, filter_province=filter_province)

    if edges_ext:
        print("Import EXT done: nodes "+str(len(nodes_ext))+" edges "+str(len(edges_ext))+ " invalid nodes "+str(len(nodes_ext_invalid))+         " invalid edges "+str(len(edges_ext_invalid)))
    else:
        print("Import EXT done: nodes "+str(len(nodes_ext))+" edges "+str(0)+ " invalid nodes "+str(len(nodes_ext_invalid)))

    if nodes_osm and nodes_ext:
        exported_files = do_analysis_internal(nodes_osm, nodes_ext, nodes_osm_invalid, nodes_ext_invalid, progress)

    #if edges_osm:
    #    check_single_lines(edges_osm)

    #if edges_ext:
    #    check_single_lines(edges_ext)

    if nodes_osm and edges_osm:
        valid_edges_osm, invalid_edges_osm = add_nodes_to_edges(nodes_osm, edges_osm)
        print("Add OSM nodes to edges: invalid edges "+str(len(invalid_edges_osm )))

    if nodes_ext and edges_ext:
        valid_edges_ext, invalid_edges_ext = add_nodes_to_edges(nodes_ext, edges_ext)
        print("Add EXT nodes to edges: invalid edges "+str(len(invalid_edges_ext )))

    #export_geojson_edges(invalid_edges_ext, "invalid_edges_ext.geojson")

    if edges_osm and edges_ext:
        do_analysis_edges(valid_edges_osm, valid_edges_ext, edges_osm_invalid, edges_ext_invalid, invalid_edges_osm, invalid_edges_ext, progress)

    if nodes_osm:
       print("OSM dataset:", osmfilename, "({} nodes)".format(len(nodes_osm)))

    if (filter_region):
        print("External dataset: {}, filtered by region '{}' ({} nodes)".format(importfilename_nodes, filter_region, len(nodes_ext)))
    else:
        print("External dataset:", importfilename_nodes, "({} nodes)".format(len(nodes_ext)))
    print()

    return exported_files
